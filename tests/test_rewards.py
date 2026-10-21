"""Independent coin fixtures: integer minutes, one award and atomic purchases.

All clocks/data are disposable; these simulations do not certify Mac sleep.
"""

from concurrent.futures import ThreadPoolExecutor
import sqlite3
import threading
from uuid import uuid4

import pytest

from backend.domain.errors import InvalidInput
from backend.domain.forest import list_forest
from backend.domain.rewards import RewardConfig, ShopConflict, ShopService, award_session
from backend.domain.tasks import create_task, get_task
from backend.domain.timer import TimerService, TimerConflict, _fingerprint
from backend.storage.db import open_database
from backend.storage.migrations import Migration, MigrationError, current_version, load_migrations, migrate
from tests.test_forest import all_rows
from tests.test_timer import FakeClock, observed
from tests.test_timer_recovery import _schema_seven_with_history


def setup_rewards(db, *, config=None, minutes=3):
    config = config or RewardConfig()
    clock = FakeClock()
    timer = TimerService(db, clock, reward_config=config)
    task = create_task(db, "Coin fixture", notes="Preserve task")
    session = timer.start(task.id, minutes, str(uuid4())).active_session
    return timer, clock, ShopService(db, config), task, session


def earn(db, amount=2, *, config=None):
    timer, clock, shop, task, session = setup_rewards(db, config=config, minutes=max(1, amount))
    saved = observed(timer, clock, amount * 60).last_session
    return timer, clock, shop, task, saved


@pytest.mark.parametrize("seconds,expected", [(0, 0), (0.999999, 0), (59.999999, 0), (60, 1), (119.999999, 1), (120, 2), (180, 3)])
def test_whole_confirmed_minutes_award_only_once_at_finalization(db, seconds, expected):
    timer, clock, shop, task, session = setup_rewards(db)
    current = observed(timer, clock, seconds)
    if current.active_session is not None:
        assert current.active_session.coin_award is None and shop.get().balance == 0
        saved = timer.control(session.id, "finish", operation_id=str(uuid4())).last_session
    else:
        saved = current.last_session
    assert saved.active_seconds == seconds and saved.coin_award == expected
    view = shop.get()
    assert view.balance == expected and len(view.recent_entries) == 1
    assert view.recent_entries[0].amount == expected and view.recent_entries[0].session_id == session.id
    before = all_rows(db)
    timer.control(session.id, "finish")
    with db.write() as conn:
        award_session(conn, session.id)
    assert all_rows(db) == before and get_task(db, task.id) == task


def test_fractional_minutes_do_not_accumulate_between_sessions(db):
    timer, clock, shop, task, session = setup_rewards(db)
    observed(timer, clock, 59)
    timer.control(session.id, "finish")
    other = timer.start(task.id, 3, str(uuid4())).active_session
    observed(timer, clock, 59)
    timer.control(other.id, "finish")
    assert shop.get().balance == 0 and [e.amount for e in shop.get().recent_entries] == [0, 0]


@pytest.mark.parametrize("interruption", ["pause", "sleep", "gap", "restart", "clock"])
def test_paused_uncertain_and_sleep_time_never_award_coins(db, interruption):
    timer, clock, shop, _, session = setup_rewards(db)
    observed(timer, clock, 65)
    if interruption == "pause":
        timer.control(session.id, "pause", expected_revision=session.revision)
        clock.advance(1000)
    elif interruption == "sleep":
        clock.advance(1, wall=1001, continuous=1001)
    elif interruption == "gap":
        clock.advance(1000)
    elif interruption == "clock":
        clock.advance(1, wall=-200)
    else:
        clock.advance(1000)
        timer = TimerService(open_database(db.path), clock)
    current = timer.get().active_session
    assert current.active_seconds == 65 and current.coin_award is None
    assert shop.get().balance == 0 and not shop.get().recent_entries
    if current.state == "needs_review":
        saved = timer.recover(current.id, "finish", expected_revision=current.revision,
                              operation_id=str(uuid4()), discard_uncertain=True).last_session
    else:
        saved = timer.control(current.id, "finish", expected_revision=current.revision).last_session
    assert saved.active_seconds == 65 and saved.coin_award == shop.get().balance == 1


def test_rate_is_captured_at_start_across_restart_and_different_configuration(db):
    timer, clock, shop, task, session = setup_rewards(db, config=RewardConfig(coins_per_minute=3))
    observed(timer, clock, 61)
    paused = timer.control(session.id, "pause", expected_revision=session.revision).active_session
    reopened = TimerService(open_database(db.path), clock, reward_config=RewardConfig(coins_per_minute=7))
    assert reopened.get().active_session.state == "paused"
    saved = reopened.control(paused.id, "finish").last_session
    assert saved.coin_award == 3 and shop.get().balance == 3
    other = reopened.start(task.id, 1, str(uuid4())).active_session
    assert observed(reopened, clock, 60).last_session.coin_award == 7
    assert shop.get().balance == 10 and other.id != saved.id


def test_recovery_resume_retains_enrollment_and_awards_combined_confirmed_intervals(db):
    timer, clock, shop, _, session = setup_rewards(db, minutes=2)
    observed(timer, clock, 59)
    clock.advance(500)
    review = timer.get().active_session
    timer.recover(session.id, "resume", expected_revision=review.revision, operation_id=str(uuid4()), discard_uncertain=True)
    saved = observed(timer, clock, 61).last_session
    assert saved.active_seconds == 120 and saved.coin_award == shop.get().balance == 2
    assert saved.tree.id == session.tree.id and saved.tree.outcome == "mature"


def test_concurrent_finish_requests_share_one_award_and_outcome(db):
    timer, clock, shop, _, session = setup_rewards(db)
    observed(timer, clock, 121)
    barrier = threading.Barrier(6)

    def finish(_):
        barrier.wait()
        return timer.control(session.id, "finish", operation_id=str(uuid4())).last_session

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(finish, range(6)))
    assert all(result.coin_award == 2 for result in results)
    assert shop.get().balance == 2 and len(shop.get().recent_entries) == len(list_forest(db)) == 1


@pytest.mark.parametrize("mode", ["early", "expiry", "recovery"])
def test_award_failure_rolls_back_session_tree_receipt_and_recovery_then_retries(db, mode):
    timer, clock, shop, _, session = setup_rewards(db, minutes=2)
    current = observed(timer, clock, 119).active_session
    if mode == "recovery":
        clock.advance(500)
        current = timer.get().active_session
    with db.write() as conn:
        conn.execute("CREATE TRIGGER fail_award BEFORE INSERT ON coin_ledger BEGIN SELECT RAISE(ABORT, 'injected award failure'); END")
    before = all_rows(db)
    key = str(uuid4())

    def finish():
        if mode == "expiry":
            return timer.get()
        if mode == "recovery":
            return timer.recover(session.id, "finish", expected_revision=current.revision,
                                 operation_id=key, discard_uncertain=True)
        return timer.control(session.id, "finish", expected_revision=current.revision, operation_id=key)

    if mode == "expiry":
        clock.advance(1)
    with pytest.raises(sqlite3.Error, match="injected award failure"):
        finish()
    assert all_rows(db) == before and shop.get().balance == 0 and list_forest(db) == []
    with db.write() as conn:
        conn.execute("DROP TRIGGER fail_award")
    saved = finish().last_session
    assert saved.coin_award == (2 if mode == "expiry" else 1)
    assert saved.tree.outcome == ("mature" if mode == "expiry" else "unfinished")
    after = all_rows(db)
    finish()
    assert all_rows(db) == after


def test_coin_enrollment_failure_rolls_back_start_and_same_request_retries(db):
    clock = FakeClock()
    timer = TimerService(db, clock)
    task = create_task(db, "Enrollment")
    key = str(uuid4())
    with db.write() as conn:
        conn.execute("CREATE TRIGGER fail_coins BEFORE INSERT ON coin_enrollments BEGIN SELECT RAISE(ABORT, 'enrollment failure'); END")
    before = all_rows(db)
    with pytest.raises(sqlite3.Error, match="enrollment failure"):
        timer.start(task.id, 1, key)
    assert all_rows(db) == before
    with db.write() as conn:
        conn.execute("DROP TRIGGER fail_coins")
    session = timer.start(task.id, 1, key).active_session
    assert observed(timer, clock, 60).last_session.coin_award == 1
    assert session.tree is not None


def test_purchase_is_atomic_replay_safe_and_species_is_locked_at_start(db):
    config = RewardConfig(birch_price=2, oak_price=0)
    timer, clock, shop, task, _ = earn(db, 2, config=config)
    key = str(uuid4())
    purchase = shop.purchase(" Birch ", 2, key.upper())
    assert purchase.balance == 0 and purchase.species == "birch"
    session = timer.start(task.id, 1, str(uuid4()), "birch").active_session
    assert session.tree.species == "birch"
    shop.purchase("oak", 0, str(uuid4()))
    before = all_rows(db)
    assert shop.purchase("birch", 2, key) == purchase
    assert all_rows(db) == before
    with pytest.raises(ShopConflict, match="already used"):
        shop.purchase("oak", 0, key)
    with pytest.raises(ShopConflict, match="already own"):
        shop.purchase("birch", 2, str(uuid4()))
    reopened = TimerService(open_database(db.path), clock, reward_config=config)
    review = reopened.get().active_session
    saved = reopened.recover(session.id, "finish", expected_revision=review.revision,
                             operation_id=str(uuid4()), discard_uncertain=True).last_session
    assert saved.tree.species == "birch" and list_forest(db)[0].species == "birch"
    reloaded = ShopService(open_database(db.path), config).get()
    assert [s.id for s in reloaded.species if s.owned] == ["pine", "birch", "oak"]
    assert get_task(db, task.id) == task
    # The replay is the original persisted result, even after future earnings.
    next_session = reopened.start(task.id, 1, str(uuid4())).active_session
    observed(reopened, clock, 60)
    assert shop.get().balance == 1 and shop.purchase("birch", 2, key).balance == 0
    assert next_session.tree.species == "pine"


def test_unowned_unknown_species_and_changed_start_replay_reject_without_partial_writes(db):
    timer, clock, shop, task, session = setup_rewards(db)
    timer.control(session.id, "finish")
    before = all_rows(db)
    for species in ("birch", "unknown", None):
        with pytest.raises(InvalidInput):
            timer.start(task.id, 1, str(uuid4()), species)
    assert all_rows(db) == before
    key = str(uuid4())
    pine = timer.start(task.id, 1, key, " Pine ").active_session
    assert timer.start(task.id, 1, key).active_session == pine
    with pytest.raises(TimerConflict):
        timer.start(task.id, 1, key, "birch")


@pytest.mark.parametrize("failure_table", ["owned_species", "coin_ledger", "shop_operations"])
def test_failed_purchase_rolls_back_debit_ownership_receipt_then_retries(db, failure_table):
    _, _, shop, _, _ = earn(db, 2, config=RewardConfig(birch_price=2))
    with db.write() as conn:
        conn.execute(f"CREATE TRIGGER fail_purchase BEFORE INSERT ON {failure_table} BEGIN SELECT RAISE(ABORT, 'injected purchase failure'); END")
    before = all_rows(db)
    key = str(uuid4())
    with pytest.raises(sqlite3.Error, match="injected purchase failure"):
        shop.purchase("birch", 2, key)
    assert all_rows(db) == before
    with db.write() as conn:
        conn.execute("DROP TRIGGER fail_purchase")
    assert shop.purchase("birch", 2, key).balance == 0
    assert shop.purchase("birch", 2, key).balance == 0
    assert len(shop.get().recent_entries) == 2


def test_insufficient_stale_price_and_negative_balance_reject_spending(db):
    _, _, shop, _, _ = earn(db, 1, config=RewardConfig(birch_price=2, oak_price=0))
    before = all_rows(db)
    with pytest.raises(ShopConflict, match="not enough"):
        shop.purchase("birch", 2, str(uuid4()))
    with pytest.raises(ShopConflict, match="price changed"):
        shop.purchase("birch", 1, str(uuid4()))
    assert all_rows(db) == before
    # A future adjustment may create a negative balance; model it through an
    # explicit disposable debit fixture without adding session correction UI.
    with db.write() as conn:
        conn.execute("INSERT INTO coin_ledger (id, kind, amount, species, created_at) VALUES (?, 'purchase', -2, 'cherry', '2026-10-20T00:00:00.000000Z')", (str(uuid4()),))
    negative = all_rows(db)
    with pytest.raises(ShopConflict, match="not enough"):
        shop.purchase("oak", 0, str(uuid4()))
    assert all_rows(db) == negative and shop.get().balance == -1


@pytest.mark.parametrize("same_species", [False, True])
def test_concurrent_purchases_never_overspend_across_distinct_database_instances(db, same_species):
    _, _, shop, _, _ = earn(db, 2, config=RewardConfig(birch_price=2, oak_price=2))
    other = ShopService(open_database(db.path), shop.config)
    barrier = threading.Barrier(2)

    def purchase(item):
        service, species = item
        barrier.wait()
        try:
            return service.purchase(species, 2, str(uuid4()))
        except ShopConflict as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(purchase, [(shop, "birch"), (other, "birch" if same_species else "oak")]))
    assert sum(not isinstance(result, ShopConflict) for result in results) == 1
    assert shop.get().balance == 0 and len(shop.get().recent_entries) == 2
    assert len([s for s in shop.get().species if s.owned and s.id != "pine"]) == 1


def test_concurrent_same_purchase_key_replays_original_result(db):
    _, _, shop, _, _ = earn(db, 2, config=RewardConfig(birch_price=2))
    other = ShopService(open_database(db.path), shop.config)
    key = str(uuid4())
    barrier = threading.Barrier(2)

    def purchase(service):
        barrier.wait()
        return service.purchase("birch", 2, key)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(purchase, [shop, other]))
    assert results[0] == results[1] and shop.get().balance == 0
    with db.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM shop_operations").fetchone()[0] == 1


@pytest.mark.parametrize("environment", [
    {"BEARPLANS_COINS_PER_MINUTE": "-1"}, {"BEARPLANS_COINS_PER_MINUTE": "1.2"},
    {"BEARPLANS_COINS_PER_MINUTE": "1000001"}, {"BEARPLANS_BIRCH_PRICE": "no"},
    {"BEARPLANS_CHERRY_PRICE": "1000000001"}, {"BEARPLANS_OAK_PRICE": "١"},
])
def test_invalid_config_fails_clearly(environment):
    with pytest.raises(ValueError, match="BEARPLANS_"):
        RewardConfig.from_environment(environment)


def test_config_defaults_zero_rate_and_environment_changes_do_not_change_service(db, monkeypatch):
    assert RewardConfig.from_environment({}) == RewardConfig(1, 30, 60, 120)
    monkeypatch.setenv("BEARPLANS_COINS_PER_MINUTE", "0")
    monkeypatch.setenv("BEARPLANS_BIRCH_PRICE", "7")
    clock = FakeClock()
    timer = TimerService(db, clock)
    shop = ShopService(db)
    monkeypatch.setenv("BEARPLANS_COINS_PER_MINUTE", "8")
    monkeypatch.setenv("BEARPLANS_BIRCH_PRICE", "9")
    task = create_task(db, "Zero award")
    timer.start(task.id, 1, str(uuid4()))
    assert observed(timer, clock, 60).last_session.coin_award == 0
    assert shop.get().coins_per_minute == 0 and shop.get().species[1].price == 7


def test_schema_nine_upgrade_preserves_all_history_and_tree_fields_without_coin_backfill(tmp_path):
    db = _schema_seven_with_history(tmp_path / "schema-nine.sqlite3")
    migrations = load_migrations()
    migrate(db, migrations[:9])
    with db.write() as conn:
        sessions = conn.execute("SELECT * FROM timer_sessions ORDER BY rowid").fetchall()
        for index, session in enumerate(sessions):
            conn.execute(
                "INSERT INTO trees (rowid, id, session_id, species, created_at, outcome, finalized_at) VALUES (?, ?, ?, 'pine', ?, ?, ?)",
                (index * 7 + 3, str(uuid4()), session["id"], session["started_at"],
                 "unfinished" if session["state"] == "finished" else None, session["finished_at"]),
            )
        rowids = [tuple(row) for row in conn.execute("SELECT rowid,* FROM trees ORDER BY rowid")]
        running = conn.execute("SELECT * FROM timer_sessions WHERE state = 'running'").fetchone()
        conn.execute("UPDATE timer_operations SET fingerprint = ? WHERE operation_id = ?", (
            _fingerprint("start", task_id=running["task_id"], duration_minutes=running["duration_minutes"]),
            running["start_operation_id"],
        ))
    before = all_rows(db)
    addition = migrations[9]
    broken = Migration(addition.version, addition.name, addition.sql + "\nINSERT INTO missing_coin_table VALUES (1);")
    with pytest.raises(MigrationError, match="rolled back"):
        migrate(db, [*migrations[:9], broken])
    assert current_version(db) == 9 and all_rows(db) == before
    with db.read() as conn:
        assert [tuple(row) for row in conn.execute("SELECT rowid,* FROM trees ORDER BY rowid")] == rowids
    migrate(db)
    after = all_rows(db)
    for name, rows in before.items():
        assert (after[name][:9] if name == "schema_migrations" else after[name]) == rows
    for name in ("coin_enrollments", "coin_ledger", "owned_species", "shop_operations"):
        assert after[name] == []
    reopened = open_database(db.path)
    assert all_rows(reopened) == after
    with db.read() as conn:
        assert [tuple(row) for row in conn.execute("SELECT rowid,* FROM trees ORDER BY rowid")] == rowids
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    timer = TimerService(reopened, FakeClock())
    review = timer.get().active_session
    assert review.tree is not None and review.coin_award is None
    assert timer.start(running["task_id"], running["duration_minutes"], running["start_operation_id"]).active_session == review
    saved = timer.recover(review.id, "finish", expected_revision=review.revision,
                           operation_id=str(uuid4()), discard_uncertain=True).last_session
    assert saved.tree is not None and saved.coin_award is None
    assert ShopService(db).get().recent_entries == []
    timer.control(saved.id, "finish")
    assert ShopService(db).get().balance == 0
    fresh = timer.start(saved.task_id, 1, str(uuid4())).active_session
    assert fresh.tree is not None
    with db.read() as conn:
        assert conn.execute("SELECT session_id FROM coin_enrollments").fetchone()[0] == fresh.id
