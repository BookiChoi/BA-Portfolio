"""Data loading utilities.

This module is responsible for ONE thing only: reading raw data from disk
into a pandas DataFrame. It must never clean, transform, analyze, or
visualize data. Keeping loading logic isolated makes it easy to swap data
sources (CSV, Excel, a database, an API, etc.) without touching the rest
of the pipeline.
"""

from __future__ import annotations

import pandas as pd

def load_raw(path: str) -> pd.DataFrame:
    """Load a raw dataset from a CSV file into a DataFrame.

    This function performs no cleaning, analysis, or visualization. It is
    intentionally kept simple so that swapping the data source later
    (e.g. a different file format or a database connection) only
    requires changes in this function.

    Args:
        path: Path to the CSV file to load.

    Returns:
        The raw dataset as a pandas DataFrame, unmodified.

    Raises:
        FileNotFoundError: If no file exists at the given path.
        pd.errors.EmptyDataError: If the file exists but contains no data.
    """
    return pd.read_csv(path)
