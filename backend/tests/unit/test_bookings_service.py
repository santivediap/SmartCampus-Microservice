import pytest

from app.services.bookings import overlaps


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (("10:00", "12:00"), ("11:00", "13:00"), True),  # partial overlap
        (("10:00", "12:00"), ("10:30", "11:30"), True),  # contained
        (("10:00", "12:00"), ("12:00", "13:00"), False),  # touching
        (("10:00", "12:00"), ("08:00", "09:00"), False),  # before
    ],
)
def test_overlaps(a, b, expected):
    assert overlaps(*a, *b) is expected
