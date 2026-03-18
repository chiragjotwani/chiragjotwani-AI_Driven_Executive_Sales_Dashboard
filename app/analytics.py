from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class OverviewMetrics:
    total_sales: float
    average_order_value: float
    total_orders: int
    unique_customers: int


def compute_overview_metrics(df: pd.DataFrame) -> OverviewMetrics:
    return OverviewMetrics(
        total_sales=float(df["Sales"].sum()),
        average_order_value=float(df["Sales"].mean()) if not df.empty else 0.0,
        total_orders=int(df.shape[0]),
        unique_customers=int(df["Customer ID"].nunique()) if "Customer ID" in df else 0,
    )


def monthly_sales(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Month", "Sales"])

    monthly = (
        df.assign(Month=df["Order Date"].dt.to_period("M").dt.to_timestamp())
        .groupby("Month", as_index=False)["Sales"]
        .sum()
        .sort_values("Month")
    )
    return monthly


def sales_by_dimension(df: pd.DataFrame, dimension: str, limit: int = 10) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[dimension, "Sales"])

    grouped = (
        df.groupby(dimension, as_index=False)["Sales"]
        .sum()
        .sort_values("Sales", ascending=False)
        .head(limit)
    )
    return grouped


def top_products(df: pd.DataFrame, limit: int = 8) -> pd.DataFrame:
    return sales_by_dimension(df, "Product Name", limit)


def detect_monthly_anomalies(monthly_df: pd.DataFrame) -> pd.DataFrame:
    if monthly_df.empty or len(monthly_df) < 3:
        return pd.DataFrame(columns=["Month", "Sales", "Deviation"])

    baseline = monthly_df["Sales"].mean()
    std_dev = monthly_df["Sales"].std()
    if not std_dev or pd.isna(std_dev):
        return pd.DataFrame(columns=["Month", "Sales", "Deviation"])

    flagged = monthly_df.copy()
    flagged["Deviation"] = (flagged["Sales"] - baseline) / std_dev
    return flagged[flagged["Deviation"].abs() >= 1.0].sort_values("Month")


def build_insight_context(df: pd.DataFrame) -> dict:
    monthly = monthly_sales(df)
    regions = sales_by_dimension(df, "Region", 4)
    categories = sales_by_dimension(df, "Category", 5)
    segments = sales_by_dimension(df, "Segment", 5)
    products = top_products(df, 5)
    anomalies = detect_monthly_anomalies(monthly)
    metrics = compute_overview_metrics(df)

    return {
        "overview": {
            "total_sales": round(metrics.total_sales, 2),
            "average_order_value": round(metrics.average_order_value, 2),
            "total_orders": metrics.total_orders,
            "unique_customers": metrics.unique_customers,
            "date_range": (
                f"{df['Order Date'].min().date()} to {df['Order Date'].max().date()}"
                if not df.empty
                else "No data"
            ),
        },
        "monthly_sales": monthly.to_dict(orient="records"),
        "region_sales": regions.to_dict(orient="records"),
        "category_sales": categories.to_dict(orient="records"),
        "segment_sales": segments.to_dict(orient="records"),
        "top_products": products.to_dict(orient="records"),
        "anomalies": anomalies.to_dict(orient="records"),
    }

