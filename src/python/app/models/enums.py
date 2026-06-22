from enum import IntEnum


class PriceLevel(IntEnum):
    """Relative price tier for a location.

    Stored as a small integer in ``locations.price_level``; a DB CHECK
    constraint keeps the column restricted to these values.
    """

    CHEAP = 1
    STANDARD = 2
    EXPENSIVE = 3
