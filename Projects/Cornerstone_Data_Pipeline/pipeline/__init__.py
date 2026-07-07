"""Cornerstone_Data_Pipeline pipeline package.

This package contains the modular building blocks of the data pipeline:

- ``load``: functions for reading raw data into memory.
- ``clean``: functions for cleaning and preparing data for analysis.
- ``analyze``: functions that compute analytical results from clean data.
- ``visualize``: functions that turn analytical results into charts.

Each module is intentionally kept independent so that it can be reused,
tested, and extended in isolation.
"""
