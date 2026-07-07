"""Entry point for the Cornerstone_Data_Pipeline pipeline.

Running this script executes the full pipeline end to end:

    Load -> Clean -> Analyze -> Visualize

This file intentionally contains no business logic. It only wires
together the reusable building blocks defined in the ``pipeline``
package. Dataset-specific paths and analysis choices should be adjusted
here as the project develops.
"""

from __future__ import annotations

from pathlib import Path

from pipeline.analyze import analyze_country_revenue, analyze_monthly_sales
from pipeline.clean import clean
from pipeline.load import load_raw
from pipeline.visualize import plot_country_revenue, plot_monthly_sales

DATA_PATH = Path("data/raw_data.csv")
OUTPUTS_DIR = Path("outputs")

def run_pipeline(data_path: Path = DATA_PATH, outputs_dir: Path = OUTPUTS_DIR) -> None:
    """Run the full Load -> Clean -> Analyze -> Visualize pipeline.

    Args:
        data_path: Path to the raw input CSV file.
        outputs_dir: Directory where generated figures should be saved.
    """
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load
    raw_df = load_raw(str(data_path))

    # 2. Clean
    clean_df = clean(raw_df)

    # 3. Analyze
    monthly_sales = analyze_monthly_sales(clean_df)
    country_revenue = analyze_country_revenue(clean_df)
    # TODO: Add future analytical calls here, e.g.:
    #   retention = analyze_customer_retention(clean_df)

    # 4. Visualize
    monthly_sales_fig = plot_monthly_sales(monthly_sales)
    country_revenue_fig = plot_country_revenue(country_revenue)
    # TODO: Add future visualization calls here, e.g.:
    #   retention_fig = plot_customer_retention(retention)

    monthly_sales_fig.savefig(outputs_dir / "monthly_sales.png")
    country_revenue_fig.savefig(outputs_dir / "country_revenue.png")

if __name__ == "__main__":
    run_pipeline()
