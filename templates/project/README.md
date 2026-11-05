# {{company}}: <project title>

<!-- 한국어 힌트: 제목을 프로젝트에 맞게 바꾼다. slug는 `{{slug}}`, 생성일은 {{created}}. -->

## Summary

- **Company:** {{company}}
- **Business question (one line):** <!-- 한국어 힌트: 02_questions.md의 핵심 질문을 한 줄로 요약한다. -->
- **Key finding (one line):** <!-- 한국어 힌트: 07_insights.md를 쓴 뒤 채운다. 숫자는 05/06 문서에 있는 것만 쓴다. -->

## How to reproduce

<!-- 한국어 힌트: 처음 보는 사람이 그대로 따라 할 수 있게 쓴다. 데이터 출처는 data_manifest.json 참고. -->

1. Set up the environment from the repo root (Python 3.12, `pip install -r requirements.txt`).
2. Place the data in `data/` (see `data_manifest.json` for source, download date, row count and checksum).
3. From this folder, run: `MPLBACKEND=Agg python main.py`
4. Run tests: `pytest -q`

## Who did what

| Stage | Owner (human/AI) | File |
|---|---|---|
| Brief | human | `workflow/00_brief.md` |
| Research | AI (researcher) | `workflow/01_research.md` |
| Business questions | human | `workflow/02_questions.md` |
| Question feedback | AI (question-coach) | `workflow/02_questions_feedback.md` |
| Data feasibility (GO/NO-GO) | AI (researcher) | `workflow/03_data_plan.md` |
| Analysis plan | AI (analyst) | `workflow/04_analysis_plan.md` |
| Plan approval (`Approved: human` line) | human | `workflow/04_analysis_plan.md` |
| Analysis execution | AI (analyst) | `workflow/05_analysis.md` |
| Validation (PASS/FAIL) | AI (validator) | `workflow/06_validation.md` |
| Insights | human | `workflow/07_insights.md` |
| Critique | AI (critic) | `workflow/08_critique.md` |
| Recommendations | human | `workflow/09_recommendations.md` |
| Impact forecast | AI (impact-modeler) | `workflow/10_impact.md` |

<!-- 한국어 힌트: 실제로 다르게 진행했다면 표를 현실에 맞게 고친다. -->

## Decisions I made

<!-- 한국어 힌트: 내가 직접 내린 판단(회사 선정, 질문, 해석, 권고)과 그 이유를 적는다. -->

## What AI did

<!-- 한국어 힌트: AI가 맡은 일(조사, 계획, 실행, 검증, 반론, 효과 예측)을 구체적으로 적는다. -->

## Where AI critique changed my view

<!-- 한국어 힌트: 08_critique.md나 06_validation.md 때문에 생각이 바뀐 지점을 적는다. 없으면 없다고 쓴다. -->
