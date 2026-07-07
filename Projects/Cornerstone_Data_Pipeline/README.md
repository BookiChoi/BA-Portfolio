# Cornerstone Data Pipeline

A reusable, modular Python boilerplate for building data analysis pipelines. This template implements a clean **Load → Clean → Analyze → Visualize** architecture so that new data analysis projects can be started quickly, consistently, and with good testing practices from day one.

> This is a starter template. It contains no dataset-specific business logic — only well-documented placeholders and reusable structure meant to be extended.

## Project Overview

The goal of this project is to provide a production-quality skeleton for data analysis work that:

- Separates concerns into independent, single-responsibility modules (loading, cleaning, analyzing, visualizing).
- Keeps analysis functions free of side effects (no printing, no plotting) so they are easy to test and reuse.
- Keeps visualization functions free of side effects (no `plt.show()`) so figures can be displayed, saved, or embedded anywhere.
- Ships with a pytest test suite and a GitHub Actions CI workflow out of the box.

## Folder Structure

```
Cornerstone_Data_Pipeline/
│
├── README.md               # This file
├── main.py                  # Orchestrates the full pipeline
├── requirements.txt         # Python dependencies
├── .gitignore
├── pytest.ini                # Pytest configuration
│
├── data/                     # Place raw input datasets here (gitignored contents)
├── outputs/                  # Generated charts/results are saved here
│
├── pipeline/                  # Core pipeline package
│   ├── __init__.py
│   ├── load.py                # Load raw data (I/O only)
│   ├── clean.py                # Clean/prepare data
│   ├── analyze.py              # Compute analytical results
│   └── visualize.py            # Build matplotlib figures
│
├── tests/                     # Pytest test suite
│   ├── test_load.py
│   └── test_clean.py
│
└── .github/
    └── workflows/
        └── ci.yml              # CI: install deps + run pytest on push/PR
```

## Installation

1. Navigate into the project directory:

   ```bash
   cd Projects/Cornerstone_Data_Pipeline
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Place your raw CSV file inside the `data/` folder (e.g. `data/raw_data.csv`).
2. Run the full pipeline:

   ```bash
   python main.py
   ```

3. Generated charts will be saved to the `outputs/` folder.

You can also import and use each stage independently:

```python
from pipeline.load import load_raw
from pipeline.clean import clean
from pipeline.analyze import analyze_monthly_sales
from pipeline.visualize import plot_monthly_sales

df = load_raw("data/raw_data.csv")
df = clean(df)
result = analyze_monthly_sales(df)
fig = plot_monthly_sales(result)
fig.savefig("outputs/monthly_sales.png")
```

### Running Tests

```bash
pytest
```

## Features

- **Modular architecture**: each pipeline stage lives in its own module and can be developed, tested, and reused independently.
- **Side-effect-free analysis**: `analyze.py` functions only compute and return results — no printing, no plotting.
- **Side-effect-free visualization**: `visualize.py` functions return `matplotlib.figure.Figure` objects instead of calling `plt.show()`, so the caller controls rendering.
- **Documented placeholders**: cleaning steps explain *why* each transformation exists, making it easy for future contributors to adapt them.
- **Test suite included**: `pytest` tests using small dummy DataFrames verify core behavior of `load` and `clean`.
- **CI-ready**: a GitHub Actions workflow automatically installs dependencies and runs tests on every push/PR touching this project.
- **Type hints & Google-style docstrings** throughout, following PEP 8.

## Future Improvements

- Implement dataset-specific cleaning rules once a real schema is defined.
- Add more analytical functions in `analyze.py` (e.g. customer retention, product performance).
- Add corresponding chart functions in `visualize.py`.
- Add configuration support (e.g. YAML/CLI args) for data paths and pipeline parameters.
- Add logging instead of silent execution in `main.py`.
- Add integration tests that run the full pipeline end-to-end on a sample dataset.
- Add code quality tooling (e.g. `ruff`, `mypy`) to the CI workflow.
