"""Shared text validation for application functions.

Titles and project names follow the same rule, so the rule lives in one place:
trim whitespace and invisible characters, reject what is empty or over-long, and
reject text SQLite cannot store.
"""

from __future__ import annotations

import unicodedata

from backend.domain.errors import InvalidInput


def _is_invisible(char: str) -> bool:
    # Whitespace, separators, control and format characters such as U+200B and U+FEFF.
    return char.isspace() or unicodedata.category(char)[0] in "ZC"


def trim_invisible(value: str) -> str:
    """Strip leading/trailing whitespace and invisible characters, keeping the inside intact."""
    start, end = 0, len(value)
    while start < end and _is_invisible(value[start]):
        start += 1
    while end > start and _is_invisible(value[end - 1]):
        end -= 1
    return value[start:end]


def clean_text(
    value: object,
    field: str,
    *,
    max_length: int,
    required: bool,
    empty_message: str,
    long_message: str,
) -> str:
    """Validate and normalize user-entered text, or raise InvalidInput naming the field."""
    if not isinstance(value, str):
        raise InvalidInput(field, f"{field.capitalize()} must be text.")
    cleaned = trim_invisible(value)
    if not cleaned and required:
        raise InvalidInput(field, empty_message)
    try:
        cleaned.encode("utf-8")
    except UnicodeEncodeError:
        raise InvalidInput(field, "That text contains characters that cannot be saved.") from None
    # Count code points, as the stored CHECK constraints do.
    if len(cleaned) > max_length:
        raise InvalidInput(field, long_message)
    return cleaned
