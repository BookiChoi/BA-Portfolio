"""Data loading — SQLite I/O only.
데이터 로딩 — SQLite I/O 전용.

Responsible for ONE thing: reading raw tables from SQLite into DataFrames.
한 가지 역할만 담당: SQLite에서 원본 테이블을 DataFrame으로 읽어오기.

Never cleans, transforms, analyzes, or visualizes data.
데이터 정제, 변환, 분석, 시각화는 절대 하지 않는다.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# The only tables that exist in airbnb_nyc.sqlite (see notebooks/airbnb_business_eda.ipynb
# Section 2). Guards against typos and SQL-injection-by-table-name.
# airbnb_nyc.sqlite에 존재하는 유일한 테이블들 (노트북 2번 섹션 참조).
# 오타 및 테이블명을 통한 SQL 인젝션을 방지한다.
VALID_TABLES: frozenset[str] = frozenset({"listings", "calendar", "reviews"})


def load_raw(path: str | Path, table: str) -> pd.DataFrame:
    """Load a table from a SQLite database into a DataFrame.
    SQLite 파일 경로와 테이블명을 받아 해당 테이블을 DataFrame으로 반환.

    Performs no cleaning — returns the table exactly as stored.
    정제 없이 테이블을 그대로 반환한다.

    Args:
        path: SQLite database file path (e.g. ``data/airbnb_nyc.sqlite``).
              SQLite 데이터베이스 파일 경로.
        table: Table name to read (``listings``, ``calendar``, or ``reviews``).
               읽을 테이블명.

    Returns:
        Raw DataFrame for the requested table.
        요청한 테이블의 원본 DataFrame.

    Raises:
        FileNotFoundError: If no file exists at the given path.
                           지정한 경로에 파일이 없을 경우.
        ValueError: If ``table`` is not one of the known tables.
                    알려진 테이블명이 아닐 경우.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Database file not found: {path}")

    if table not in VALID_TABLES:
        raise ValueError(
            f"Unknown table '{table}'. Expected one of: {sorted(VALID_TABLES)}"
        )

    logger.info("Loading table '%s' from %s", table, path)
    with sqlite3.connect(path) as conn:
        # Table name is validated against VALID_TABLES above, so it is safe to
        # interpolate directly — sqlite3 does not support parameterised table names.
        # 테이블명은 위에서 VALID_TABLES로 검증되어 안전하다 — sqlite3는
        # 테이블명에 파라미터 바인딩을 지원하지 않는다.
        df = pd.read_sql(f"SELECT * FROM {table}", conn)  # noqa: S608

    logger.info("Loaded %d rows x %d columns from '%s'", *df.shape, table)
    return df


def get_connection(path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection for direct SQL queries in analyze.py.
    analyze.py에서 직접 SQL 쿼리를 실행할 SQLite connection을 연다.

    Used for the SQL-backed business questions (JOIN, CTE, window functions)
    that are more naturally expressed as raw SQL than as ``load_raw`` calls.
    JOIN/CTE/윈도우 함수처럼 raw SQL로 표현하는 것이 더 자연스러운
    비즈니스 질문 분석에 사용된다.

    Args:
        path: SQLite database file path.
              SQLite 데이터베이스 파일 경로.

    Returns:
        An open ``sqlite3.Connection``. Caller is responsible for closing it
        (a ``with`` block is recommended).
        열린 ``sqlite3.Connection``. 호출자가 닫을 책임이 있다 (``with`` 사용 권장).

    Raises:
        FileNotFoundError: If no file exists at the given path.
                           지정한 경로에 파일이 없을 경우.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Database file not found: {path}")
    return sqlite3.connect(path)
