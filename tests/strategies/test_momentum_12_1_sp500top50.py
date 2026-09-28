import datetime as dt

import pandas as pd
import pytest
from src.strategies.momentum_12_1_sp500top50 import month_end_rebalance_dates, monthly_target_weights

D = [dt.date(2026, 1, 29), dt.date(2026, 1, 30), dt.date(2026, 2, 2), dt.date(2026, 2, 27),
     dt.date(2026, 3, 2), dt.date(2026, 3, 3)]


def test_month_ends_exclude_last_date():
    assert month_end_rebalance_dates(pd.Index(D)) == [dt.date(2026, 1, 30), dt.date(2026, 2, 27)]


def test_weights_on_month_ends_only():
    mom = pd.DataFrame({
        "A": [0.1, 0.30, 0.0, 0.10, 0.0, 0.0],
        "B": [0.1, 0.20, 0.0, 0.40, 0.0, 0.0],
        "C": [0.1, 0.10, 0.0, 0.30, 0.0, 0.0],
        "D": [0.1, -0.10, 0.0, 0.20, 0.0, 0.0],
        "E": [0.1, -0.20, 0.0, float("nan"), 0.0, 0.0],
    }, index=pd.Index(D))
    w = monthly_target_weights(mom, n_long=1, n_short=1, weight_per_position=0.1)
    jan = w.loc[dt.date(2026, 1, 30)].to_dict()
    feb = w.loc[dt.date(2026, 2, 27)].to_dict()
    assert jan == {"A": 0.1, "B": 0.0, "C": 0.0, "D": 0.0, "E": -0.1}
    assert feb == {"A": -0.1, "B": 0.1, "C": 0.0, "D": 0.0, "E": 0.0}   # E has no value -> flat
    others = w.drop(index=[dt.date(2026, 1, 30), dt.date(2026, 2, 27)])
    assert others.isna().all().all()


def test_ties_broken_by_ticker_name():
    mom = pd.DataFrame({"B": [0.5, 0.0], "A": [0.5, 0.0], "C": [0.1, 0.0]},
                       index=pd.Index([dt.date(2026, 1, 30), dt.date(2026, 2, 2)]))
    w = monthly_target_weights(mom, n_long=1, n_short=1, weight_per_position=0.1)
    assert w.loc[dt.date(2026, 1, 30)].to_dict() == {"B": 0.0, "A": 0.1, "C": -0.1}


def test_too_few_names_skips_date():
    mom = pd.DataFrame({"A": [0.5, 0.0], "B": [float("nan"), 0.0]},
                       index=pd.Index([dt.date(2026, 1, 30), dt.date(2026, 2, 2)]))
    w = monthly_target_weights(mom, n_long=1, n_short=1)
    assert w.isna().all().all()


def test_bad_arguments_raise():
    mom = pd.DataFrame({"A": [0.5]}, index=pd.Index([dt.date(2026, 1, 30)]))
    with pytest.raises(ValueError):
        monthly_target_weights(mom, n_long=0, n_short=1)
    with pytest.raises(ValueError):
        monthly_target_weights(mom, n_long=1, n_short=1, weight_per_position=0.0)
