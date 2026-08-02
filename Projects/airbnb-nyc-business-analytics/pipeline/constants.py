"""Shared pipeline constants.
파이프라인 공유 상수.

Single source of truth for thresholds and fixed analysis parameters used across
``clean``, ``analyze``, and (if needed) ``visualize``.
``clean`` / ``analyze`` / (필요 시) ``visualize``에서 쓰는 임계값·고정 분석
파라미터의 단일 기준점이다.
"""

from __future__ import annotations

# NYC Local Law 18 only regulates stays under 30 nights — listings already set up
# as 30+ night rentals are exempt from short-term-rental registration entirely.
# NYC Local Law 18은 30박 미만 단기 임대만 규제 대상이다 — 이미 30박 이상으로
# 설정된 매물은 애초에 등록 의무 대상이 아니다.
REGISTRATION_MIN_NIGHTS_THRESHOLD = 30

# Top-4 revenue segments identified in Q1 (EDA Section 4-4) — reused by the
# superhost-effect check so it always compares apples to apples with the
# segmentation table, instead of re-deriving "top 4" independently.
# Q1(EDA 4-4번 섹션)에서 확인된 매출 상위 4개 세그먼트 — 슈퍼호스트 효과 검정에서
# 재사용해 세그멘테이션 테이블과 항상 동일한 기준으로 비교한다.
TOP_4_SEGMENTS: tuple[tuple[str, str], ...] = (
    ("Manhattan", "Entire home/apt"),
    ("Brooklyn", "Entire home/apt"),
    ("Brooklyn", "Private room"),
    ("Manhattan", "Private room"),
)

# COVID-19 hit NYC short-term rentals hard in 2020; growth rates are compared
# pre- vs post-pandemic rather than as one continuous trend line.
# 2020년 코로나19가 NYC 단기 임대 시장에 큰 타격을 줬다 — 성장률은 하나의 연속
# 추세가 아니라 팬데믹 전/후로 나눠 비교한다.
PRE_COVID_YEARS: tuple[int, int] = (2010, 2019)
POST_COVID_YEARS: tuple[int, int] = (2021, 2025)
COVID_YEAR = 2020
