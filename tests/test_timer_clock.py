"""Platform clock selection and conservative fallback without real OS sleep."""

import ctypes
from datetime import UTC, datetime
from uuid import uuid4

from backend.domain.tasks import create_task
from backend.domain.timer import ClockSample, SystemClock, TimerService
from tests.test_timer import FakeClock


def test_linux_clock_uses_sleep_inclusive_boottime(monkeypatch):
    import backend.domain.timer as timer

    calls = []
    monkeypatch.setattr(timer.sys, "platform", "linux")
    monkeypatch.setattr(timer.time, "CLOCK_BOOTTIME", 71, raising=False)
    monkeypatch.setattr(timer.time, "monotonic_ns", lambda: 12_000_000_000)
    monkeypatch.setattr(timer.time, "clock_gettime_ns", lambda clock_id: calls.append(clock_id) or 90_000_000_000)
    sample = SystemClock().sample()
    assert calls == [71]
    assert sample.monotonic_ns == 12_000_000_000 and sample.continuous_ns == 90_000_000_000
    assert sample.sleep_detection and sample.wall.tzinfo is UTC


def test_mac_clock_preserves_measured_monotonic_pair(monkeypatch):
    import backend.domain.timer as timer

    calls = []
    monkeypatch.setattr(timer.sys, "platform", "darwin")
    monkeypatch.setattr(timer.time, "CLOCK_MONOTONIC", 72)
    monkeypatch.setattr(timer.time, "monotonic_ns", lambda: 20_000_000_000)
    monkeypatch.setattr(timer.time, "clock_gettime_ns", lambda clock_id: calls.append(clock_id) or 120_000_000_000)
    sample = SystemClock().sample()
    assert calls == [72]
    assert sample.monotonic_ns == 20_000_000_000 and sample.continuous_ns == 120_000_000_000
    assert sample.sleep_detection


def test_windows_clock_excludes_suspend_from_credit(monkeypatch):
    import backend.domain.timer as timer

    class InterruptClock:
        def __init__(self, ticks):
            self.ticks = ticks

        def __call__(self, pointer):
            ctypes.cast(pointer, ctypes.POINTER(ctypes.c_ulonglong)).contents.value = self.ticks
            return 1

    class Kernel:
        QueryUnbiasedInterruptTime = InterruptClock(123_450_000)
        QueryInterruptTime = InterruptClock(987_650_000)

    monkeypatch.setattr(timer.sys, "platform", "win32")
    monkeypatch.setattr(ctypes, "WinDLL", lambda *args, **kwargs: Kernel(), raising=False)
    sample = SystemClock().sample()
    assert sample.monotonic_ns == 12_345_000_000 and sample.continuous_ns == 98_765_000_000
    assert sample.sleep_detection


def test_unsupported_platform_has_no_measured_sleep_claim(monkeypatch):
    import backend.domain.timer as timer

    monkeypatch.setattr(timer.sys, "platform", "unsupported")
    monkeypatch.setattr(timer.time, "monotonic_ns", lambda: 200)
    sample = SystemClock().sample()
    assert sample.continuous_ns == sample.monotonic_ns == 200
    assert not sample.sleep_detection


def test_unknown_sleep_capability_requires_review_instead_of_claiming_sleep(db):
    class UnknownClock(FakeClock):
        def sample(self):
            return ClockSample(self.wall, self.monotonic_ns, self.continuous_ns, sleep_detection=False)

    clock = UnknownClock(datetime(2026, 10, 18, tzinfo=UTC))
    service = TimerService(db, clock)
    task = create_task(db, "Fallback timing")
    session = service.start(task.id, 1, str(uuid4())).active_session
    clock.advance(1, wall=20, continuous=20)
    review = service.get().active_session
    assert review.id == session.id and review.state == "needs_review"
    assert review.active_seconds == 0
    assert review.recovery.kind == "checkpoint_gap"
    assert review.recovery.measured_sleep_seconds is None
