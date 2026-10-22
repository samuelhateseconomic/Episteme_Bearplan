"""Read-only daily streaks from the exact confirmed credit in saved intervals.

All finalized outcomes and legacy closed intervals qualify. Running, paused,
review and unresolved interruption records cannot contribute. Wall timestamps
allocate saved integer credit to calendar dates; they never create earned time.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from pydantic import BaseModel, ConfigDict

from backend.domain.calendar import ApplicationCalendar
from backend.storage.db import Database, StorageError

THRESHOLD_MICROSECONDS = 3_600_000_000


class StreakDataError(StorageError):
    """A saved interval cannot be allocated without guessing its dates or credit."""

    def __init__(self) -> None:
        super().__init__(
            "A saved timer interval has invalid dates or confirmed time, so daily progress "
            "could not be calculated safely. Your records were kept. Retry after restoring "
            "a verified backup or report this data error; no missing time was estimated."
        )


class StreakDay(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date
    active_microseconds: int
    qualified: bool


class StreakView(BaseModel):
    model_config = ConfigDict(frozen=True)

    today: date
    timezone: str
    threshold_microseconds: int = THRESHOLD_MICROSECONDS
    current_streak: int
    streak_through: date | None
    days: list[StreakDay]


def _instant(value: object) -> datetime:
    if not isinstance(value, str):
        raise StreakDataError()
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if instant.tzinfo is None or instant.utcoffset() is None:
            raise ValueError("Missing timezone")
        return instant.astimezone(UTC)
    except (ValueError, OverflowError):
        raise StreakDataError() from None


def _microseconds(value: timedelta) -> int:
    return (value.days * 86_400 + value.seconds) * 1_000_000 + value.microseconds


def _allocate(
    totals: dict[date, int], calendar: ApplicationCalendar,
    started_at: object, ended_at: object, credit: object,
) -> None:
    start, end = _instant(started_at), _instant(ended_at)
    if not isinstance(credit, int) or isinstance(credit, bool) or credit < 0 or end < start:
        raise StreakDataError()
    wall_microseconds = _microseconds(end - start)
    if not wall_microseconds:
        # A clock can remain at one wall instant while the awake clock advances.
        # Attribute only its recorded credit, never an invented elapsed duration.
        try:
            totals[calendar.localize(start).date()] += credit
        except (ValueError, OverflowError):
            raise StreakDataError() from None
        return
    cursor, allocated = start, 0
    try:
        while cursor < end:
            local = calendar.localize(cursor)
            day = local.date()
            boundary = end
            if end - cursor > timedelta(hours=1):
                boundary = cursor + timedelta(hours=1)
            if day < date.max:
                boundary = min(boundary, calendar.next_midnight(cursor))
            if boundary <= cursor:
                raise StreakDataError()
            # A historic backward change at midnight can briefly enter tomorrow,
            # then return to yesterday. Split at offset changes as well as midnight.
            # IANA transitions are separated by more than an hour; bounded probes
            # and an integer bisection also work with per-instant system-local rules.
            if calendar.localize(boundary).utcoffset() != local.utcoffset():
                low, high = 0, _microseconds(boundary - cursor)
                while high - low > 1:
                    middle = (low + high) // 2
                    probe = cursor + timedelta(microseconds=middle)
                    if calendar.localize(probe).utcoffset() == local.utcoffset():
                        low = middle
                    else:
                        high = middle
                boundary = cursor + timedelta(microseconds=high)
            # Cumulative integer floors preserve every microsecond even when wall
            # and awake clocks drift, or tiny credit spans several calendar dates.
            cumulative = credit * _microseconds(boundary - start) // wall_microseconds
            totals[day] += cumulative - allocated
            allocated, cursor = cumulative, boundary
    except (ValueError, OverflowError):
        raise StreakDataError() from None


def get_streaks(db: Database, *, now: datetime | None = None) -> StreakView:
    instant = datetime.now(UTC) if now is None else now
    calendar = ApplicationCalendar.from_environment()
    today = calendar.localize(instant).date()
    totals: dict[date, int] = defaultdict(int)
    with db.read() as conn:
        # One query gives one SQLite snapshot. No derived counter or backfill write.
        rows = conn.execute(
            "SELECT i.started_at, i.ended_at, i.active_microseconds "
            "FROM timer_intervals AS i JOIN timer_sessions AS s ON s.id = i.session_id "
            "WHERE s.state = 'finished' AND i.ended_at IS NOT NULL "
            "AND NOT EXISTS (SELECT 1 FROM timer_interruptions AS interruption "
            "WHERE interruption.session_id = s.id AND interruption.resolved_at IS NULL)"
        ).fetchall()
    for row in rows:
        _allocate(totals, calendar, row["started_at"], row["ended_at"], row["active_microseconds"])
    qualifying = {day for day, credit in totals.items() if credit >= THRESHOLD_MICROSECONDS}
    through = today if today in qualifying else today - timedelta(days=1) if today > date.min else None
    current, cursor = 0, through
    while cursor is not None and cursor in qualifying:
        current += 1
        cursor = cursor - timedelta(days=1) if cursor > date.min else None
    days = [today - timedelta(days=offset) for offset in reversed(range(7)) if today.toordinal() > offset]
    return StreakView(
        today=today, timezone=calendar.label(instant), current_streak=current,
        streak_through=through if current else None,
        days=[StreakDay(date=day, active_microseconds=totals.get(day, 0), qualified=day in qualifying) for day in days],
    )
