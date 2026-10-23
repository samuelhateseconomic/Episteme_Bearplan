"""Exact correction/reversal, cutover, audit, stale/replay and failure fixtures."""
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
import json
import sqlite3
from uuid import uuid4

import pytest

from backend.domain.corrections import CorrectionConflict, CorrectionDraft, apply_correction, list_saved_sessions, preview_correction
from backend.domain.errors import InvalidInput
from backend.domain.forest import enroll_tree, finalize_tree, list_forest
from backend.domain.planning import create_placement
from backend.domain.weeks import close_week, preview_close
from backend.domain.rewards import RewardConfig, ShopConflict, ShopService, award_session, enroll_coins
from backend.domain.statistics import get_statistics
from backend.domain.streaks import get_streaks
from backend.domain.tasks import create_task
from backend.domain.timer import TimerService
from backend.storage.db import Database, open_database
from backend.storage.migrations import Migration, MigrationError, current_version, load_migrations, migrate
from tests.test_forest import all_rows
from tests.test_streaks import HOUR, saved_interval
from tests.test_timer import FakeClock

NOW = datetime(2026, 10, 23, 20, tzinfo=UTC)
MINUTE = 60_000_000


@pytest.fixture(autouse=True)
def utc(monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "UTC")


def seeded(db, credit=HOUR, *, rate=1, tree=True, start=None, end=None, outcome="completed"):
    task = create_task(db, "Synthetic saved work", estimate_minutes=60)
    session = saved_interval(db, start or NOW - timedelta(hours=1), end or NOW, credit, task=task, outcome=outcome)
    with db.write() as conn:
        conn.execute("UPDATE timer_sessions SET duration_minutes = ? WHERE id = ?", (max(1, (credit + MINUTE - 1) // MINUTE), session))
        if tree:
            enroll_tree(conn, session, NOW.isoformat())
            finalize_tree(conn, session)
        if rate is not None:
            enroll_coins(conn, session, RewardConfig(coins_per_minute=rate))
            award_session(conn, session)
    return session, task


def draft_for(db, session, values, reason="Correct a recorded interruption"):
    view = next(row for row in list_saved_sessions(db) if row["id"] == session)
    return CorrectionDraft(expected_revision=view["revision"], reason=reason,
                           intervals=[{"id": row["id"], "active_microseconds": value} for row, value in zip(view["intervals"], values, strict=True)])


def correct(db, session, values, *, reason="Correct a recorded interruption", key=None):
    draft = draft_for(db, session, values, reason)
    preview = preview_correction(db, session, draft)
    result = apply_correction(db, session, draft, preview["preview_token"], key or str(uuid4()))
    return draft, preview, result


def test_correct_after_spending_reverses_through_adjustments_preserves_purchases_and_initial_award(db):
    session, task = seeded(db)
    create_placement(db, task.id, "2026-10-23")
    close_week(db, "2026-10-19", preview_close(db, "2026-10-19").preview_token)
    shop = ShopService(db, RewardConfig(birch_price=60, oak_price=0))
    shop.purchase("birch", 60, str(uuid4()))
    before = all_rows(db)
    draft, preview, result = correct(db, session, [HOUR // 2])
    assert preview["coin_delta"] == -30 and preview["balance_after"] == -30
    assert preview["days"][0]["qualified_before"] and not preview["days"][0]["qualified_after"]
    assert result["tree_outcome"] == "unfinished"
    assert shop.get().balance == -30 and shop.get().species[1].owned
    with pytest.raises(ShopConflict, match="not enough"):
        shop.purchase("oak", 0, str(uuid4()))
    assert get_statistics(db, now=NOW).active_microseconds == HOUR // 2
    assert get_streaks(db, now=NOW).current_streak == 0
    after = all_rows(db)
    changed = {"timer_sessions", "timer_intervals", "trees", "coin_adjustments", "session_correction_baselines", "session_corrections"}
    for name in before.keys() - changed:
        assert after[name] == before[name]
    assert len(after["coin_adjustments"]) == len(after["session_corrections"]) == 1
    assert len(after["trees"]) == 1 and list_forest(db)[0].id == list_forest(open_database(db.path))[0].id
    assert TimerService(db, FakeClock(NOW)).get().last_session.coin_award == 30
    # Reversal is a new reviewed edit restoring the immutable before-values.
    history = list_saved_sessions(db)[0]["history"][0]
    assert history["before"][0]["active_microseconds"] == HOUR
    correct(db, session, [history["before"][0]["active_microseconds"]], reason="Reverse mistaken correction")
    assert shop.get().balance == 0 and shop.get().species[1].owned
    assert list_forest(db)[0].outcome == "mature" and get_streaks(db, now=NOW).current_streak == 1
    final = all_rows(db)
    assert final["coin_ledger"] == before["coin_ledger"] and len(final["session_corrections"]) == 2
    assert final["tasks"] == before["tasks"] and len(final["session_correction_baselines"]) == 1


def test_preview_is_read_only_and_retries_replay_original_result_even_after_later_work(db):
    session, _ = seeded(db)
    draft = draft_for(db, session, [HOUR // 2], "  Correct a break  ")
    before = all_rows(db)
    preview = preview_correction(db, session, draft)
    assert all_rows(db) == before
    key = str(uuid4())
    result = apply_correction(db, session, draft, preview["preview_token"], key)
    correct(db, session, [HOUR])
    after = all_rows(db)
    # Normalized whitespace is the same operation. Stale revision is valid only for replay.
    normalized = draft.model_copy(update={"reason": "Correct a break"})
    assert apply_correction(open_database(db.path), session, normalized, preview["preview_token"], key.upper()) == result
    assert all_rows(db) == after
    with pytest.raises(CorrectionConflict, match="different work"):
        apply_correction(db, session, normalized.model_copy(update={"reason": "Another reason"}), preview["preview_token"], key)
    assert all_rows(db) == after


@pytest.mark.parametrize("credit,rate,target,delta", [(60_000_000, 3, 59_999_999, -3), (59_999_999, 2, 1, 0), (60_000_001, 0, 0, 0)])
def test_captured_rate_whole_session_floor_and_zero_adjustments(db, credit, rate, target, delta):
    session, _ = seeded(db, credit, rate=rate)
    _, preview, _ = correct(db, session, [target])
    assert preview["coin_delta"] == delta
    assert len(all_rows(db)["coin_adjustments"]) == 1
    assert ShopService(db, RewardConfig(coins_per_minute=999)).get().balance == target // MINUTE * rate


@pytest.mark.parametrize("tree", [False, True])
def test_legacy_cutovers_do_not_create_tree_enrollment_or_award(db, tree):
    session, _ = seeded(db, rate=None, tree=tree)
    before = all_rows(db)
    _, preview, _ = correct(db, session, [HOUR // 2])
    assert preview["coin_contribution_after"] is None and preview["coin_delta"] == 0
    assert len(all_rows(db)["trees"]) == int(tree)
    for name in ("coin_enrollments", "coin_ledger", "coin_adjustments", "owned_species"):
        assert all_rows(db)[name] == before[name]


@pytest.mark.parametrize("target", [-1, HOUR + 1])
def test_corrections_cannot_add_unconfirmed_time_or_go_negative(db, target):
    session, _ = seeded(db)
    before = all_rows(db)
    with pytest.raises(InvalidInput, match="original confirmed maximum"):
        preview_correction(db, session, draft_for(db, session, [target]))
    assert all_rows(db) == before
    correct(db, session, [0])
    with pytest.raises(InvalidInput, match="original confirmed maximum"):
        preview_correction(db, session, draft_for(db, session, [HOUR + 1]))
    correct(db, session, [HOUR])


def test_unknown_duplicate_missing_and_no_change_intervals_and_blank_reason_fail_without_writes(db):
    session, _ = seeded(db)
    base = draft_for(db, session, [HOUR // 2])
    before = all_rows(db)
    for updates in ({"intervals": []}, {"intervals": base.intervals * 2},
                    {"intervals": [{"id": str(uuid4()), "active_microseconds": 1}]},
                    {"reason": "\u200b  "}, {"reason": "x" * 501}, {"expected_revision": 0}):
        draft = CorrectionDraft(**{**base.model_dump(), **updates})
        with pytest.raises(InvalidInput):
            preview_correction(db, session, draft)
    with pytest.raises(InvalidInput, match="at least one"):
        preview_correction(db, session, draft_for(db, session, [HOUR]))
    assert all_rows(db) == before


@pytest.mark.parametrize("change", ["session", "wallet", "timezone", "day_total"])
def test_stale_preview_cannot_apply_any_partial_changes(db, monkeypatch, change):
    session, _ = seeded(db)
    draft = draft_for(db, session, [HOUR // 2])
    preview = preview_correction(db, session, draft)
    if change == "session":
        correct(db, session, [HOUR // 4])
    elif change == "wallet":
        ShopService(db, RewardConfig(birch_price=1)).purchase("birch", 1, str(uuid4()))
    elif change == "day_total":
        seeded(db, credit=MINUTE, rate=None)
    else:
        monkeypatch.setenv("BEARPLANS_TIMEZONE", "America/Los_Angeles")
    before = all_rows(db)
    with pytest.raises(CorrectionConflict, match="changed"):
        apply_correction(db, session, draft, preview["preview_token"], str(uuid4()))
    assert all_rows(db) == before


def test_failed_adjustment_rolls_back_session_tree_baseline_audit_and_retry_then_succeeds(db):
    session, _ = seeded(db)
    draft = draft_for(db, session, [HOUR // 2])
    preview = preview_correction(db, session, draft)
    key = str(uuid4())
    with db.write() as conn:
        conn.execute("CREATE TRIGGER injected_failure BEFORE INSERT ON coin_adjustments BEGIN SELECT RAISE(ABORT, 'Injected failure'); END")
    before = all_rows(db)
    with pytest.raises(sqlite3.IntegrityError, match="Injected"):
        apply_correction(db, session, draft, preview["preview_token"], key)
    assert all_rows(db) == before
    with db.write() as conn:
        conn.execute("DROP TRIGGER injected_failure")
    assert apply_correction(db, session, draft, preview["preview_token"], key)["coin_delta"] == -30


@pytest.mark.parametrize("table", ["session_corrections", "session_correction_baselines", "coin_adjustments"])
def test_audit_baseline_and_adjustments_are_immutable(db, table):
    session, _ = seeded(db)
    correct(db, session, [HOUR // 2])
    before = all_rows(db)
    for sql in (f"DELETE FROM {table}", f"UPDATE {table} SET session_id = session_id"):
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            with db.write() as conn:
                conn.execute(sql)
    assert all_rows(db) == before


def test_concurrent_same_operation_saves_once_and_competing_operation_conflicts(db):
    session, _ = seeded(db)
    draft = draft_for(db, session, [HOUR // 2])
    preview = preview_correction(db, session, draft)
    key = str(uuid4())
    def apply(_):
        return apply_correction(Database(db.path), session, draft, preview["preview_token"], key)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(apply, range(2)))
    assert results[0] == results[1] and len(all_rows(db)["session_corrections"]) == 1
    with pytest.raises(CorrectionConflict):
        apply_correction(db, session, draft, preview["preview_token"], str(uuid4()))


@pytest.mark.parametrize("zone,start,end,expected", [
    ("UTC", "2026-10-22T23:59:59.999997Z", "2026-10-23T00:00:00.000003Z", {"2026-10-22": 1, "2026-10-23": 2}),
    ("America/Los_Angeles", "2026-11-01T08:30:00Z", "2026-11-01T10:30:00Z", {"2026-11-01": 3}),
])
def test_corrected_microseconds_dates_and_streaks_share_exact_allocation(db, monkeypatch, zone, start, end, expected):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", zone)
    session, _ = seeded(db, credit=5, rate=None, start=start, end=end)
    _, preview, _ = correct(db, session, [3])
    now = datetime.fromisoformat(end.replace("Z", "+00:00"))
    assert {day["date"]: day["after_microseconds"] for day in preview["days"]} == expected
    assert {str(day.date): day.active_microseconds for day in get_statistics(db, now=now).days} == expected
    assert {str(day.date): day.active_microseconds for day in get_streaks(db, now=now).days if day.active_microseconds} == expected


@pytest.mark.parametrize("damage", ["open", "missing", "invalid_date", "total_mismatch", "unresolved", "unfinished", "missing_award"])
def test_ineligible_or_inconsistent_sessions_explain_block_and_preserve_records(db, damage):
    session, _ = seeded(db)
    with db.write() as conn:
        if damage == "open": conn.execute("UPDATE timer_intervals SET ended_at = NULL")
        elif damage == "missing": conn.execute("DELETE FROM timer_intervals")
        elif damage == "invalid_date": conn.execute("UPDATE timer_intervals SET started_at = 'invalid'")
        elif damage == "total_mismatch": conn.execute("UPDATE timer_sessions SET active_microseconds = 1")
        elif damage == "unfinished": conn.execute("UPDATE timer_sessions SET state = 'paused', finished_at = NULL, outcome = NULL")
        elif damage == "missing_award": conn.execute("DELETE FROM coin_ledger")
        else:
            conn.execute("INSERT INTO timer_interruptions (id,session_id,kind,reason,checkpoint_at,detected_at,confirmed_active_microseconds) "
                         "VALUES (?,?,'service_restart','Fixture',?,?,?)", (str(uuid4()), session, NOW.isoformat(), NOW.isoformat(), HOUR))
    with db.read() as conn:
        revision = conn.execute("SELECT revision FROM timer_sessions WHERE id = ?", (session,)).fetchone()[0]
        intervals = [{"id": row[0], "active_microseconds": 0} for row in conn.execute("SELECT id FROM timer_intervals")]
    before = all_rows(db)
    draft = CorrectionDraft(expected_revision=revision, reason="Reject unsafe correction", intervals=intervals)
    with pytest.raises(CorrectionConflict):
        preview_correction(db, session, draft)
    assert all_rows(db) == before


def test_upgrade_from_12_preserves_every_existing_row_and_failure_retries_atomically(tmp_path):
    db = Database(tmp_path / "old.sqlite3")
    migrations = load_migrations()
    migrate(db, migrations[:12])
    saved_interval(db, NOW - timedelta(hours=1), NOW, HOUR)
    before = all_rows(db)
    addition = migrations[12]
    with pytest.raises(MigrationError, match="rolled back"):
        migrate(db, [*migrations[:12], Migration(addition.version, addition.name, addition.sql + "\nINSERT INTO missing VALUES (1);")])
    assert current_version(db) == 12 and all_rows(db) == before
    migrate(db)
    after = all_rows(db)
    for name, rows in before.items():
        assert (after[name][:len(rows)] if name in ("schema_migrations", "migration_fingerprints") else after[name]) == rows
    assert current_version(db) == 13
    assert all_rows(open_database(db.path)) == after


def test_multiple_intervals_keep_pause_gaps_and_captured_whole_session_rounding(db):
    session, _ = seeded(db, credit=MINUTE, rate=3)
    with db.write() as conn:
        first = conn.execute("SELECT * FROM timer_intervals WHERE session_id = ?", (session,)).fetchone()
        conn.execute("UPDATE timer_intervals SET active_microseconds = ? WHERE id = ?", (30_000_000, first["id"]))
        conn.execute("INSERT INTO timer_intervals (id,session_id,started_at,checkpoint_at,ended_at,active_microseconds) VALUES (?,?,?,?,?,?)",
                     (str(uuid4()), session, "2026-10-23T21:00:00Z", "2026-10-23T21:00:30Z", "2026-10-23T21:00:30Z", 30_000_000))
    before = all_rows(db)
    _, preview, _ = correct(db, session, [29_999_999, 30_000_000])
    assert preview["coin_delta"] == -3 and preview["after_microseconds"] == 59_999_999
    with db.read() as conn:
        rows = [tuple(row) for row in conn.execute("SELECT started_at,checkpoint_at,ended_at FROM timer_intervals ORDER BY rowid")]
    assert rows == [(row[2], row[3], row[4]) for row in before["timer_intervals"]]
    assert len(all_rows(db)["timer_intervals"]) == 2


def test_correcting_history_leaves_another_paused_timer_and_finish_replay_unchanged(db):
    historical, _ = seeded(db)
    timer = TimerService(db, FakeClock(NOW))
    task = create_task(db, "Current unfinished work")
    current = timer.start(task.id, 1, str(uuid4())).active_session
    paused = timer.control(current.id, "pause", expected_revision=current.revision).active_session
    before = timer.get().active_session
    correct(db, historical, [0])
    assert timer.get().active_session == before == paused
    # A later finish retry of corrected history cannot award again or undo edits.
    timer.control(historical, "finish", operation_id=str(uuid4()))
    assert ShopService(db).get().balance == 0 and len(all_rows(db)["coin_adjustments"]) == 1
