# Airbnb NYC — Business Analytics
# 에어비앤비 NYC — 비즈니스 분석

An end-to-end data analysis project tracing a single business narrative through NYC's short-term rental market: **where the revenue is → whether that growth is real → who is regulatory risk → who to contact first**.
The project covers question-driven **Exploratory Data Analysis (EDA)** with SQL (JOIN, CTE, window functions) and a modular **Load → Clean → Analyze → Visualize** pipeline implemented in Python.
NYC 단기 임대 시장을 하나의 비즈니스 스토리로 추적하는 엔드-투-엔드 데이터 분석 프로젝트: **매출은 어디에 있는가 → 그 성장은 실재하는가 → 규제 리스크는 누구에게 있는가 → 누구부터 접촉해야 하는가**.
SQL(JOIN, CTE, 윈도우 함수) 기반의 질문 중심 **탐색적 데이터 분석(EDA)** 과 모듈형 **Load → Clean → Analyze → Visualize** 파이프라인을 Python으로 구현했다.

**Portfolio project by Booki Choi — August 2026**

---

## Business Questions / 비즈니스 질문

Four questions were defined before analysis began, each required to demonstrate a specific SQL technique, and chained into one narrative:
분석 전에 4개 질문을 먼저 정의했다. 각 질문은 특정 SQL 기법을 사용하도록 설계했고, 하나의 스토리로 이어지도록 구성했다.

**WHERE is the revenue → is the growth REAL → WHO carries the risk → WHO to contact first**
**매출은 어디에 있는가 → 그 성장은 진짜인가 → 리스크는 누가 지고 있는가 → 누구부터 접촉할 것인가**

| # | Question / 질문 | SQL Technique / SQL 기법 | Key Finding / 핵심 발견 |
|---|-----------------|------------------------|------------------------|
| Q1 | Where is NYC short-term rental revenue concentrated? / 매출은 어디에 집중되어 있는가? | JOIN + GROUP BY + aggregates | Top 4 borough x room-type segments = **84.2%** of $389M market revenue. Superhosts earn **2.8x–6.0x** more in every top segment (all p < 0.001) |
| Q2 | Is that growth real, and who leads it today? / 성장은 실재하며 지금은 누가 주도하는가? | JOIN + date function (`strftime`) + GROUP BY | Brooklyn led review growth pre-COVID (76.6%/yr vs Manhattan 71.9%/yr). Post-COVID, Manhattan's growth (17.1%/yr, significant) overtook Brooklyn's (5.2%/yr, **not** significant) |
| Q3 | How much of that revenue sits with unregistered hosts? / 그 매출 중 얼마가 미등록 호스트에게 있는가? | CTE filter + GROUP BY (distribution) | Only 18.3% of listings are registration-eligible (`minimum_nights < 30`). Among them, Manhattan holds **85.8%** of all unlicensed at-risk revenue. License status is **not independent** of borough (χ² p ≈ 0) |
| Q4 | Which hosts should compliance contact first? / 어떤 호스트부터 접촉해야 하는가? | `RANK()` + cumulative `SUM() OVER()` | Just **15 of 104** at-risk hosts hold 50% of the $7.0M at-risk revenue; **35 hosts** hold 80% (Gini = 0.62) |

---

## Dataset / 데이터셋

| Attribute / 항목 | Detail / 내용 |
|-----------------|--------------|
| Source / 출처 | [Inside Airbnb — New York City](http://insideairbnb.com/get-the-data/) |
| Format / 형식 | SQLite (`airbnb_nyc.sqlite`), 3 tables |
| `listings` | 30,259 rows x 90 columns — one row per listing |
| `calendar` | Daily availability per listing (forward-looking booking window) |
| `reviews` | One row per review, 2010–2026 (used as a demand proxy over time) |
| Revenue basis / 매출 기준 | Airbnb's own `estimated_revenue_l365d` (trailing 365 days) |

**Data quality issues handled / 처리한 데이터 품질 문제:**
- `estimated_revenue_l365d` is NULL for 30.9% of listings (Airbnb couldn't compute it) → excluded from revenue analysis / 매출 계산 불가 매물 30.9%는 매출 분석에서 제외
- `estimated_revenue_l365d == 0` for ~55% of the remainder → kept as a real "inactive" signal, not treated as missing / 매출 0은 결측이 아니라 "비활성" 신호로 유지
- `calendar.date` is a **forward-looking** booking window, not a historical occupancy log → used only as a secondary signal, weakly correlated (r≈-0.11) with Airbnb's own backward-looking `estimated_occupancy_l365d` / `calendar.date`는 미래 예약 구간이라 보조 지표로만 사용
- `license` has 3 real states (NULL / `'Exempt'` / a real registration number) → always modeled as a 3-way `license_status`, never collapsed to 2 / `license`는 3가지 실제 상태를 가지므로 항상 3단계로 다룸
- 2020 is a genuine COVID-19 demand shock, and the most recent year is a **partial year** → both flagged in growth-rate calculations rather than silently averaged in / 2020년 코로나 충격과 최신 부분 연도는 성장률 계산에서 항상 표시

> **Note:** All cleaning decisions are validated with real numbers in `notebooks/airbnb_business_eda.ipynb` (Section 8) before being implemented in `pipeline/`.
> **참고:** 모든 전처리 결정은 `notebooks/airbnb_business_eda.ipynb`(8번 섹션)에서 실제 수치로 검증한 뒤 `pipeline/`에 구현했다.

---

## Project Structure / 프로젝트 구조

```
airbnb-nyc-business-analytics/
│
├── README.md
├── main.py                              # Pipeline entry point / 파이프라인 진입점 (CLI)
│
├── data/
│   └── airbnb_nyc.sqlite                # Raw dataset — not tracked in git / 원본 데이터 (git 미추적)
│
├── outputs/                             # Generated charts and CSVs / 생성된 차트 및 요약 CSV
│   ├── q1_segment_revenue.png / .csv
│   ├── q1_superhost_effect.png / .csv
│   ├── q2_borough_review_trend.png / .csv
│   ├── q2_growth_rate_comparison.png
│   ├── q2_growth_rates.csv
│   ├── q3_license_status_share.png
│   ├── q3_unlicensed_by_borough.png / .csv
│   ├── q3_license_risk_distribution.csv
│   ├── q4_pareto_curve.png
│   └── q4_top_priority_hosts.png / (q4_host_priority_ranking.csv)
│
├── pipeline/                            # Core pipeline package / 핵심 파이프라인 패키지
│   ├── constants.py                     # Shared thresholds / 공유 상수
│   ├── load.py                          # SQLite I/O only / SQLite 로드 전용
│   ├── clean.py                         # license_status / is_active / eligibility filters
│   ├── analyze.py                       # SQL-backed Q1-Q4 + statistical tests
│   └── visualize.py                     # Returns Figure objects — no plt.show()
│
├── notebooks/
│   └── airbnb_business_eda.ipynb        # Question-driven EDA notebook (bilingual EN/KR)
│
└── tests/
    ├── test_load.py                     # load_raw / get_connection
    ├── test_clean.py                    # license_status / is_active / eligibility
    ├── test_analyze.py                  # gini, growth rates, crossover, chi-square, risk summary
    └── test_cross_validation.py         # pandas (clean.py) vs SQL (analyze.py) rule agreement, on real DB
```

> `.gitignore` is managed at the **BA-Portfolio repo root** (monorepo).
> `.gitignore`는 **BA-Portfolio 레포 루트**에서 관리한다 (모노레포).

---

## Pipeline Architecture / 파이프라인 구조

```
load_raw() / get_connection()   load.py       Read SQLite table / open a connection for SQL queries
                                               SQLite 테이블 로드 / SQL 쿼리용 connection 열기
    ↓
clean()                         clean.py      Derive license_status + is_active
                                               license_status, is_active 파생
get_eligible_listings()                       Q3/Q4-only subset (minimum_nights < 30)
                                               Q3/Q4 전용 서브셋 (minimum_nights < 30)
drop_null_revenue()                           Revenue-based-analysis-only filter
                                               매출 기반 분석 전용 필터
    ↓
analyze_*() / check_*()         analyze.py    SQL (JOIN/CTE/window fn) + statistical tests
                                               → DataFrame or dict
                                               SQL(JOIN/CTE/윈도우함수) + 통계 검정
                                               → DataFrame 또는 dict 반환
    ↓
plot_*()                        visualize.py  One function per chart → matplotlib Figure
                                               차트당 함수 하나 → matplotlib Figure 반환
    ↓
main.py                                       Save 8 PNGs + 7 CSVs to outputs/
                                               8개 PNG + 7개 CSV를 outputs/ 에 저장
```

**Design principles / 설계 원칙:**
- `analyze.py`'s SQL-backed functions replicate the exact queries validated in the EDA notebook — no re-deriving logic differently in two places
  `analyze.py`의 SQL 기반 함수는 EDA 노트북에서 검증한 쿼리를 그대로 재사용한다 — 로직을 두 곳에서 다르게 재구현하지 않는다
- `visualize.py` functions return `Figure` objects and never call `plt.show()` — the caller controls rendering
  `visualize.py` 함수는 `Figure` 객체를 반환하며 `plt.show()`를 호출하지 않음 — 렌더링은 호출자가 결정
- Statistical-test functions are named `check_*` (not `test_*`) so they are never accidentally collected as pytest tests when imported into a test module
  통계 검정 함수는 `test_*`가 아니라 `check_*`로 명명해, 테스트 모듈에 import될 때 pytest가 실수로 테스트로 수집하지 않도록 한다
- Each cleaning rule in `clean.py` has a `WHY:` docstring explaining the business reason
  `clean.py` 의 각 정제 규칙에는 비즈니스 이유를 설명하는 `WHY:` 설명이 있음
- `license_status` / `is_active` / eligibility are intentionally implemented twice — once in pandas (`clean.py`, tested/reusable) and once in raw SQL (`analyze.py`, to demonstrate `CASE WHEN` / CTE filtering). `test_cross_validation.py` proves both agree on the real database, turning the duplication into a checked invariant instead of a silent risk.
  `license_status` / `is_active` / 등록 대상 여부는 의도적으로 두 번 구현되어 있다 — pandas(`clean.py`, 테스트·재사용 가능)와 순수 SQL(`analyze.py`, `CASE WHEN`/CTE 필터링 시연용). `test_cross_validation.py`가 실제 DB에서 둘의 결과가 일치함을 검증해, 중복을 방치된 위험이 아니라 확인된 불변조건으로 만든다

---

## Installation / 설치

```bash
cd Projects/airbnb-nyc-business-analytics

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install pandas numpy matplotlib seaborn scipy pytest
```

Place the raw dataset at `data/airbnb_nyc.sqlite`.
원본 데이터를 `data/airbnb_nyc.sqlite` 위치에 넣는다.

---

## Usage / 실행

**Run the full pipeline / 전체 파이프라인 실행:**

```bash
MPLBACKEND=Agg python main.py
```

**Custom paths / 경로 직접 지정:**

```bash
MPLBACKEND=Agg python main.py --data data/airbnb_nyc.sqlite --output outputs/
```

All 8 charts and 7 summary CSVs are saved to `outputs/`.
8개 차트와 7개 요약 CSV가 `outputs/` 에 저장된다.

**Run tests / 테스트 실행:**

```bash
pytest tests/ -v
```

27 tests cover `load.py` (SQLite I/O, invalid table/missing file), `clean.py` (license_status,
is_active, eligibility filtering), the pure-pandas functions in `analyze.py` (Gini
coefficient, growth-rate regression, crossover detection, chi-square independence), and
`test_cross_validation.py` (4 tests that run `clean.py`'s pandas rules and `analyze.py`'s SQL
side by side against the real database and assert they produce identical counts — skipped
automatically if `data/airbnb_nyc.sqlite` is absent). The SQL-backed Q1-Q4 functions
themselves are exercised end-to-end by running `main.py` against the real database rather
than mocked in unit tests.
27개 테스트는 `load.py`(SQLite I/O, 잘못된 테이블/누락 파일), `clean.py`(license_status,
is_active, 등록 대상 필터링), `analyze.py`의 순수 pandas 함수(지니계수, 성장률 회귀,
크로스오버 탐지, 카이제곱 독립성 검정), 그리고 `test_cross_validation.py`(`clean.py`의
pandas 규칙과 `analyze.py`의 SQL을 실제 DB에 대해 나란히 실행해 결과가 동일한지 확인하는
4개 테스트 — `data/airbnb_nyc.sqlite`가 없으면 자동 스킵)를 검증한다. SQL 기반 Q1~Q4
함수 자체는 단위 테스트에서 mock으로 대체하는 대신, `main.py`를 실제 DB로 실행해
end-to-end로 검증한다.

---

## Outputs / 출력 파일

| File / 파일 | Description / 설명 |
|------------|-------------------|
| `q1_segment_revenue.png` / `.csv` | Revenue by borough x room-type segment, top 4 highlighted / 세그먼트별 매출, 상위 4개 강조 |
| `q1_superhost_effect.png` / `.csv` | Superhost vs regular-host average revenue in the top-4 segments / 상위 4개 세그먼트 슈퍼호스트 효과 |
| `q2_borough_review_trend.png` / `.csv` | Yearly review count by borough, with COVID-dip and partial-year flags / 자치구별 연도별 리뷰 추이 |
| `q2_growth_rate_comparison.png` / `q2_growth_rates.csv` | Pre- vs post-COVID annual growth rate, Manhattan vs Brooklyn / 코로나 전후 성장률 비교 |
| `q3_license_status_share.png` | License status share by borough (100% stacked bar) / 자치구별 라이선스 상태 비중 |
| `q3_unlicensed_by_borough.png` / `.csv` | Unlicensed listing count & revenue-at-risk by borough / 자치구별 미등록 매물·리스크 매출 |
| `q3_license_risk_distribution.csv` | Full borough x license_status distribution table / 전체 분포 테이블 |
| `q4_pareto_curve.png` | Host rank vs cumulative at-risk revenue share (Lorenz/Pareto curve) / 호스트 순위별 누적 매출 곡선 |
| `q4_top_priority_hosts.png` / `q4_host_priority_ranking.csv` | Top 15 hosts for compliance outreach, full ranked list / 우선 접촉 대상 호스트 |

---

## Key Cross-Question Insights / 교차 인사이트

**1. The market is concentrated at every level / 시장은 모든 레벨에서 집중되어 있다**
- Q1: 4 of 18 borough x room-type segments = 84.2% of revenue / 18개 세그먼트 중 4개가 매출의 84.2%
- Q4: 15 of 104 at-risk hosts = 50% of at-risk revenue / 104명 중 15명이 리스크 매출의 50%

**2. Growth leadership flipped after COVID / 코로나 이후 성장 주도권이 바뀌었다**
Brooklyn out-grew Manhattan pre-COVID (76.6%/yr vs 71.9%/yr), but post-COVID Manhattan's
growth (17.1%/yr, statistically significant) overtook Brooklyn's (5.2%/yr, not significant).
The borough driving Q1's largest revenue segment is now also the borough driving new demand.
코로나 이전엔 브루클린이 맨해튼보다 빠르게 성장했지만(76.6%/yr vs 71.9%/yr), 코로나 이후엔
맨해튼(17.1%/yr, 유의함)이 브루클린(5.2%/yr, 유의하지 않음)을 앞섰다. Q1에서 가장 큰 매출
세그먼트를 만든 자치구가 지금의 신규 수요도 주도하고 있다.

**3. Regulatory risk is concentrated exactly where the revenue is / 규제 리스크는 매출이 있는 곳에 그대로 집중되어 있다**
Manhattan — Q1's #1 revenue segment — also holds 85.8% of all unlicensed at-risk revenue
(Q3), and the borough x license_status association is highly significant (χ² p ≈ 0), not
random noise. The same 4-borough concentration pattern from Q1 repeats as a compliance
liability in Q3-Q4.
Q1에서 매출 1위였던 맨해튼이 Q3의 미등록 리스크 매출의 85.8%도 보유하고 있으며, 자치구 x
license_status 연관성은 매우 유의하다(χ² p≈0) — 우연이 아니다. Q1의 집중 패턴이 Q3~Q4에서는
컴플라이언스 부채로 그대로 반복된다.

---

## Tech Stack / 기술 스택

- Python 3.12
- pandas, sqlite3
- scipy.stats (Kruskal-Wallis, Mann-Whitney U, chi-square, linear regression)
- matplotlib, seaborn
- pytest
