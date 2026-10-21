"""Confirmed-time rewards and serialized cosmetic purchases.

Only new-session enrollment establishes eligibility. The timer calls award_session
inside its finalization transaction; reads and purchase retries never mint coins.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import sqlite3
from typing import Literal, Mapping
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict

from backend.domain.errors import InvalidInput
from backend.storage.db import Database, utc_now

Species = Literal["pine", "birch", "oak", "cherry"]
SPECIES_NAMES = {"pine": "Pine", "birch": "Birch", "oak": "Oak", "cherry": "Cherry"}


class ShopConflict(InvalidInput):
    """A purchase cannot safely use the displayed balance, price or request ID."""


@dataclass(frozen=True)
class RewardConfig:
    """Configurable proposed defaults, fixed for this service process."""

    coins_per_minute: int = 1
    birch_price: int = 30
    oak_price: int = 60
    cherry_price: int = 120

    def __post_init__(self) -> None:
        for name, maximum in (("coins_per_minute", 1_000_000), ("birch_price", 1_000_000_000),
                              ("oak_price", 1_000_000_000), ("cherry_price", 1_000_000_000)):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
                raise ValueError(f"BEARPLANS_{name.upper()} must be a whole number from 0 to {maximum}.")

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> RewardConfig:
        source = os.environ if environment is None else environment
        values = {}
        for name in ("coins_per_minute", "birch_price", "oak_price", "cherry_price"):
            key = f"BEARPLANS_{name.upper()}"
            if key in source:
                try:
                    # Reject decimal notation and other ambiguous configuration.
                    if not source[key].isascii() or not source[key].isdecimal():
                        raise ValueError
                    values[name] = int(source[key])
                except (ValueError, TypeError):
                    raise ValueError(f"{key} must be a nonnegative whole number.") from None
        return cls(**values)

    def price(self, species: str) -> int:
        return 0 if species == "pine" else getattr(self, f"{species}_price")


class ShopSpecies(BaseModel):
    id: Species
    name: str
    price: int
    owned: bool


class LedgerEntry(BaseModel):
    id: str
    kind: Literal["session_award", "purchase"]
    amount: int
    session_id: str | None
    species: Species | None
    created_at: str


class ShopView(BaseModel):
    balance: int
    coins_per_minute: int
    species: list[ShopSpecies]
    recent_entries: list[LedgerEntry]


class PurchaseResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    operation_id: str
    species: Species
    price: int
    balance: int


def normalize_species(value: object) -> Species:
    if not isinstance(value, str) or value.strip().lower() not in SPECIES_NAMES:
        raise InvalidInput("species", "Choose Pine, Birch, Oak or Cherry.")
    return value.strip().lower()  # type: ignore[return-value]


def require_owned_species(conn: sqlite3.Connection, value: object) -> Species:
    species = normalize_species(value)
    if species != "pine" and conn.execute(
        "SELECT 1 FROM owned_species WHERE species = ?", (species,),
    ).fetchone() is None:
        raise InvalidInput("species", "Buy this species in the tree shop before starting a countdown with it.")
    return species


def enroll_coins(conn: sqlite3.Connection, session_id: str, config: RewardConfig) -> None:
    conn.execute("INSERT INTO coin_enrollments VALUES (?, ?)", (session_id, config.coins_per_minute))


def award_session(conn: sqlite3.Connection, session_id: str) -> None:
    """Save exactly one initial award, including zero, for an enrolled final result."""
    row = conn.execute(
        "SELECT timer_sessions.*, coin_enrollments.coins_per_minute FROM timer_sessions"
        " JOIN coin_enrollments ON coin_enrollments.session_id = timer_sessions.id WHERE timer_sessions.id = ?",
        (session_id,),
    ).fetchone()
    if row is None:
        return
    if row["state"] != "finished" or conn.execute(
        "SELECT 1 FROM timer_interruptions WHERE session_id = ? AND resolved_at IS NULL", (session_id,),
    ).fetchone():
        raise ValueError("A coin award requires a finalized countdown with resolved interruptions.")
    amount = (row["active_microseconds"] // 60_000_000) * row["coins_per_minute"]
    conn.execute(
        "INSERT INTO coin_ledger (id, kind, amount, session_id, created_at) VALUES (?, 'session_award', ?, ?, ?)"
        " ON CONFLICT(session_id) WHERE kind = 'session_award' DO NOTHING",
        (str(uuid4()), amount, session_id, row["finished_at"]),
    )


def session_award(conn: sqlite3.Connection, session_id: str) -> int | None:
    row = conn.execute("SELECT amount FROM coin_ledger WHERE session_id = ? AND kind = 'session_award'", (session_id,)).fetchone()
    return None if row is None else row["amount"]


def _balance(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COALESCE(SUM(amount), 0) FROM coin_ledger").fetchone()[0]


class ShopService:
    def __init__(self, db: Database, config: RewardConfig | None = None) -> None:
        self.db = db
        self.config = RewardConfig.from_environment() if config is None else config

    def get(self) -> ShopView:
        with self.db.read() as conn:
            # One read snapshot keeps balance, ownership and history consistent
            # when a second tab finishes or buys a species during this request.
            conn.execute("BEGIN")
            owned = {row[0] for row in conn.execute("SELECT species FROM owned_species")}
            return ShopView(
                balance=_balance(conn), coins_per_minute=self.config.coins_per_minute,
                species=[ShopSpecies(id=key, name=name, price=self.config.price(key), owned=key == "pine" or key in owned)
                         for key, name in SPECIES_NAMES.items()],
                recent_entries=[LedgerEntry(**dict(row)) for row in conn.execute(
                    "SELECT * FROM coin_ledger ORDER BY rowid DESC LIMIT 50",
                )],
            )

    def purchase(self, species: object, expected_price: object, operation_id: object) -> PurchaseResult:
        selected = normalize_species(species)
        if isinstance(expected_price, bool) or not isinstance(expected_price, int) or expected_price < 0:
            raise InvalidInput("expected_price", "Refresh the shop and review this species price before buying.")
        try:
            if not isinstance(operation_id, str):
                raise ValueError
            key = str(UUID(operation_id))
        except ValueError:
            raise InvalidInput("operation_id", "Use a valid new UUID for this purchase, then retry.") from None
        fingerprint = json.dumps({"species": selected, "expected_price": expected_price}, sort_keys=True, separators=(",", ":"))
        with self.db.write() as conn:
            receipt = conn.execute("SELECT * FROM shop_operations WHERE operation_id = ?", (key,)).fetchone()
            if receipt is not None:
                if receipt["fingerprint"] != fingerprint:
                    raise ShopConflict("operation_id", "This purchase ID was already used for different work. Refresh the shop and try again.")
                return PurchaseResult.model_validate_json(receipt["result_json"])
            if selected == "pine" or conn.execute("SELECT 1 FROM owned_species WHERE species = ?", (selected,)).fetchone():
                raise ShopConflict("species", "You already own this species. Choose it when starting a new countdown.")
            price = self.config.price(selected)
            if expected_price != price:
                raise ShopConflict("expected_price", "This species price changed. Refresh the shop and review its current price before buying.")
            balance = _balance(conn)
            if balance < 0 or balance < price:
                raise ShopConflict("balance", "There are not enough available coins for this species. Finish more confirmed tracking time, then refresh the shop.")
            at = utc_now()
            conn.execute("INSERT INTO owned_species VALUES (?, ?)", (selected, at))
            conn.execute(
                "INSERT INTO coin_ledger (id, kind, amount, species, created_at) VALUES (?, 'purchase', ?, ?, ?)",
                (str(uuid4()), -price, selected, at),
            )
            result = PurchaseResult(operation_id=key, species=selected, price=price, balance=balance - price)
            conn.execute("INSERT INTO shop_operations VALUES (?, ?, ?)", (key, fingerprint, result.model_dump_json()))
            return result
