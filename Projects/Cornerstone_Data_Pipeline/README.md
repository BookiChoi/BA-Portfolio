# Online Retail — Business Growth Opportunity Analysis
# 온라인 리테일 — 비즈니스 성장 기회 분석

An end-to-end data analysis project exploring business growth opportunities in a UK-based online retail dataset.
The project covers question-driven **Exploratory Data Analysis (EDA)** and a modular **Load → Clean → Analyze → Visualize** pipeline implemented in Python.
UK 기반 온라인 리테일 데이터셋에서 비즈니스 성장 기회를 탐색하는 엔드-투-엔드 데이터 분석 프로젝트.
질문 중심의 **탐색적 데이터 분석(EDA)** 과 모듈형 **Load → Clean → Analyze → Visualize** 파이프라인을 Python으로 구현했다.

**Portfolio project by Booki Choi — July 2026**

---

## Business Questions / 비즈니스 질문

Five questions were defined before analysis began, following the logic:
분석 전에 5개 질문을 먼저 정의했다. 질문은 아래 흐름을 따른다:

**WHERE → WHEN → WHAT → HOW MUCH → WHO**
**어디서 → 언제 → 무엇이 → 얼마에 → 누가**

| # | Question / 질문 | Key Finding / 핵심 발견 |
|---|----------------|----------------------|
| Q1 | Which countries generate the most revenue? / 어느 국가가 가장 많은 매출을 만드는가? | UK = 84.6% of revenue (£9.0M of £10.6M total). Top non-UK: Netherlands, Ireland, Germany, France |
| Q2 | How has monthly revenue changed over time? / 월별 매출은 어떻게 변해왔는가? | 83% revenue growth Dec 2010 → Nov 2011. November is the peak month |
| Q3 | Which products drive the most revenue? / 어떤 상품이 매출을 주도하는가? | Top 20% of products (804 of 4,020) generate **78.7%** of revenue. High revenue ≠ high frequency |
| Q4 | How are customer order values distributed? / 고객 주문 금액 분포는 어떻게 되는가? | Median order £304 vs mean £534 — heavily right-skewed. Top 0.9% of orders drive **18.6%** of revenue |
| Q5 | Who are the highest-value customers? / 가장 가치 있는 고객은 누구인가? | Top 20% of customers (866 of 4,333) generate **74.6%** of revenue. VIPs peak in November; non-VIPs in December |

---

## Dataset / 데이터셋

| Attribute / 항목 | Detail / 내용 |
|-----------------|--------------|
| Source / 출처 | [UCI Machine Learning Repository — Online Retail](https://archive.ics.uci.edu/ml/datasets/online+retail) |
| Period / 기간 | December 2010 – December 2011 |
| Raw rows / 원본 행 수 | ~541,000 transactions |
| Cleaned rows / 정제 후 행 수 | ~530,000 |
| Columns / 컬럼 | InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country |
| Countries / 국가 수 | 38 |
| Revenue basis / 매출 기준 | Gross (Quantity × UnitPrice); cancellation invoices excluded / 취소 인보이스 제외 |

**Data quality issues handled / 처리한 데이터 품질 문제:**
- Cancellations (`C`-prefix `InvoiceNo`) → removed via `Quantity <= 0` filter / 취소 행 제거
- Accounting adjustments (`A`-prefix `InvoiceNo`) → removed explicitly / 회계 분개 행 명시적 제거
- Zero / negative `UnitPrice` → removed / 0 이하 단가 제거
- Non-standard country names: `EIRE → Ireland`, `RSA → South Africa` / 비표준 국가명 정규화
- Non-country values: `Unspecified`, `European Community` → removed / 비국가 값 제거
- ~24.9% of rows have no `CustomerID` — confirmed as guest purchases, retained for Q1–Q4, excluded for Q5 / CustomerID 없는 행은 게스트 구매로 확인. Q1~Q4는 포함, Q5는 제외

> **Note:** The dataset is UK-biased. Findings reflect the behaviour of a UK-centric retailer and should not be generalised to global markets.
> **주의:** 데이터셋이 UK 중심으로 편향되어 있다. 분석 결과를 글로벌 시장에 그대로 적용하는 것은 적절하지 않다.

---

## Project Structure / 프로젝트 구조

```
Cornerstone_Data_Pipeline/
│
├── README.md
├── main.py                         # Pipeline entry point / 파이프라인 진입점 (CLI)
├── requirements.txt
│
├── data/
│   └── online_retail.xlsx          # Raw dataset — not tracked in git / 원본 데이터 (git 미추적)
│
├── outputs/                        # Generated charts and CSVs / 생성된 차트 및 요약 CSV
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
├── pipeline/                       # Core pipeline package / 핵심 파이프라인 패키지
│   ├── load.py                     # I/O only — load .xlsx or .csv / 데이터 로드 전용
│   ├── clean.py                    # All cleaning rules with WHY comments / 정제 규칙 (WHY 주석 포함)
│   ├── analyze.py                  # Pure functions — no printing, no plotting / 순수 함수
│   └── visualize.py                # Returns Figure objects — no plt.show() / Figure 객체 반환
│
├── notebooks/
│   └── business_eda.ipynb          # Question-driven EDA notebook / 질문 중심 EDA 노트북
│
├── tests/
│   ├── test_load.py
│   └── test_clean.py
│
└── .github/workflows/ci.yml        # GitHub Actions: install + pytest on push/PR
```

---

## Pipeline Architecture / 파이프라인 구조

```
load_raw()        load.py       Read .xlsx / .csv → raw DataFrame
                                .xlsx 또는 .csv 로드 → 원본 DataFrame
    ↓
clean()           clean.py      Apply 6 global cleaning rules → cleaned DataFrame
                                6개 전역 정제 규칙 적용 → 정제된 DataFrame
get_customer_df()               Q5-only subset (CustomerID NaN removed)
                                Q5 전용 서브셋 (CustomerID NaN 제거)
    ↓
analyze_*()       analyze.py    One function per business question → DataFrame or dict
                                비즈니스 질문당 함수 하나 → DataFrame 또는 dict 반환
    ↓
plot_*()          visualize.py  One function per chart → matplotlib Figure
                                차트당 함수 하나 → matplotlib Figure 반환
    ↓
main.py                         Save 13 PNGs + 5 CSVs to outputs/
                                13개 PNG + 5개 CSV를 outputs/ 에 저장
```

**Design principles / 설계 원칙:**
- `analyze.py` functions are side-effect-free — no printing, no plotting, independently unit-testable
  `analyze.py` 함수는 부작용 없음 — 출력·시각화 없이 독립적으로 단위 테스트 가능
- `visualize.py` functions return `Figure` objects and never call `plt.show()` — the caller controls rendering
  `visualize.py` 함수는 `Figure` 객체를 반환하며 `plt.show()`를 호출하지 않음 — 렌더링은 호출자가 결정
- Each cleaning rule in `clean.py` has a `WHY:` comment explaining the business reason
  `clean.py` 의 각 정제 규칙에는 비즈니스 이유를 설명하는 `WHY:` 주석이 있음

---

## Installation / 설치

```bash
cd Projects/Cornerstone_Data_Pipeline

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Place the raw dataset at `data/online_retail.xlsx`.
원본 데이터를 `data/online_retail.xlsx` 위치에 넣는다.

---

## Usage / 실행

**Run the full pipeline / 전체 파이프라인 실행:**

```bash
MPLBACKEND=Agg python main.py
```

**Custom paths / 경로 직접 지정:**

```bash
MPLBACKEND=Agg python main.py --data data/online_retail.xlsx --output outputs/
```

All 13 charts and 5 summary CSVs are saved to `outputs/`.
13개 차트와 5개 요약 CSV가 `outputs/` 에 저장된다.

**Run tests / 테스트 실행:**

```bash
pytest
```

---

## Outputs / 출력 파일

| File / 파일 | Description / 설명 |
|------------|-------------------|
| `q1_uk_vs_others.png` | Donut chart: UK (84.6%) vs Other Countries / UK vs 기타 국가 도넛 차트 |
| `q1_country_revenue.png` | Bar chart: all non-UK countries by revenue / 비-UK 전체 국가 매출 막대그래프 |
| `q1_country_revenue.csv` | Revenue and share % for all non-UK countries / 국가별 매출 및 비중 |
| `q2_monthly_revenue.png` | Line chart: monthly revenue Dec 2010 – Dec 2011 / 월별 매출 라인 차트 |
| `q2_monthly_revenue_bar.png` | Bar chart: same data, easier per-month comparison / 월별 매출 막대 차트 |
| `q2_monthly_revenue.csv` | Monthly revenue table / 월별 매출 테이블 |
| `q3_pareto.png` | Pareto chart: top 20% products → 78.7% of revenue / 파레토 차트 |
| `q3_top_products.png` | Top 20 products by revenue with frequency rank / 매출 Top 20 상품 |
| `q3_top_products.csv` | Top 20 products table / 상위 상품 테이블 |
| `q3_product_segments.png` | 4-quadrant scatter: revenue vs frequency per product / 상품 4분면 산점도 |
| `q4_order_value_histogram.png` | Order value distribution (capped at p99 = £4,806) / 주문 금액 히스토그램 |
| `q4_order_value_boxplot.png` | Box plot: order value spread / 주문 금액 박스플롯 |
| `q4_large_order_impact.csv` | Revenue share from orders above £500 / £1K / £5K / £10K / 대형 주문 영향 |
| `q5_top_customers.png` | Top 20 customers by revenue with order count / 매출 Top 20 고객 |
| `q5_top_customers.csv` | Top 20 customers table / 상위 고객 테이블 |
| `q5_customer_segments.png` | 4-quadrant scatter: VIP / Big Spender / Loyal / Casual / 고객 4분면 산점도 |
| `q5_customer_revenue_hist.png` | Customer revenue distribution (capped at p99) / 고객 매출 분포 히스토그램 |
| `q5_vip_seasonal.png` | VIP vs Non-VIP monthly revenue normalised 0–100 / VIP vs 일반 계절성 비교 |

---

## Key Cross-Question Insights / 교차 인사이트

**1. The November spike is driven by VIP customers / 11월 피크는 VIP가 만든다**
Overall revenue peaks in November (Q2). VIP customers peak even more sharply in November (Q5).
VIP bulk pre-purchasing is the primary driver of the seasonal spike.
전체 매출은 11월에 피크(Q2). VIP 고객은 11월 피크가 더욱 두드러짐(Q5).
VIP의 대량 사전 구매가 계절성 급등의 주요 원인이다.

**2. Concentration risk repeats at every level / 집중 리스크가 모든 레벨에서 반복된다**
- Q1: 1 country (UK) = 84.6% of revenue / 1개국 = 매출의 84.6%
- Q3: Top 20% of products = 78.7% of revenue / 상위 20% 상품 = 매출의 78.7%
- Q5: Top 20% of customers = 74.6% of revenue / 상위 20% 고객 = 매출의 74.6%

The business is structurally dependent on a small group at every dimension.
비즈니스가 모든 차원에서 소수에게 구조적으로 의존하고 있다.

**3. Large orders (Q4) and B2B customers (Q5) are the same phenomenon / 대형 주문과 B2B 고객은 같은 현상의 양면이다**
Top 0.9% of orders (above £5,000) drive 18.6% of revenue.
These map directly to the High Rev / Low Freq "Big Spender" segment — likely B2B buyers purchasing premium niche products in bulk.
상위 0.9% 주문(£5,000 초과)이 매출의 18.6%를 담당한다.
이들은 Q5의 고매출·저빈도 "Big Spender" 세그먼트와 동일 — B2B 구매자가 프리미엄 상품을 대량 구매하는 패턴이다.

---

## Tech Stack / 기술 스택

- Python 3.12
- pandas, openpyxl
- matplotlib, seaborn
- pytest
- GitHub Actions (CI)
