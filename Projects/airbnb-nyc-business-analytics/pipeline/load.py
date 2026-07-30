"""Data loading — SQLite I/O only.
데이터 로딩 — SQLite I/O 전용.

Responsible for ONE thing: reading raw tables from SQLite into DataFrames.
한 가지 역할만 담당: SQLite에서 원본 테이블을 DataFrame으로 읽어오기.

Never cleans, transforms, analyzes, or visualizes data.
데이터 정제, 변환, 분석, 시각화는 절대 하지 않는다.
"""

from __future__ import annotations

import pandas as pd


def load_raw(path: str, table: str) -> pd.DataFrame:
    """Load a table from a SQLite database into a DataFrame.
    SQLite 파일 경로와 테이블명을 받아 해당 테이블을 DataFrame으로 반환.

    TODO: Implement SQLite read logic.
    TODO: SQLite 읽기 로직 구현.

    Args:
        path: SQLite database file path (e.g. ``data/airbnb_nyc.sqlite``).
              SQLite 데이터베이스 파일 경로.
        table: Table name to read (``listings``, ``calendar``, or ``reviews``).
               읽을 테이블명.

    Returns:
        Raw DataFrame for the requested table.
        요청한 테이블의 원본 DataFrame.
    """
    pass
