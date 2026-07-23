import pytest

from src.alerting import decide_alert


def test_first_check_below_threshold():
    assert decide_alert(None, 550.0, 600.0) == "threshold"


def test_first_check_above_threshold():
    assert decide_alert(None, 700.0, 600.0) is None


def test_crossing_threshold():
    assert decide_alert(650.0, 550.0, 600.0) == "threshold"


def test_still_below_threshold_stays_quiet():
    assert decide_alert(550.0, 545.0, 600.0) is None


def test_big_drop_above_threshold():
    assert decide_alert(900.0, 780.0, 600.0) == "drop"


def test_small_drop_stays_quiet():
    assert decide_alert(900.0, 880.0, 600.0) is None


def test_price_increase_stays_quiet():
    assert decide_alert(550.0, 650.0, 600.0) is None


def test_exactly_at_threshold_is_not_below():
    assert decide_alert(620.0, 600.0, 600.0) is None


@pytest.mark.parametrize(
    "previous, current, expected",
    [
        (1000.0, 900.0, None),
        (1000.0, 899.0, "drop"),
    ],
)
def test_drop_boundary(previous, current, expected):
    assert decide_alert(previous, current, 500.0) == expected
