from __future__ import annotations

from functools import lru_cache

import pandas as pd

from app.config import AppConfig


@lru_cache(maxsize=1)
def load_sales_data(path: str | None = None) -> pd.DataFrame:
    config = AppConfig()
    csv_path = path or str(config.data_path)
    df = pd.read_csv(csv_path)
    df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True, errors="coerce")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], dayfirst=True, errors="coerce")
    df["Sales"] = pd.to_numeric(df["Sales"], errors="coerce").fillna(0.0)
    df["Postal Code"] = df["Postal Code"].astype("string")
    df = df.dropna(subset=["Order Date"]).sort_values("Order Date").reset_index(drop=True)
    return df


def apply_filters(
    df: pd.DataFrame,
    start_date,
    end_date,
    regions: list[str],
    segments: list[str],
    categories: list[str],
    sub_categories: list[str],
) -> pd.DataFrame:
    filtered = df.copy()
    filtered = filtered[
        (filtered["Order Date"].dt.date >= start_date)
        & (filtered["Order Date"].dt.date <= end_date)
    ]

    if regions:
        filtered = filtered[filtered["Region"].isin(regions)]
    if segments:
        filtered = filtered[filtered["Segment"].isin(segments)]
    if categories:
        filtered = filtered[filtered["Category"].isin(categories)]
    if sub_categories:
        filtered = filtered[filtered["Sub-Category"].isin(sub_categories)]

    return filtered.reset_index(drop=True)

