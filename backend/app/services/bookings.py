"""Booking business rules (no Flask imports)."""


def overlaps(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
    """Return True if two HH:MM time ranges overlap.

    Ranges that only touch (10:00-12:00 and 12:00-13:00) do not overlap.
    """
    return start_a < end_b and end_a > start_b


# TODO: create_booking, list_bookings, delete_booking
