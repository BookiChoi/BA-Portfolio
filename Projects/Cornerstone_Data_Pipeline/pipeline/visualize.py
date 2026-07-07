"""Visualization functions.

Each chart is implemented as its own, single-purpose function. Functions
in this module accept already-processed DataFrames (typically the output
of an ``analyze`` function) and return a ``matplotlib.figure.Figure``
object. They must never call ``plt.show()``, so that the caller decides
how and where to display or save the figure (e.g. in a notebook, a web
app, or as a saved PNG file in ``outputs/``).
"""

from __future__ import annotations

import matplotlib.figure
import matplotlib.pyplot as plt
import pandas as pd

def plot_monthly_sales(df: pd.DataFrame) -> matplotlib.figure.Figure:
    """Create a line chart of monthly sales totals.

    Placeholder example showing the expected shape of a visualization
    function: it takes the output of an analysis function (e.g.
    ``analyze.analyze_monthly_sales``) and returns a Figure. Replace the
    column names below with the real schema once it is known.

    Args:
        df: A DataFrame with monthly sales totals, expected to contain a
            "month" column and a "sales" column.

    Returns:
        A matplotlib Figure containing the line chart. The figure is
        returned, not displayed, so the caller controls rendering.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    if not df.empty:
        ax.plot(df["month"].astype(str), df["sales"], marker="o")

    ax.set_title("Monthly Sales")
    ax.set_xlabel("Month")
    ax.set_ylabel("Sales")
    fig.tight_layout()

    return fig

def plot_country_revenue(df: pd.DataFrame) -> matplotlib.figure.Figure:
    """Create a bar chart of revenue by country.

    Placeholder example demonstrating a bar-chart style visualization
    function. Replace the column names below with the real schema once
    it is known.

    Args:
        df: A DataFrame with revenue totals, expected to contain a
            "country" column and a "revenue" column.

    Returns:
        A matplotlib Figure containing the bar chart. The figure is
        returned, not displayed, so the caller controls rendering.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    if not df.empty:
        ax.bar(df["country"].astype(str), df["revenue"])

    ax.set_title("Revenue by Country")
    ax.set_xlabel("Country")
    ax.set_ylabel("Revenue")
    fig.tight_layout()

    return fig

# TODO: Add future chart functions below, following the same pattern:
# one chart per function, accepting a processed DataFrame and returning
# a Figure, never calling plt.show(). Examples of future charts:
#   - plot_customer_retention(df)
#   - plot_product_performance(df)
