"""Data cleaning — listings preparation only.
데이터 정제 — listings 전처리 전용.

Each transformation must include a comment explaining WHY.
모든 변환에는 WHY 주석으로 이유를 설명해야 한다.
"""

from __future__ import annotations

import pandas as pd


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and type-correct the listings DataFrame.
    listings DataFrame을 정제하고 타입을 정리한다.

    TODO: Required cleaning steps:
    TODO: 정리 필요 항목:
        - Parse ``price``: remove ``$`` and ``,``, convert to float.
          ``price`` 파싱: ``$``·``,`` 제거 후 float 변환.
        - Derive ``has_license`` (bool) from ``license`` nullability.
          ``license`` 결측 여부를 ``has_license``(bool)로 변환.
        - Handle missing values and dtype consistency.
          결측치·타입 정리.

    Args:
        df: Raw listings DataFrame from ``load_raw``.
            ``load_raw`` 출력 listings DataFrame.

    Returns:
        Cleaned listings DataFrame ready for analysis.
        분석 준비가 완료된 listings DataFrame.
    """
    pass
