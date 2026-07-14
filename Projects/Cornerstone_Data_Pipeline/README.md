# Online Retail — Business Growth Opportunity Analysis

An end-to-end data analysis project exploring business growth opportunities in a UK-based online retail dataset.
The project covers question-driven **Exploratory Data Analysis (EDA)** and a modular **Load → Clean → Analyze → Visualize** pipeline implemented in Python.

**Portfolio project by Booki Choi — July 2026**

---

## Business Questions

Five questions were defined before analysis began, following the logic:
**WHERE → WHEN → WHAT → HOW MUCH → WHO**

| # | Question | Key Finding |
|---|----------|-------------|
| Q1 | Which countries generate the most revenue? | UK = 84.6% of revenue (£9.0M of £10.6M). Top non-UK markets: Netherlands, Ireland, Germany, France |
| Q2 | How has monthly revenue changed over time? | 83% revenue growth Dec 2010 → Nov 2011. November is the peak month every year |
| Q3 | Which products drive the most revenue? | Top 20% of products (804 of 4,020) generate **78.7%** of revenue. High revenue ≠ high frequency |
| Q4 | How are customer order values distributed? | Median order £304 vs mean £534 — heavily right-skewed. Top 0.9% of orders drive **18.6%** of revenue |
| Q5 | Who are the highest-value customers? | Top 20% of customers (866 of 4,333) generate **74.6%** of revenue. VIPs peak in November; non-VIPs in December |

---

## Dataset

| Attribute | Detail |
|-----------|--------|
| Source | [UCI Machine Learning Repository — Online Retail](https://archive.ics.uci.edu/ml/datasets/online+retail) |
| Period | December 2010 – December 2011 |
| Raw rows | ~541,000 transactions |
| Cleaned rows | ~530,000 |
| Columns | InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country |
| Countries | 38 |
| Revenue basis | Gross (Quantity × UnitPrice); cancellation invoices excluded |

**Data quality issues handled:**
- Cancellations (`C`-prefix `InvoiceNo`) → removed via `Quantity <= 0` filter
- Accounting adjustments (`A`-prefix `InvoiceNo`, e.g. "Adjust bad debt") → removed explicitly
- Zero / negative `UnitPrice` → removed
- Non-standard country names: `EIRE → Ireland`, `RSA → South Africa`
- Non-country values: `Unspecified`, `European Community` → removed
- ~24.9% of rows have no `CustomerID` — confirmed as guest purchases, retained for Q1–Q4, excluded for Q5

> **Note:** The dataset is UK-biased. Findings reflect the behaviour of a UK-centric retailer and should not be generalised to global markets.

---

## Project Structure

```
Cornerstone_Data_Pipeline/
│
├── README.md
├── main.py                         # Pipeline entry point (CLI)
├── requirements.txt
│
├── data/
│   └── online_retail.xlsx          # Raw dataset (not tracked in git)
│
├── outputs/                        # Generated charts and summary CSVs
│   ├── q1_uk_vs_others.png
│   ├── q1_country_revenue.png / .csv
│   ├── q2_monthly_revenue.png
│   ├── q2_monthly_revenue_bar.png / .csv
│   ├── q3_pareto.png
│   ├── q3_top_products.png / .csv
│   ├── q3_product_segments.png
│   ├── q4_order_value_histogram.png
│   ├── q4_order_value_boxplot.png
│   ├── q4_large_order_impact.csv
│   ├── q5_top_customers.png / .csv
│   ├── q5_customer_segments.png
│   ├── q5_customer_revenue_hist.png
│   └── q5_vip_seasonal.png
│
├── pipeline/                       # Core pipeline package
│   ├── load.py                     # I/O only — load .xlsx or .csv
│   ├── clean.py                    # All cleaning rules with WHY comments
│   ├── analyze.py                  # Pure functions — no printing, no plotting
│   └── visualize.py                # Returns Figure objects — no plt.show()
│
├── notebooks/
│   └── business_eda.ipynb          # Question-driven EDA notebook
│
├── tests/
│   ├── test_load.py
│   └── test_clean.py
│
└── .github/workflows/ci.yml        # GitHub Actions: install + pytest on push/PR
```

---

## Pipeline Architecture

```
load_raw()          load.py     Read .xlsx / .csv → raw DataFrame
    ↓
clean()             clean.py    Apply 6 global cleaning rules → cleaned DataFrame
get_customer_df()               Q5-only subset (CustomerID NaN removed)
    ↓
analyze_*()         analyze.py  One function per business question → DataFrame or dict
    ↓
plot_*()            visualize.py One function per chart → matplotlib Figure
    ↓
main.py                         Save 13 PNGs + 5 CSVs to outputs/
```

**Design principles:**
- `analyze.py` functions are side-effect-free — no printing, no plotting, independently testable
- `visualize.py` functions return `Figure` objects and never call `plt.show()` — the caller controls rendering
- Each cleaning rule in `clean.py` has a `WHY:` comment explaining the business reason

---

## Installation

```bash
cd Projects/Cornerstone_Data_Pipeline

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Place the raw dataset at `data/online_retail.xlsx`.

---

## Usage

**Run the full pipeline:**

```bash
python main.py
```

**Custom paths:**

```bash
python main.py --data data/online_retail.xlsx --output outputs/
```

All 13 charts and 5 summary CSVs are saved to `outputs/`.

**Run tests:**

```bash
pytest
```

---

## Outputs

| File | Description |
|------|-------------|
| `q1_uk_vs_others.png` | Donut chart: UK (84.6%) vs Other Countries |
| `q1_country_revenue.png` | Bar chart: all non-UK countries by revenue |
| `q1_country_revenue.csv` | Revenue and share % for all non-UK countries |
| `q2_monthly_revenue.png` | Line chart: monthly revenue Dec 2010 – Dec 2011 |
| `q2_monthly_revenue_bar.png` | Bar chart: same data, easier per-month comparison |
| `q2_monthly_revenue.csv` | Monthly revenue table |
| `q3_pareto.png` | Pareto chart: top 20% products → 78.7% of revenue |
| `q3_top_products.png` | Top 20 products by revenue with frequency rank |
| `q3_top_products.csv` | Top 20 products table |
| `q3_product_segments.png` | 4-quadrant scatter: revenue vs frequency per product |
| `q4_order_value_histogram.png` | Order value distribution (capped at p99 = £4,806) |
| `q4_order_value_boxplot.png` | Box plot: same data showing spread |
| `q4_large_order_impact.csv` | Revenue share from orders above £500 / £1K / £5K / £10K |
| `q5_top_customers.png` | Top 20 customers by revenue with order count |
| `q5_top_customers.csv` | Top 20 customers table |
| `q5_customer_segments.png` | 4-quadrant scatter: VIP / Big Spender / Loyal / Casual |
| `q5_customer_revenue_hist.png` | Customer revenue distribution (capped at p99) |
| `q5_vip_seasonal.png` | VIP vs Non-VIP monthly revenue (normalised 0–100) |

---

## Key Cross-Question Insights

**1. November spike is driven by VIP customers**
Overall revenue peaks in November (Q2). VIP customers peak even more sharply in November (Q5).
VIP bulk pre-purchasing is the primary driver of the seasonal spike.

**2. Concentration risk at every level**
- Q1: 1 country (UK) = 84.6% of revenue
- Q3: Top 20% of products = 78.7% of revenue
- Q5: Top 20% of customers = 74.6% of revenue

The business is structurally dependent on a small group at every dimension.

**3. Large orders (Q4) and B2B customers (Q5) are the same phenomenon**
Top 0.9% of orders (above £5,000) drive 18.6% of revenue.
These map directly to the High Rev / Low Freq "Big Spender" customer segment —
likely B2B buyers purchasing premium niche products in bulk.

---

## Tech Stack

- Python 3.12
- pandas, openpyxl
- matplotlib, seaborn
- pytest
- GitHub Actions (CI)
