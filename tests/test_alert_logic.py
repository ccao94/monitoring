SIGNIFICANT_DROP = 0.10


def should_alert(previous, current, threshold):
    """Mirrors the decision logic in main.py."""
    crossed = current < threshold and (previous is None or previous >= threshold)
    big_drop = previous is not None and current < previous * (1 - SIGNIFICANT_DROP)
    if crossed:
        return "threshold"
    if big_drop:
        return "drop"
    return None


def test_first_check_below_threshold():
    assert should_alert(None, 550.0, 600.0) == "threshold"


def test_first_check_above_threshold():
    assert should_alert(None, 700.0, 600.0) is None


def test_crossing_threshold():
    assert should_alert(650.0, 550.0, 600.0) == "threshold"


def test_still_below_threshold_stays_quiet():
    assert should_alert(550.0, 545.0, 600.0) is None


def test_big_drop_above_threshold():
    assert should_alert(900.0, 780.0, 600.0) == "drop"


def test_small_drop_stays_quiet():
    assert should_alert(900.0, 880.0, 600.0) is None


def test_price_increase_stays_quiet():
    assert should_alert(550.0, 650.0, 600.0) is None