"""Independent daily-credit fixtures. All data/clocks are disposable."""

from datetime import UTC, datetime, timedelta
import os
import time
from uuid import uuid4

import pytest

from backend.domain.errors import InvalidInput
from backend.domain.planning import application_today, create_placement
from backend.domain.projects import create_project
from backend.domain.rewards import RewardConfig, ShopService
from backend.domain.streaks import StreakDataError, get_streaks
from backend.domain.tasks import create_task, get_task
from backend.domain.timer import TimerService
from backend.domain.weeks import close_week, preview_close
from backend.storage.db import open_database
from tests.test_forest import all_rows
from tests.test_timer import FakeClock, observed

HOUR = 3_600_000_000
NOW = datetime(2026, 10, 21, 20, tzinfo=UTC)


def iso(value):
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z") if isinstance(value, datetime) else value


def saved_interval(db, start, end, credit, *, outcome="completed", state="finished", task=None, interval=True, closed=True):
    """Build an explicitly historical fixture with no tree/coin enrollment."""
    task = task or create_task(db, "Historical streak work")
    session_id = str(uuid4())
    with db.write() as conn:
        conn.execute(
            "INSERT INTO timer_sessions (id, start_operation_id, task_id, task_title, project_id, project_name, "
            "duration_minutes, state, active_microseconds, started_at, checkpoint_at, finished_at, outcome) "
            "VALUES (?, ?, ?, ?, ?, 'Historical project', 180, ?, ?, ?, ?, ?, ?)",
            (session_id, str(uuid4()), task.id, task.title, task.project_id, state, min(credit, 3 * HOUR), iso(start),
             iso(end), iso(end) if state == "finished" else None, outcome if state == "finished" else None),
        )
        if interval:
            conn.execute(
                "INSERT INTO timer_intervals (id, session_id, started_at, checkpoint_at, ended_at, active_microseconds) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid4()), session_id, iso(start), iso(end), iso(end) if closed else None, credit),
            )
    return session_id


@pytest.fixture(autouse=True)
def utc_calendar(monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "UTC")


def amounts(view):
    return {day.date.isoformat(): day.active_microseconds for day in view.days}


def test_empty_view_has_seven_ascending_zero_days_and_no_writes(db):
    before = all_rows(db)
    view = get_streaks(db, now=NOW)
    assert view.model_dump(mode="json") == {
        "today": "2026-10-21", "timezone": "UTC", "threshold_microseconds": HOUR,
        "current_streak": 0, "streak_through": None,
        "days": [{"date": f"2026-10-{day}", "active_microseconds": 0, "qualified": False} for day in range(15, 22)],
    }
    assert all_rows(db) == before


@pytest.mark.parametrize("credit,qualified", [(0, False), (999_999, False), (HOUR - 1, False), (HOUR, True), (HOUR + 1, True)])
@pytest.mark.parametrize("outcome", ["completed", "finished_early", "interrupted"])
def test_exact_threshold_includes_all_saved_outcomes_and_legacy_intervals(db, credit, qualified, outcome):
    saved_interval(db, NOW - timedelta(hours=2), NOW - timedelta(hours=1), credit, outcome=outcome)
    before = all_rows(db)
    view = get_streaks(db, now=NOW)
    assert view.days[-1].active_microseconds == credit and view.days[-1].qualified is qualified
    assert view.current_streak == int(qualified)
    assert all_rows(db) == before
    assert not before["trees"] and not before["coin_enrollments"] and not before["coin_ledger"]


def test_two_half_hours_from_separate_projects_and_subtask_qualify_once(db):
    project = create_project(db, "Other course")
    parent = create_task(db, "Container", project_id=project.id)
    child = create_task(db, "Leaf", project_id=project.id, parent_id=parent.id)
    saved_interval(db, NOW - timedelta(hours=3), NOW - timedelta(hours=2, minutes=30), HOUR // 2)
    saved_interval(db, NOW - timedelta(hours=1), NOW - timedelta(minutes=30), HOUR // 2, task=child)
    before = all_rows(db)
    view = get_streaks(db, now=NOW)
    assert view.days[-1].active_microseconds == HOUR and view.current_streak == 1
    assert get_task(db, parent.id).completed is False and all_rows(db) == before


@pytest.mark.parametrize("state", ["running", "paused", "needs_review"])
def test_unfinished_sessions_exclude_even_their_closed_confirmed_intervals(db, state):
    saved_interval(db, NOW - timedelta(hours=1), NOW, HOUR, state=state)
    assert get_streaks(db, now=NOW).days[-1].active_microseconds == 0


def test_missing_or_open_intervals_do_not_fall_back_to_session_aggregate(db):
    saved_interval(db, NOW - timedelta(hours=1), NOW, HOUR, interval=False)
    saved_interval(db, NOW - timedelta(hours=1), NOW, HOUR, closed=False)
    assert get_streaks(db, now=NOW).current_streak == 0
    assert get_streaks(db, now=NOW).days[-1].active_microseconds == 0


def test_unresolved_interruptions_exclude_finished_session_without_backfill(db):
    session = saved_interval(db, NOW - timedelta(hours=1), NOW, HOUR)
    with db.write() as conn:
        conn.execute(
            "INSERT INTO timer_interruptions (id, session_id, kind, reason, checkpoint_at, detected_at, confirmed_active_microseconds) "
            "VALUES (?, ?, 'service_restart', 'Unresolved fixture', ?, ?, ?)",
            (str(uuid4()), session, iso(NOW), iso(NOW), HOUR),
        )
    before = all_rows(db)
    assert get_streaks(db, now=NOW).days[-1].active_microseconds == 0 and all_rows(db) == before


def test_current_day_can_remain_incomplete_without_losing_yesterdays_run(db):
    for days_ago in range(1, 10):
        end = NOW - timedelta(days=days_ago)
        saved_interval(db, end - timedelta(hours=1), end, HOUR)
    saved_interval(db, NOW - timedelta(minutes=30), NOW, HOUR // 2)
    view = get_streaks(db, now=NOW)
    assert view.current_streak == 9 and view.streak_through.isoformat() == "2026-10-20"
    assert not view.days[-1].qualified and len(view.days) == 7
    saved_interval(db, NOW - timedelta(minutes=30), NOW, HOUR // 2)
    assert get_streaks(db, now=NOW).current_streak == 10


def test_missing_yesterday_breaks_run_and_future_days_do_not_extend_it(db):
    saved_interval(db, NOW - timedelta(days=2, hours=1), NOW - timedelta(days=2), HOUR)
    saved_interval(db, NOW + timedelta(days=1), NOW + timedelta(days=1, hours=1), HOUR)
    view = get_streaks(db, now=NOW)
    assert view.current_streak == 0 and view.streak_through is None
    saved_interval(db, NOW - timedelta(hours=1), NOW, HOUR)
    assert get_streaks(db, now=NOW).current_streak == 1


@pytest.mark.parametrize("configured", ["America/Los_Angeles", None])
@pytest.mark.parametrize("start,end,day_before,day_after", [
    ("2026-03-08T07:30:00Z", "2026-03-08T10:30:00Z", "2026-03-07", "2026-03-08"),
    ("2026-11-01T06:30:00Z", "2026-11-01T09:30:00Z", "2026-10-31", "2026-11-01"),
])
def test_midnight_and_both_dst_transitions_use_actual_local_rules(db, monkeypatch, configured, start, end, day_before, day_after):
    if configured is None and not hasattr(time, "tzset"):
        pytest.skip("OS local timezone switching requires tzset on this host")
    original_tz = os.environ.get("TZ")
    try:
        if configured is None:
            monkeypatch.delenv("BEARPLANS_TIMEZONE")
            monkeypatch.setenv("TZ", "America/Los_Angeles")
            time.tzset()
        else:
            monkeypatch.setenv("BEARPLANS_TIMEZONE", configured)
        saved_interval(db, start, end, 3 * HOUR)
        now = datetime.fromisoformat(end.replace("Z", "+00:00"))
        view = get_streaks(db, now=now)
        assert amounts(view)[day_before] == 1_800_000_000
        assert amounts(view)[day_after] == 9_000_000_000
        assert sum(amounts(view).values()) == 3 * HOUR
        assert view.today == application_today(now)[0] and view.current_streak == 1
    finally:
        if configured is None:
            if original_tz is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = original_tz
            time.tzset()


@pytest.mark.parametrize("start,end,expected", [
    ("2026-10-20T23:59:59.999997Z", "2026-10-21T00:00:00.000003Z", {"2026-10-20": 2, "2026-10-21": 3}),
    ("2026-10-19T12:00:00Z", "2026-10-21T12:00:00Z", {"2026-10-19": 1, "2026-10-20": 2, "2026-10-21": 2}),
])
def test_cumulative_integer_allocation_conserves_tiny_credit_during_wall_drift(db, start, end, expected):
    saved_interval(db, start, end, 5)
    view = get_streaks(db, now=NOW)
    assert {day: value for day, value in amounts(view).items() if value} == expected
    assert sum(amounts(view).values()) == 5


def test_zero_wall_span_assigns_recorded_positive_credit_to_start_date(db):
    saved_interval(db, NOW, NOW, HOUR)
    assert get_streaks(db, now=NOW).days[-1].active_microseconds == HOUR


@pytest.mark.parametrize("start,end", [
    ("not-an-instant", iso(NOW)), (iso(NOW), "2026-10-21"),
    (iso(NOW), "2026-10-21T19:59:59.999999Z"),
    ("2026-10-21T19:00:00", iso(NOW)),
])
def test_malformed_or_backward_saved_spans_fail_without_changes(db, start, end):
    saved_interval(db, start, end, HOUR)
    before = all_rows(db)
    with pytest.raises(StreakDataError, match="records were kept"):
        get_streaks(db, now=NOW)
    assert all_rows(db) == before


def test_timezone_changes_reattribute_history_without_editing_saved_records(db, monkeypatch):
    start = datetime(2026, 10, 21, 6, 30, tzinfo=UTC)
    saved_interval(db, start, start + timedelta(hours=1), HOUR)
    before = all_rows(db)
    assert get_streaks(db, now=NOW).current_streak == 1
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "America/Los_Angeles")
    changed = get_streaks(db, now=NOW)
    assert amounts(changed)["2026-10-20"] == amounts(changed)["2026-10-21"] == HOUR // 2
    assert changed.current_streak == 0 and all_rows(db) == before


def test_invalid_timezone_is_actionable_and_does_not_change_records(db, monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "not/a-zone")
    before = all_rows(db)
    with pytest.raises(InvalidInput, match="Correct it or unset"):
        get_streaks(db, now=NOW)
    assert all_rows(db) == before


def test_real_application_finalization_pause_recovery_retry_preserves_rewards_and_closed_history(db):
    clock = FakeClock(NOW - timedelta(hours=2))
    config = RewardConfig(birch_price=30)
    timer = TimerService(db, clock, reward_config=config)
    task = create_task(db, "Persist all work", notes="Keep", deadline="2026-10-30")
    create_placement(db, task.id, "2026-10-21")
    preview = preview_close(db, "2026-10-21")
    close_week(db, "2026-10-21", preview.preview_token)
    original_task = get_task(db, task.id)
    first = timer.start(task.id, 30, str(uuid4())).active_session
    assert observed(timer, clock, 1800).last_session.outcome == "completed"
    assert get_streaks(db, now=clock.wall).days[-1].active_microseconds == HOUR // 2
    shop = ShopService(db, config)
    shop.purchase("birch", 30, str(uuid4()))
    second = timer.start(task.id, 60, str(uuid4()), "birch").active_session
    observed(timer, clock, 900)
    paused = timer.control(second.id, "pause", expected_revision=second.revision).active_session
    clock.advance(600)
    assert get_streaks(db, now=clock.wall).days[-1].active_microseconds == HOUR // 2
    timer.control(second.id, "resume", expected_revision=paused.revision)
    observed(timer, clock, 900)
    clock.advance(600)
    review = timer.get().active_session
    assert review.state == "needs_review"
    key = str(uuid4())
    finished = timer.recover(second.id, "finish", expected_revision=review.revision, operation_id=key, discard_uncertain=True)
    assert finished.last_session.outcome == "interrupted" and finished.last_session.active_seconds == 1800
    assert finished.last_session.coin_award == 30 and finished.last_session.tree.species == "birch"
    before = all_rows(db)
    view = get_streaks(db, now=clock.wall)
    assert view.current_streak == 1 and view.days[-1].active_microseconds == HOUR
    timer.recover(second.id, "finish", expected_revision=review.revision, operation_id=key, discard_uncertain=True)
    assert get_streaks(open_database(db.path), now=clock.wall) == view
    assert all_rows(db) == before and get_task(db, task.id) == original_task
    assert len(before["coin_ledger"]) == 3 and len(before["trees"]) == 2
    assert before["trees"][0][1] == first.id


@pytest.mark.parametrize("zone,start,end,expected", [
    ("America/Goose_Bay", "2009-11-01T02:00:00Z", "2009-11-01T05:00:00Z", {"2009-10-31": 7_140_000_000, "2009-11-01": 3_660_000_000}),
    ("America/Sao_Paulo", "2018-11-04T02:30:00Z", "2018-11-04T03:30:00Z", {"2018-11-03": HOUR // 2, "2018-11-04": HOUR // 2}),
    ("Pacific/Apia", "2011-12-30T09:30:00Z", "2011-12-30T10:30:00Z", {"2011-12-29": HOUR // 2, "2011-12-31": HOUR // 2}),
])
def test_historic_midnight_rollback_gap_and_skipped_day_allocate_real_dates(db, monkeypatch, zone, start, end, expected):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", zone)
    credit = sum(expected.values())
    saved_interval(db, start, end, credit)
    view = get_streaks(db, now=datetime.fromisoformat(end.replace("Z", "+00:00")))
    assert {day: value for day, value in amounts(view).items() if value} == expected
    assert sum(amounts(view).values()) == credit


@pytest.mark.parametrize("zone,instant", [("America/Los_Angeles", "0001-01-01T00:00:00Z"), ("Pacific/Kiritimati", "9999-12-31T23:59:59Z")])
def test_saved_instants_outside_local_calendar_range_fail_safely(db, monkeypatch, zone, instant):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", zone)
    saved_interval(db, instant, instant, 1)
    before = all_rows(db)
    with pytest.raises(StreakDataError):
        get_streaks(db, now=NOW)
    assert all_rows(db) == before


def test_schema_seven_legacy_history_qualifies_after_upgrade_without_tree_or_coin_backfill(tmp_path):
    from tests.test_timer_recovery import _schema_seven_with_history

    legacy = _schema_seven_with_history(tmp_path / "streak-upgrade.sqlite3")
    before = all_rows(legacy)
    upgraded = open_database(legacy.path)
    after = all_rows(upgraded)
    for table, rows in before.items():
        assert (after[table][:7] if table == "schema_migrations" else after[table]) == rows
    now = datetime(2026, 10, 18, 21, tzinfo=UTC)
    view = get_streaks(upgraded, now=now)
    assert view.days[-1].active_microseconds == 4_250_000
    assert all_rows(upgraded) == after and not after["trees"] and not after["coin_enrollments"]
    # The old unfinished session contributes only after explicit recovery finalization.
    timer = TimerService(upgraded, FakeClock(now))
    review = timer.get().active_session
    assert review.state == "needs_review" and review.active_seconds == 4.25
    finished = timer.recover(review.id, "finish", expected_revision=review.revision,
                             operation_id=str(uuid4()), discard_uncertain=True).last_session
    assert finished.coin_award is None and finished.tree is None
    final_rows = all_rows(upgraded)
    assert get_streaks(open_database(upgraded.path), now=now).days[-1].active_microseconds == 8_500_000
    assert all_rows(upgraded) == final_rows and not final_rows["coin_ledger"]
