"""Entry point for the Airbnb NYC Business Analytics pipeline.
Airbnb NYC 비즈니스 분석 파이프라인 진입점.

Full pipeline:

    Load → Clean → Analyze → Visualize → Save

Run from the project directory:

    python main.py

This file contains no business logic — it only orchestrates
the building blocks in ``pipeline/``.
이 파일에는 비즈니스 로직이 없다.
``pipeline/`` 패키지의 빌딩 블록을 연결(orchestrate)하는 역할만 한다.
"""

from pipeline import analyze, clean, load, visualize


def main():
    # TODO: Run load → clean → analyze (4 questions) → visualize (4 charts).
    # TODO: load → clean → analyze(4개 질문) → visualize(4개 차트) 순서로 실행.
    pass


if __name__ == "__main__":
    main()
