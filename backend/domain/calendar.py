"""The service's calendar: configured IANA rules or the OS rules at each instant."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from backend.domain.errors import InvalidInput


@dataclass(frozen=True)
class ApplicationCalendar:
    zone: ZoneInfo | None

    @classmethod
    def from_environment(cls) -> ApplicationCalendar:
        configured = os.environ.get("BEARPLANS_TIMEZONE", "").strip()
        if not configured:
            return cls(None)
        try:
            return cls(ZoneInfo(configured))
        except (ZoneInfoNotFoundError, ValueError):
            raise InvalidInput(
                "timezone",
                "BEARPLANS_TIMEZONE must name an installed IANA timezone, such as "
                "America/Los_Angeles. Correct it or unset it to use system local time.",
            ) from None

    def localize(self, instant: datetime) -> datetime:
        if instant.tzinfo is None or instant.utcoffset() is None:
            raise ValueError("The application clock must be timezone-aware.")
        # astimezone() without a zone consults OS rules for this particular instant.
        # Its returned tzinfo is a fixed offset and must never be reused for another day.
        return instant.astimezone(self.zone) if self.zone is not None else instant.astimezone()

    def label(self, instant: datetime) -> str:
        return self.zone.key if self.zone is not None else f"System local ({self.localize(instant).tzname()})"

    def next_midnight(self, instant: datetime) -> datetime:
        tomorrow = self.localize(instant).date() + timedelta(days=1)
        midnight = datetime.combine(tomorrow, time.min)
        # For system local time a naive astimezone() resolves the OS rules for that
        # midnight, rather than reusing today's fixed UTC offset across DST.
        if self.zone is not None:
            midnight = midnight.replace(tzinfo=self.zone)
        boundary = midnight.astimezone(UTC)
        if boundary <= instant:
            # Midnight itself may occur twice after a historic backward change.
            # A cursor past its first occurrence needs the second one.
            boundary = midnight.replace(fold=1).astimezone(UTC)
        return boundary


def application_today(now: datetime | None = None) -> tuple[date, str]:
    instant = datetime.now(UTC) if now is None else now
    calendar = ApplicationCalendar.from_environment()
    return calendar.localize(instant).date(), calendar.label(instant)
