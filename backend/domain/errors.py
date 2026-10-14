class InvalidInput(ValueError):
    """A caller supplied a value the application rules reject."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field
        self.message = message
