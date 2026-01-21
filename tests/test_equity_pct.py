### Headcount Simulator App
### m02n/tests/test_equity_pct.py
###
### Author: Sharon + GitHub Copilot
### Date: Jan 20, 2026
###
### Headcount app tests for equity percentage feature.

import pandas as pd
import pytest
from pathlib import Path


def _load_any_equity_column(csv_path: Path) -> pd.Series:
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    # preferred column
    if "equity_pct" in df.columns:
        col = "equity_pct"
    elif "equity" in df.columns:
        col = "equity"
    elif "equity_shares" in df.columns:
        col = "equity_shares"
    else:
        return pd.Series(dtype=float)
    # coerce numeric, remove empty strings
    series = pd.to_numeric(df[col].replace("", pd.NA), errors="coerce").dropna()
    return series.astype(float)


def test_equity_pct_under_100_default_roster():
    path = Path(__file__).parent.parent / "data_room/people/employee_roster.csv"
    series = _load_any_equity_column(path)
    # If equity column is present, assert all values are <= 100
    if not series.empty:
        assert series.max() <= 100.0, f"Found equity value > 100 in {path}: {series.max()}"


def test_equity_pct_under_100_uploaded_seed():
    path = Path(__file__).parent.parent / "employee_roster_seed_startup.csv"
    series = _load_any_equity_column(path)
    if not series.empty:
        assert series.max() <= 100.0, f"Found equity value > 100 in {path}: {series.max()}"

