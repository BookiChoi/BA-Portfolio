"""Analytical functions.

Each analytical question is implemented as its own, single-purpose
function. Functions in this module must never print or plot: they only
compute and return results (a DataFrame or a scalar). This keeps
analysis logic reusable and easy to unit test, independent of how the
results are eventually displayed or visualized.
"""

from __future__ import annotations

import pandas as pd

def analyze_monthly_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate sales totals by month.

    Placeholder example showing the expected shape of an analysis
    function: it takes a cleaned DataFrame and returns a new DataFrame
    with aggregated results. Replace the column names below with the
    real schema once it is known.

    Args:
        df: A cleaned DataFrame expected to contain a date column and a
            sales/revenue column.

    Returns:
        A DataFrame with one row per month and the aggregated sales
        total for that month.
    """
    # TODO: Replace "date" and "sales" with the real column names once
    # the dataset schema is known, e.g.:
    #   monthly = (
    #       df.assign(month=df["date"].dt.to_period("M"))
    #       .groupby("month")["sales"]
    #       .sum()
    #       .reset_index()
    #   )
    #   return monthly
    return pd.DataFrame(columns=["month", "sales"])

def analyze_country_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate revenue totals by country.

    Placeholder example demonstrating a groupby-style analysis function.
    Replace the column names below with the real schema once it is
    known.

    Args:
        df: A cleaned DataFrame expected to contain a country column and
            a revenue column.

    Returns:
        A DataFrame with one row per country and the aggregated revenue
        total for that country.
    """
    # TODO: Replace "country" and "revenue" with the real column names
    # once the dataset schema is known, e.g.:
    #   return (
    #       df.groupby("country")["revenue"]
    #       .sum()
    #       .reset_index()
    #       .sort_values("revenue", ascending=False)
    #   )
    return pd.DataFrame(columns=["country", "revenue"])

# TODO: Add future analytical functions below, following the same
# pattern: one function per question, no printing, no plotting, and a
# DataFrame or scalar return value. Examples of future analyses:
#   - analyze_customer_retention(df)
#   - analyze_product_performance(df)
#   - analyze_average_order_value(df)
