"""Data loading utilities.
데이터 로딩 유틸리티.

Responsible for ONE thing: reading raw data from disk into a DataFrame.
한 가지 역할만 담당: 원본 데이터를 디스크에서 DataFrame으로 읽어오기.

Never cleans, transforms, analyzes, or visualizes data.
데이터 정제, 변환, 분석, 시각화는 절대 하지 않는다.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def load_raw(path: str | Path) -> pd.DataFrame:
    """Load the Online Retail dataset from an Excel file.
    Online Retail 데이터셋을 Excel 파일에서 로드한다.

    Supports .xlsx / .xls (openpyxl) and .csv files.
    .xlsx / .xls (openpyxl) 및 .csv 파일을 지원한다.

    Performs no cleaning — returns the file exactly as stored.
    정제 없이 파일 그대로 반환한다.

    Args:
        path: Path to the data file. / 데이터 파일 경로.

    Returns:
        Raw DataFrame, unmodified. / 수정되지 않은 원본 DataFrame.

    Raises:
        FileNotFoundError: If no file exists at the given path.
                           지정한 경로에 파일이 없을 경우.
        ValueError: If the file extension is not supported.
                    지원하지 않는 파일 확장자일 경우.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    suffix = path.suffix.lower()
    logger.info("Loading raw data from %s", path)

    if suffix in {".xlsx", ".xls"}:
        # CustomerID는 원본에서 float으로 저장되어 있으므로 Float64(nullable)로 명시
        df = pd.read_excel(path, dtype={"CustomerID": "Float64"})
    elif suffix == ".csv":
        df = pd.read_csv(path, dtype={"CustomerID": "Float64"})
    else:
        raise ValueError(f"Unsupported file type '{suffix}'. Use .xlsx, .xls, or .csv.")

    logger.info("Loaded %d rows × %d columns", *df.shape)
    return df
