"""Data cleaning utilities.

This module is responsible for taking a raw DataFrame and returning a
cleaned DataFrame that is ready for analysis. Each transformation below
is a placeholder example meant to be adapted to the specifics of a real
dataset. Every step explains WHY it is done, not just what it does, so
future contributors understand the reasoning before changing it.
"""

from __future__ import annotations

import pandas as pd

def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean a raw DataFrame and prepare it for analysis.

    This function chains together small, well-documented transformation
    steps. It is a starter template: the individual steps are placeholder
    examples and should be replaced or extended with dataset-specific
    logic as the project develops.

    Args:
        df: The raw DataFrame, typically produced by ``load.load_raw``.

    Returns:
        A cleaned copy of the input DataFrame.
    """
    cleaned_df = df.copy()

    cleaned_df = _remove_duplicates(cleaned_df)
    cleaned_df = _handle_missing_values(cleaned_df)
    cleaned_df = _fix_dtypes(cleaned_df)

    return cleaned_df

def _remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove fully duplicated rows.

    WHY: Duplicate rows (e.g. from repeated exports or double form
    submissions) would otherwise be double-counted in downstream
    aggregations, skewing analysis results.

    Args:
        df: The DataFrame to de-duplicate.

    Returns:
        A DataFrame with duplicate rows removed.
    """
    return df.drop_duplicates()

def _handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values in the dataset.

    WHY: Downstream analysis and visualization functions often assume
    non-null values (e.g. for grouping or arithmetic). Silently leaving
    NaNs in place can cause misleading aggregations or runtime errors,
    so missing values must be explicitly addressed and documented.

    This is a placeholder strategy. Replace it with logic appropriate to
    each column once the real dataset schema is known, for example:
        - Dropping rows missing a required identifier.
        - Filling numeric columns with a median/mean.
        - Filling categorical columns with a sentinel value like
          "Unknown".

    Args:
        df: The DataFrame whose missing values should be handled.

    Returns:
        A DataFrame with missing values addressed.
    """
    # Placeholder: drop rows where ALL values are missing, since such
    # rows carry no information at all. Column-specific handling should
    # be added here once real columns are known.
    return df.dropna(how="all")

def _fix_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure columns have the correct, analysis-ready data types.

    WHY: Data loaded from CSV files is often typed incorrectly (e.g.
    dates loaded as strings, IDs loaded as floats). Incorrect dtypes can
    break sorting, grouping, and time-based analysis, so types should be
    normalized as early as possible in the pipeline.

    This is a placeholder that performs no conversions yet. Add
    dataset-specific conversions here once real column names are known,
    for example:
        df["order_date"] = pd.to_datetime(df["order_date"])
        df["customer_id"] = df["customer_id"].astype("string")

    Args:
        df: The DataFrame whose dtypes should be normalized.

    Returns:
        A DataFrame with corrected data types.
    """
    return df
