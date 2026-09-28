import pandas as pd
import pytest
from src.features.momentum import compute_momentum

DATES = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-05", "2026-01-06", "2026-01-07"])


def test_known_values():
    prices = pd.DataFrame({"A": [100.0, 110.0, 120.0, 130.0, 140.0],
                           "B": [50.0, 50.0, 40.0, 40.0, 60.0]}, index=DATES)
    out = compute_momentum(prices, formation_days=3, skip_days=1)
    # row 3: price[2]/price[0]-1 ; row 4: price[3]/price[1]-1
    assert out["A"].iloc[:3].isna().all()
    assert out["A"].iloc[3] == pytest.approx(0.2)
    assert out["A"].iloc[4] == pytest.approx(130.0 / 110.0 - 1)
    assert out["B"].iloc[3] == pytest.approx(-0.2)
    assert out["B"].iloc[4] == pytest.approx(-0.2)


def test_gap_gives_nan():
    prices = pd.DataFrame({"A": [100.0, float("nan"), 120.0, 130.0, 140.0]}, index=DATES)
    out = compute_momentum(prices, formation_days=3, skip_days=1)
    assert pd.isna(out["A"].iloc[4])          # needs price[1], which is missing
    assert out["A"].iloc[3] == pytest.approx(0.2)


def test_no_lookahead():
    prices = pd.DataFrame({"A": [100.0, 110.0, 120.0, 130.0, 140.0]}, index=DATES)
    changed = prices.copy()
    changed.iloc[4, 0] = 999.0                 # change only the last day
    a = compute_momentum(prices, 3, 1)
    b = compute_momentum(changed, 3, 1)
    assert a.iloc[:4].equals(b.iloc[:4])      # earlier values unaffected
    assert a.iloc[4, 0] == b.iloc[4, 0]       # skip_days=1: day 4 doesn't use day 4's own price


def test_bad_days_raise():
    prices = pd.DataFrame({"A": [100.0, 110.0, 120.0, 130.0, 140.0]}, index=DATES)
    with pytest.raises(ValueError):
        compute_momentum(prices, formation_days=2, skip_days=2)


def test_unsorted_index_raises():
    prices = pd.DataFrame({"A": [100.0, 110.0, 120.0, 130.0, 140.0]}, index=DATES[::-1])
    with pytest.raises(ValueError):
        compute_momentum(prices, 3, 1)


def test_nonpositive_price_raises():
    prices = pd.DataFrame({"A": [100.0, 0.0, 120.0, 130.0, 140.0]}, index=DATES)
    with pytest.raises(ValueError):
        compute_momentum(prices, 3, 1)
