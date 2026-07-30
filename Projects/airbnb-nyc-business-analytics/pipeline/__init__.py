"""Airbnb NYC Business Analytics pipeline package.
Airbnb NYC 비즈니스 분석 파이프라인 패키지.

Modular building blocks:
모듈형 빌딩 블록:

- ``load``: read SQLite tables into DataFrames.
  SQLite 테이블을 DataFrame으로 읽기.
- ``clean``: prepare and type-correct listing data.
  listings 데이터 전처리 및 타입 정리.
- ``analyze``: SQL-backed analytical queries (one function per business question).
  SQL 기반 분석 (비즈니스 질문당 함수 하나).
- ``visualize``: turn analytical results into charts.
  분석 결과를 차트로 변환.

Each module is intentionally kept independent so that it can be reused,
tested, and extended in isolation.
각 모듈은 재사용·테스트·확장이 가능하도록 독립적으로 유지한다.
"""
