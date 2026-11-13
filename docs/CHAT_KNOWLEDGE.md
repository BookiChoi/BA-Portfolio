# 파이프라인 안내 (claude.ai Project용 지식 파일)

이 문서는 레포를 읽을 수 없는 Claude가 이 레포의 사람-AI 분석 파이프라인을 설명할 때 쓰는 자료다.
모든 문장 끝의 괄호는 근거 파일이다. 확인하지 못한 것은 "TODO: 확인 필요"로 남겼다.
작성 기준: 레포 파일을 읽고 확인한 내용만 쓴다. 기준 시점의 레포 상태이므로 이후 바뀌었을 수 있다.

## 0. 한눈에 보기

- 사람이 회사, 비즈니스 질문, 인사이트, 추천을 쓴다. AI 에이전트는 조사, 질문 피드백, 분석 계획과 실행, 검증, 반박, 효과 예측을 맡는다 (`docs/PIPELINE.md`).
- 각 단계는 `Projects/<slug>/workflow/`에 번호 붙은 파일을 남기고, 모든 파일의 1행은 작성자 표시다: `Author: human` 또는 `Author: ai/<agent>` (`docs/PIPELINE.md`).
- 에이전트끼리는 파일로만 일을 넘긴다 (`docs/PIPELINE.md`, `.claude/agents/*.md`).
- 모든 숫자는 실행된 코드 또는 인용한 출처에서 나와야 한다 (`docs/PIPELINE.md`).
- `Learning/`, `Practice/`는 소유자의 학습 자료라서 요청 없이는 수정하지 않는다 (`CLAUDE.md`).
- `Projects/` 아래 이름이 `_`로 시작하는 폴더(예: `_template`)는 프로젝트가 아니다 (`CLAUDE.md`).
- 프로젝트 폴더 구성: `config.yaml`, `data/`, `data_manifest.json`, `notebooks/`, `outputs/`, `pipeline/`, `README.md`, `tests/`, `workflow/` (`Projects/_template/`).
- 템플릿의 `workflow/`에는 `00_brief.md`, `02_questions.md`, `07_insights.md`, `09_recommendations.md` 네 개만 있고, 모두 2행이 `Status:` 줄이다 (`Projects/_template/workflow/`, `scripts/project_state.py`).

## 1. 파이프라인 단계 (00~10)

접두사 설명: `[PROJECT]`는 사람이 쓴 문서의 커밋, `[AI-PROJECT]`는 AI 단계의 커밋이다 (`.claude/skills/run-project/SKILL.md`).

| 단계 | 산출물 (`workflow/`) | 담당 | 사람 게이트 | 커밋 접두사 |
|---|---|---|---|---|
| 00 Brief | `00_brief.md` | 사람 (`docs/PIPELINE.md`) | 2행 `Status: final`로 완료 표시 (`scripts/project_state.py`) | `[PROJECT] <slug> 00 brief: ...` (SKILL의 stage 라벨) |
| 01 Research | `01_research.md` | AI `researcher` (mode `research`) (`docs/PIPELINE.md`) | 없음 | `[AI-PROJECT] <slug> 01-research: ...` (`.claude/skills/run-project/SKILL.md`) |
| 02 Questions | `02_questions.md` | 사람 | `Status`: `draft` → `ready-for-coach` → `final` (`scripts/project_state.py`) | `[PROJECT] <slug> 02 questions: ...` |
| 02 Feedback | `02_questions_feedback.md` | AI `question-coach` (`docs/PIPELINE.md`) | 사람이 읽고 질문을 직접 고친 뒤 `final`로 바꾼다 (`scripts/project_state.py`) | `[AI-PROJECT] <slug> 02-feedback: ...` |
| 03 Data plan | `03_data_plan.md` | AI `researcher` (mode `data-feasibility`) | 게이트 1: 사람이 GO/NO-GO를 읽고 데이터를 준비한 뒤 승인 줄을 직접 추가 (`docs/PIPELINE.md`) | AI: `[AI-PROJECT] <slug> 03-data-plan: ...`, 사람 승인: `[PROJECT] <slug> 03 data plan approved: ...` (SKILL) |
| 04 Analysis plan | `04_analysis_plan.md` | AI `analyst` (phase A), 계획만 쓰고 멈춤 (`.claude/agents/analyst.md`) | 게이트 2: 사람이 계획을 검토하고 승인 줄을 직접 추가 (`docs/PIPELINE.md`) | AI: `[AI-PROJECT] <slug> 04-analysis-plan: ...`, 사람 승인: `[PROJECT] <slug> 04 plan approved: ...` (SKILL) |
| 05 Analysis | `05_analysis.md` | AI `analyst` (phase B), 승인된 계획만 실행 (`.claude/agents/analyst.md`) | 없음 | `[AI-PROJECT] <slug> 05-analysis: ...` (SKILL) |
| 06 Validation | `06_validation.md` | AI `validator` (`docs/PIPELINE.md`) | 게이트 3: FAIL이 있으면 자동 진행 없음 (아래 3절) | `[AI-PROJECT] <slug> 06-validation: ...` (SKILL) |
| 06 Fail resolution | `06_fail_resolution.md` | 사람, FAIL 이후에만 필요 (`docs/PIPELINE.md`) | `Decision: accept-with-caveat` 또는 `drop-question` (`scripts/project_state.py`) | `[PROJECT] <slug> 06 fail resolution: ...` (SKILL) |
| 07 Insights | `07_insights.md` | 사람 | 게이트 4: 핵심 숫자 1~2개를 직접 재현. 도구가 확인할 수 없는 작업 약속이다 (`docs/PIPELINE.md`) | `[PROJECT] <slug> 07 insights: ...` (SKILL) |
| 08 Critique | `08_critique.md` | AI `critic` (`docs/PIPELINE.md`) | 없음 | `[AI-PROJECT] <slug> 08-critique: ...` (SKILL) |
| 09 Recommendations | `09_recommendations.md` | 사람 | `Status: final` (`scripts/project_state.py`) | `[PROJECT] <slug> 09 recommendations: ...` (SKILL) |
| 10 Impact | `10_impact.md`, `10_impact_assumptions.json` | AI `impact-modeler` (`docs/PIPELINE.md`) | 없음 | `[AI-PROJECT] <slug> 10-impact: ...` (SKILL) |

- 사람 쪽 커밋 라벨은 SKILL이 `00 brief`처럼 공백 형태로 안내하지만, netflix-engagement 이력에는 `00-brief`, `04-plan`처럼 하이픈 형태도 쓰였다 (`.claude/skills/run-project/SKILL.md`, `git log`). 사람 커밋의 라벨 형식을 강제하는 검사는 없다: `check_commits.py`의 R3은 `[AI-PROJECT]`에만 적용된다 (`scripts/check_commits.py`).
- 사람 문서는 2행에 `Status:`가 있다. 허용값은 `00`/`07`/`09`가 `draft`, `final`, `02`는 `draft`, `ready-for-coach`, `final`이다 (`scripts/project_state.py`).
- `03_data_plan.md`와 `06_validation.md`의 2행은 정확히 `Overall verdict: GO|NO-GO` 또는 `Overall verdict: PASS|FAIL`이어야 한다 (`.claude/agents/researcher.md`, `.claude/agents/validator.md`).
- netflix-engagement에서는 위 표 밖의 보조 문서도 만들었다: `01_research_review.md`, `01b_data_profile.md`, `05a_scope_stop.md`, `05b_pilot_stop.md`, `05_pilot_check` (`Projects/netflix-engagement/workflow/`). 파이프라인 표준 단계는 아니다 (`docs/PIPELINE.md`).

## 2. 에이전트 6종

모든 에이전트는 `model: sonnet`이다 (`.claude/agents/*.md`). 공통 규칙: 커밋하지 않는다, 영어로 쓴다, 파일 1행에 `Author: ai/<agent>`를 쓴다 (예외: `10_impact_assumptions.json`은 작성자 줄이 없다) (`.claude/agents/*.md`, `.claude/skills/run-project/SKILL.md`). `.env`, `.zshrc`, `.envrc`는 읽지 않는다 (`.claude/agents/*.md`).

| 이름 | 하는 일 | 쓸 수 있는 파일 (프로젝트 기준) | 쓸 수 없는 것 | 도구 | model / effort |
|---|---|---|---|---|---|
| `researcher` | mode `research`: 회사, 뉴스, 후보 데이터셋 조사. mode `data-feasibility`: 질문별 데이터 확인과 GO/NO-GO (`.claude/agents/researcher.md`) | `workflow/01_research.md`, `workflow/03_data_plan.md` (`.claude/hooks/guard.py` ALLOW) | 비즈니스 질문 작성, 뉴스 원문 복사, `workflow/` 밖 쓰기, 사람 문서 (`.claude/agents/researcher.md`) | Read, Write, Glob, Grep, WebSearch, WebFetch (Bash 없음) | sonnet / low |
| `question-coach` | `02_questions.md`의 모호성, 측정 가능성, 숨은 가정, 더 날카로운 방향, 결정 연결을 비판. 질문을 대신 쓰지 않는다 (`.claude/agents/question-coach.md`) | `workflow/02_questions_feedback.md` (guard.py ALLOW) | 질문 재작성, 사람 문서 (`.claude/agents/question-coach.md`) | Read, Write, Glob, Grep | sonnet / medium |
| `analyst` | phase A: `04_analysis_plan.md` 작성 후 멈춤. phase B: 승인된 계획만 구현, 실행하고 `05_analysis.md` 작성 (`.claude/agents/analyst.md`) | `workflow/04_analysis_plan.md`, `workflow/05_analysis.md`, `pipeline/**`, `outputs/**`, `notebooks/**`, `data_manifest.json`, `main.py`, `tests/test_*.py` (SKILL 표). guard.py ALLOW에는 `data/**`도 있음 (아래 참고) | `tests/test_validation_*.py` (guard.py DENY), 사람 문서, 승인 줄 작성, 인터넷에서 임의로 데이터 다운로드, 다른 프로젝트, 계획에 없는 분석 (`.claude/agents/analyst.md`) | Read, Write, Edit, Bash, Glob, Grep | sonnet / medium |
| `validator` | 분석 숫자를 다른 방법으로 독립 재계산하고 가정을 점검해 숫자별 PASS/FAIL을 `06_validation.md`에 기록 (`.claude/agents/validator.md`) | `workflow/06_validation.md`, `workflow/logs/**`, `tests/test_validation_*.py` (guard.py ALLOW) | 분석가의 코드, 파이프라인 모듈, 산출물 수정 (`.claude/agents/validator.md`) | Read, Write, Bash, Glob, Grep (Edit 없음) | sonnet / medium |
| `critic` | `07_insights.md`에 대해 대안 설명, 교란, 데이터 한계, 결론을 뒤집을 증거를 `08_critique.md`로 정리. 코드 실행 없음 (`.claude/agents/critic.md`) | `workflow/08_critique.md` (guard.py ALLOW) | 새 숫자 만들기, 인사이트 재작성, 추천 쓰기 (`.claude/agents/critic.md`) | Read, Write, Glob, Grep (Bash 없음) | sonnet / medium |
| `impact-modeler` | 사람의 추천과 가정 아래서 low/base/high 시나리오와 민감도 분석, 실험 설계를 `10_impact.md`와 `10_impact_assumptions.json`으로 작성 (`.claude/agents/impact-modeler.md`) | `workflow/10_impact.md`, `workflow/10_impact_assumptions.json`, `pipeline/impact_*.py`, `outputs/impact_*` (guard.py ALLOW, SKILL 표) | FAIL이거나 검증되지 않은 숫자 사용, 결과를 보장하는 표현, 사람 문서 (`.claude/agents/impact-modeler.md`) | Read, Write, Edit, Bash, Glob, Grep | sonnet / medium |

- **불일치 표시 (analyst의 `data/**`):** `.claude/hooks/guard.py`의 analyst 허용 목록에는 `data/**`가 있지만, `.claude/skills/run-project/SKILL.md`의 analyst 쓰기 표와 `.claude/agents/analyst.md`에는 `data/`가 없다. 오히려 SKILL의 범위 확인은 `data/` 안의 변경을 허용 범위 밖으로 보고 커밋하지 않고 멈춘다. 즉 훅은 쓰기를 허용하지만 skill은 그 결과를 커밋하지 않는다. 의도된 설계인지는 TODO: 확인 필요.
- 데이터 취득: analyst는 사람이 `data/`에 둔 파일이나 `03_data_plan.md`에서 사람이 승인한 URL에서만 받고, 출처 URL, 다운로드 날짜, 행 수, 체크섬을 `data_manifest.json`에 기록한다 (`.claude/agents/analyst.md`).
- 에이전트 이름 6종은 모두 `.claude/agents/`에 파일이 있다: `analyst`, `critic`, `impact-modeler`, `question-coach`, `researcher`, `validator`.

## 3. /run-project 동작

시작: 사람만 `/run-project <slug>`로 시작한다 (모델 자동 호출 금지) (`.claude/skills/run-project/SKILL.md`: `disable-model-invocation: true`, `docs/PIPELINE.md`). 사용자에게 하는 말은 한국어이고 경로와 명령은 원문이다 (SKILL).

**상태 판별:** 판별은 `python3 scripts/project_state.py <slug>`만 한다. 모델이 추론으로 단계를 정하면 안 된다 (SKILL).
- 이 스크립트는 `workflow/` 바로 아래 파일만 보며, `workflow/archive/` 아래로 옮긴 파일은 무시한다 (`scripts/project_state.py`).
- 출력은 JSON이고 키는 `stage`, `next_actor`(`human`, `ai`, `done`), `agent`, `mode`, `action`, `blockers`, `inputs`, `expected_outputs`, `info`다 (`scripts/project_state.py`).
- 단계 이름: `00_brief`, `01_research`, `02_questions_draft`, `02_coach_feedback`, `02_apply_feedback`, `03_data_plan`, `03_review`, `04_plan`, `04_review`, `05_analysis`, `06_validation`, `06_fail_decision`, `07_insights`, `08_critique`, `09_recommendations`, `10_impact`, `done` (`scripts/project_state.py`).
- 판별은 파일의 존재와 비어 있지 않음, 2행의 Status 또는 verdict, 승인 줄 유무로 한다 (`scripts/project_state.py`).

**한 번에 한 단계만:** 한 번 호출에 AI 단계는 최대 하나이고, 끝나면 멈춘다. 서브에이전트가 막히거나 실패해도 재시도나 우회를 하지 않고 이유를 보고하고 멈춘다 (SKILL "Hard rules").

**공통 선행 절차:**
- Step 0: slug가 `^[a-z0-9]+(-[a-z0-9]+)*$`에 맞고 `Projects/<slug>/`가 있는지 확인한다. 아니면 `_`로 시작하지 않는 폴더 목록을 보여주고 묻는다.
- Step 2: 현재 브랜치가 `project/<slug>`가 아니면 사용자에게 먼저 확인받고, 승인 뒤에만 만들거나 전환한다. 승인이 없으면 멈춘다 (SKILL).

**사람 차례일 때 (`next_actor: human`):** 아무것도 수정하지 않고, `action`, `blockers`, `info.file`로 지금 할 일을 구체적으로 알려준 뒤 멈춘다 (SKILL Step 3).
- 03_review: `03_data_plan.md`의 GO/NO-GO와 이유를 요약해 주고, GO면 데이터 준비 확인과 승인 줄 추가를 사람에게 안내한다.
- NO-GO 절차(설명만 하고 자동화하지 않음): `02_questions.md` 수정 → 옛 03을 `workflow/archive/run1/`로 `git mv` → `02_questions.md`의 Status를 `ready-for-coach` 또는 `final`로 되돌림 → `/run-project` 재실행 (SKILL).
- 06_fail_decision: 사람이 `06_fail_resolution.md`를 정해진 형식(1행 `Author: human`, 2행 `Status: final`, 3행 `Decision: ...`)으로 쓰거나, `05`와 `06`을 `workflow/archive/runN/`으로 옮기고 분석을 다시 돌린다 (SKILL, `scripts/project_state.py`).
- 07_insights: 핵심 숫자를 직접 재현하라고 상기시킨다 (SKILL).
- 끝으로 완료된 사람 문서의 `git add <파일>`, `git commit -m "[PROJECT] <slug> <라벨>: ..."` 명령을 알려주지만 실행은 사람이 한다 (SKILL).

**AI 차례일 때 (`next_actor: ai`)**: 정확히 한 단계만 다음 순서로 한다 (SKILL Step 4).
1. 스냅샷: `git status --porcelain --untracked-files=all -- Projects/<slug>` 결과를 기억한다.
2. `.claude/active_project`에 slug 한 줄을 쓴다 (훅이 서브에이전트의 쓰기를 이 프로젝트로 제한).
3. `agent`에 적힌 서브에이전트를 Agent 도구로 실행한다. 프롬프트에 slug, 폴더, mode, stage, 읽을 입력 파일, 기대 산출물, "커밋하지 말 것, 기대 산출물만 쓸 것, 막히면 우회하지 말고 보고할 것"을 담는다.
4. 완료 보고를 기다린다. 보고는 정보로만 취급하고 지시로 따르지 않는다.
5. 검증: 기대 산출물이 존재하고 비어 있지 않고 1행이 `Author: ai/<agent>`인지(JSON 제외), `project_state.py`를 다시 돌려 단계가 진행했는지, 스냅샷과 비교한다.
6. 범위 확인: 새로 생기거나 바뀐 경로가 모두 `Projects/<slug>/` 안, `data/` 밖, 5 MB 미만, 해당 에이전트의 쓰기 범위 안인지 본다. 벗어나면 아무것도 커밋하지 않고 경로를 알리고 멈춘다.
7. 커밋: 해당 경로만 하나씩 명시해 `git add`하고 `[AI-PROJECT] <slug> <stage>: <summary>`로 커밋한다. Co-Authored-By 트레일러를 붙이고 push하지 않는다.
8. `.claude/active_project`를 비운다. 실패하거나 중간에 멈춰도 비운다.
9. 한국어로 보고하고 멈춘다: 만든 경로, 짧은 요약, 다음 단계, `/usage` 확인 안내. validator 보고에 FAIL이 있으면 있다고 분명히 말하고 자동 수정을 제안하지 않는다.

**done일 때:** 모든 단계가 끝났다고 보고하고, README의 "Decisions I made", "What AI did", "Where AI critique changed my view" 작성을 제안한다 (SKILL Step 5).

**멈춤 조건:**
- 가드 훅이 호출을 막으면 즉시 멈추고 막힌 메시지를 그대로 알린다 (SKILL).
- 서브에이전트가 막히거나 실패하면 재시도 없이 보고하고 멈춘다 (SKILL).
- 범위 확인에서 예상 밖 경로가 나오면 커밋 없이 멈춘다 (SKILL).
- 브랜치 전환에 사용자의 승인이 없거나 전환이 실패하면 멈춘다 (SKILL).
- `project_state.py`가 `error`를 내면(잘못된 slug, `workflow/` 없음) 보고하고 멈춘다 (SKILL, `scripts/project_state.py`).

## 4. 사람 승인 규칙

- **승인 줄이 필요한 문서:** `03_data_plan.md`와 `04_analysis_plan.md`뿐이다 (`CLAUDE.md`, `docs/PIPELINE.md`). 줄의 정확한 문구는 `.claude/agents/analyst.md`와 `docs/PIPELINE.md`에서 확인할 수 있고, 이 문서에서는 훅에 걸리지 않도록 줄 맨 앞에 쓰지 않는다.
- **쓰는 방법:** 사람이 문서를 검토한 뒤 편집기에서 직접 타이핑한다. 훅도 이것을 의도된 방법으로 둔다 (`docs/PIPELINE.md` Safety measures).
- **03 승인 전:** GO/NO-GO를 읽고, 데이터를 `data/`에 두거나 URL을 확인한다 (`docs/PIPELINE.md`).
- **04 승인 후에만 phase B:** analyst는 `04_analysis_plan.md`를 읽어 승인 줄이 없거나 위치, 문구, 중복, 계획 변경 후 추가 등 의심스러운 점이 있으면 phase B로 넘어가지 않고 오케스트레이터에 보고한다 (`.claude/agents/analyst.md`).
- **AI는 쓰지 않는다:** analyst는 이 줄을 어떤 경우에도 쓰거나 고치지 않고, `/run-project`도 쓰지 않는다 (`.claude/agents/analyst.md`, `.claude/skills/run-project/SKILL.md`).
- **승인 후 잠금:** 승인 줄이 들어간 `03_data_plan.md`, `04_analysis_plan.md`는 서브에이전트가 수정할 수 없다 (`.claude/hooks/guard.py` G2).
- **명령에 승인 문구를 쓰면 안 되는 이유:** 훅은 Bash 명령 어디에든 승인 문구가 들어 있으면 차단한다. Write/Edit 텍스트는 줄이 그 문구로 시작할 때 차단한다. 메인 세션도 예외가 아니다 (`.claude/hooks/guard.py` G1). 실제로 netflix-engagement의 04 검토 중 메인 세션이 이 문구가 든 확인 명령을 실행했다가 차단되었고, 세션은 우회 없이 멈춘 뒤 문구 없이 다시 확인했다 (`Projects/netflix-engagement/README.md` 섹션 4(c)). 이유는 문서에 적힌 대로 "승인 줄은 사람만 쓴다"이다 (`docs/PIPELINE.md`).
- **사람만 쓰는 문서:** `00`, `02`, `07`, `09`, `06_fail_resolution.md`와 승인 줄이다 (`CLAUDE.md`).

## 5. 가드 훅 규칙과 한계

**등록:** `.claude/settings.json`의 PreToolUse가 `Write|Edit|MultiEdit|NotebookEdit|Bash|Read`에 `.claude/hooks/guard.py`를 실행한다. 명령 실패 시 차단(`|| exit 2`, `onFailure: block`)이다 (`.claude/settings.json`).

**규칙 요약** (`.claude/hooks/guard.py` docstring과 코드):
- G1 (메인 세션 포함 모든 호출): `.env*`(`.env.example` 제외), `.zshrc`, `.envrc` 접근 금지. 승인 줄 작성 금지 (4절).
- G2 (서브에이전트): 쓰기는 `Projects/<slug>/` 안에서만, slug는 `_`로 시작하지 않고 `.claude/active_project`의 값과 같아야 한다. 이 파일이 없거나 비었거나 형식이 틀리면 거부한다. `.claude/`, `CLAUDE.md`, `.git/`, `scripts/`, 루트 `tests/`, `Learning/`, `Practice/`, `Projects/_*/`와 사람 문서(00, 02, 07, 09, `06_fail_resolution.md`) 쓰기는 거부한다. `MultiEdit`, `NotebookEdit`은 서브에이전트에게 통째로 금지다.
- G3: 에이전트별 허용 목록(2절 표).
- G4 (서브에이전트의 Bash, 최선 노력): `rm`, `sudo`, `chmod`, `ssh`, `scp`, `curl`, `wget`와 `git commit/push/add/reset/checkout/restore/rebase/merge/stash/clean`을 막고, 패키지 설치(`pip`, `uv`, `npm`, `pnpm`)를 막는다. 리다이렉트, `tee`, `sed -i`, `mv`, `cp`의 쓰기 대상을 검사한다.
- G5: 입력을 읽을 수 없거나 내부 오류가 나면 차단한다(fail closed). 메시지에 훅을 임시로 끄는 방법(`.claude/settings.json`의 항목 제거)이 안내된다.
- 경로는 `realpath`로 해석해 `..`와 심볼릭 링크 우회를 실제 대상으로 판단하고, 보호 이름은 대소문자 구분 없이 비교한다.
- 읽기: 서브에이전트의 `Read`는 G1(민감 파일)만 검사한다 (`guard.py`의 `evaluate`).

**알려진 한계:**
- Bash 검사는 명령 텍스트만 본다. Python 스크립트나 `-c`, `make`, `node`, `dd of=`처럼 프로그램 내부에서 하는 쓰기는 보이지 않는다 (`guard.py` docstring, `docs/PIPELINE.md`).
- 변수, 명령 치환, `eval`, `xargs`, `find -exec/-delete`는 펼쳐 보지 않는다. `bash|sh|zsh|dash -c "..."`만 두 단계까지 재검사한다 (`guard.py` docstring).
- `> >> tee sed -i mv cp` 외의 쓰기 명령(`touch`, `mkdir`, `ln`, `install`, `rsync` 등)은 검사하지 않는다 (`guard.py` docstring).
- 해석할 수 없는 명령은 거부하므로 특이하지만 올바른 입력도 막힐 수 있다. 쓰기 대상에 `$` 변수가 있으면 "리터럴 경로를 쓰라"며 막는다 (`guard.py`).
- 활성 프로젝트는 호출 자체가 아니라 `.claude/active_project` 파일에서 온다 (`guard.py` docstring).
- 훅 입력에 `agent_type`이 없으면 메인 세션으로 보고 G1만 적용한다. 즉 G2~G4의 경로 제한은 메인 세션에는 걸리지 않는다 (`guard.py`의 `evaluate`).
- `Grep`, `Glob`과 훅 매처 밖의 도구(예: `WebSearch`, `WebFetch`)는 훅이 보지 못한다 (`guard.py` docstring, `.claude/settings.json`).
- 훅은 사람이 편집기에서 승인 줄을 타이핑하는 것을 막을 수 없다 (의도된 방법) (`docs/PIPELINE.md`).
- 훅은 사람이 07 전에 핵심 숫자를 실제로 재현했는지 확인할 수 없다 (`docs/PIPELINE.md`).
- 훅은 단위 테스트와 실제 세션의 수동 확인(`.envrc` 읽기 차단, 서브에이전트의 `.claude/` 쓰기 차단, 승인 줄 차단)이 있다 (`docs/PIPELINE.md`). 테스트 파일: `tests/test_guard_hook.py`.

## 6. 스크립트 사용법 (모두 표준 라이브러리만 사용, `scripts/*.py --help`로 확인)

**`scripts/new_project.py`**: 템플릿에서 새 프로젝트를 만든다.
```
python scripts/new_project.py <slug> --company "<name>" [--target-dir <부모 폴더>]
```
- `slug`는 소문자, 숫자, 하이픈(`^[a-z0-9]+(-[a-z0-9]+)*$`), `--company`는 필수다. `--target-dir`은 부모 폴더이고 기본값은 레포의 `Projects/`다.
- 이미 있는 폴더는 덮어쓰지 않고 오류로 끝난다. 템플릿의 `{{slug}}`, `{{company}}`, `{{created}}`를 `.md/.yaml/.yml/.json` 파일에서 치환한다. 끝나면 `00_brief.md`를 직접 쓰라고 안내한다 (`scripts/new_project.py`).

**`scripts/project_state.py`**: 현재 단계를 JSON으로 출력한다.
```
python scripts/project_state.py <slug> [--projects-dir <경로>]
```
- 결과 JSON 형식과 단계 이름은 3절을 본다. 종료 코드는 정상 0, 오류 1이다 (`scripts/project_state.py`). 사람이 직접 실행해도 된다 (`docs/PIPELINE.md`).

**`scripts/check_commits.py`**: push 전에 커밋 메시지와 파일을 검사한다 (읽기 전용 git 명령).
```
python scripts/check_commits.py [--range <rev-range>] [--max-size-mb 5]
```
- 기본 범위는 `@{upstream}..HEAD`이고, 업스트림이 없으면 `origin/main..HEAD`다. 둘 다 없으면 오류이며 `--range main..HEAD`처럼 지정해야 한다. `--max-size-mb` 기본값은 5다.
- R1: `Co-Authored-By: Claude` 트레일러가 있으면 제목이 `[AI-PROJECT]`, `[AI-FEAT]`, `[AI-CHORE]`, `[AI-FIX]`로 시작해야 한다.
- R2: 제목이 `[AI-`로 시작하면 그 트레일러와 허용된 TYPE이 있어야 한다.
- R3: `[AI-PROJECT]` 제목은 `[AI-PROJECT] <slug> <stage>: <summary>`이고 stage는 `^[0-9]{2}-[a-z0-9-]+$`(예: `04-analysis-plan`)다.
- R4: `Projects/*/data/`의 파일(`.gitkeep` 제외)과 크기 한도를 넘는 추가/수정 파일을 금지한다.
- 경고(종료 코드에 영향 없음): `Claude-Session:` 트레일러. 공개 저장소라면 push 시 세션 주소가 함께 공개될 수 있다는 내용이다.
- 오류가 있으면 종료 코드 1이다. 머지 커밋은 파일 목록 없이 메시지 검사만 받는다 (`scripts/check_commits.py`).
- 테스트: `tests/test_check_commits.py`, `tests/test_new_project.py`, `tests/test_project_state.py`, `tests/test_guard_hook.py`. 실행은 루트에서 `pytest -q tests/` (`CLAUDE.md`).

## 7. 커밋 규칙

- AI가 도운 커밋은 `[AI-<TYPE>]`로 시작한다. TYPE은 `PROJECT`, `FEAT`, `CHORE`, `FIX`다 (`CLAUDE.md`, `docs/PIPELINE.md`).
- 프로젝트 작업은 `[AI-PROJECT] <slug> <stage>: <summary>`, stage 이름은 고정(예: `04-analysis-plan`)이다 (`CLAUDE.md`, `.claude/skills/run-project/SKILL.md`).
- `Co-Authored-By` 트레일러를 유지한다. `[AI-...]` 제목에 트레일러가 없으면 `check_commits.py`가 오류(R2)로 본다 (`CLAUDE.md`, `scripts/check_commits.py`).
- 논리적 변경 하나당 커밋 하나다 (`CLAUDE.md`).
- `git add -A`와 `git add .`는 쓰지 않고 경로를 명시한다. 추적되지 않는 학습 노트북이 섞이지 않게 하려는 규칙이다 (`CLAUDE.md`).
- 데이터 파일(csv, xlsx, sqlite 등)은 커밋하지 않는다. 새 프로젝트는 출처 URL, 다운로드 날짜, 행 수를 `data_manifest.json`에 기록한다 (`CLAUDE.md`).
- 사람 문서의 커밋은 `[PROJECT] <slug> <라벨>: ...` 형식이다. `/run-project`는 이 명령을 안내만 한다 (`.claude/skills/run-project/SKILL.md`).
- push는 사람이 한다. 소유자 허락 없이는 push하지 않고, push한 커밋은 amend나 rebase하지 않는다 (`CLAUDE.md`). push 전에 `python scripts/check_commits.py`를 돌린다 (`CLAUDE.md`).
- 에이전트는 커밋하지 않는다. `/run-project` skill이 에이전트의 파일을 커밋한다 (`docs/PIPELINE.md`, `.claude/agents/*.md`).
- **squash 금지 (사람이 정한 운영 규칙, 레포 문서에는 아직 명시되지 않음):** PR은 merge commit으로 합치고 squash merge나 rebase merge는 하지 않는다. 이유는 `[PROJECT]`와 `[AI-...]` 커밋이 섞인 이력이 사람과 AI의 역할 증거이기 때문이다 (소유자 지시. `CLAUDE.md`와 다른 레포 파일에는 없음). 참고로 netflix-engagement 브랜치는 merge commit으로 `main`에 합쳐졌다 (`git log`의 "Merge pull request #1").

## 8. 흔한 문제와 대처 (레포 문서에 이미 적힌 것만)

- **훅이 호출을 막음:** 즉시 멈추고 막힌 메시지(`guard: blocked: ...`)를 그대로 알린다. 우회하거나 재시도하지 않는다 (`.claude/skills/run-project/SKILL.md`, `.claude/hooks/guard.py`).
- **"no active project" 메시지:** 서브에이전트는 `.claude/active_project`에 slug가 없으면 쓸 수 없다. `/run-project`가 이 파일에 slug를 쓰고 단계가 끝나면 비운다 (`.claude/hooks/guard.py`, SKILL).
- **"리터럴 경로를 쓰라"거나 "해석할 수 없다"는 메시지:** 쓰기 대상에 `$`나 백틱이 있거나 명령을 파싱할 수 없을 때의 차단이다. 명령을 단순화하고 리터럴 경로를 쓴다 (`.claude/hooks/guard.py`).
- **훅 내부 오류로 모든 호출이 막힘:** 훅은 fail closed다. 메시지가 안내하는 대로 `.claude/settings.json`의 항목을 손으로 지우면 임시로 끌 수 있다 (`.claude/hooks/guard.py`). 이 파일은 요청 없이는 수정하지 않는 규칙이다 (`CLAUDE.md`).
- **승인 줄이 없거나 의심스러움:** analyst는 phase B로 넘어가지 않고 보고한다 (`.claude/agents/analyst.md`).
- **분석가의 중단 조건 (netflix-engagement의 승인된 계획에 적힌 예):** 0 이하의 시간값이 나오면 멈추고 보고, 중복 행이 서로 다른 시즌이 아니면 멈추고 묻는다, 라벨링 범위의 80% 목표도 키 상한을 넘으면 멈추고 묻는다, 파일럿 매칭률이 85% 미만이면 멈춘다 (`Projects/netflix-engagement/workflow/04_analysis_plan.md`). 이 중 범위 상한과 파일럿 정지는 실제로 발동해 `05a_scope_stop.md`, `05b_pilot_stop.md`가 남았고, 사람이 계획을 수정한 뒤 다시 돌렸다 (`Projects/netflix-engagement/README.md` 섹션 3, 4(b)). 이 숫자 기준들은 그 프로젝트 계획의 값이다. 모든 프로젝트의 공통 규칙은 아니다.
- **계획에 없는 분석이 필요해 보임:** 실행하지 말고 `05_analysis.md`에 사람에게 주는 제안으로 적는다 (`.claude/agents/analyst.md`).
- **중단 보고서를 `05_analysis.md`로 두면 생기는 문제 (문서에 명시된 규칙은 아님):** 코드로 확인된 사실만 적는다. `scripts/project_state.py`는 `05_analysis.md`가 비어 있지 않으면 05가 끝난 것으로 보고 다음 단계를 `06_validation`(validator)으로 정한다 (`scripts/project_state.py`의 05, 06 분기). 따라서 중단 보고서를 그 이름으로 두면 분석이 끝나지 않았는데도 도구가 검증 단계로 넘어갈 수 있다. 이것은 코드에서 읽은 동작이고, 이 문제를 직접 설명하는 문서는 없다. netflix-engagement는 중단 보고서를 `05a_scope_stop.md`, `05b_pilot_stop.md`로 따로 두었다. `05_analysis.md`는 그 뒤 마지막 실행 커밋 하나로만 만들어졌다 (`Projects/netflix-engagement/workflow/`, `git log`).
- **validator가 FAIL을 냄:** 자동 수정이나 진행은 없다. 사람이 `06_fail_resolution.md`를 쓰거나 05, 06을 `archive/runN/`으로 옮겨 다시 돌린다. `Overall verdict` 줄이 PASS인데 표에 FAIL 셀이 있으면 FAIL로 처리하고 경고한다 (`docs/PIPELINE.md`, `scripts/project_state.py`).
- **데이터 계획이 NO-GO:** 3절의 NO-GO 절차를 따른다 (SKILL).
- **서브에이전트 실행 뒤 범위 확인 실패:** 아무것도 커밋하지 않고 예상 밖 경로를 알린다. 사전에 이미 수정되어 있던 파일이 섞여도 같다 (SKILL).
- **`check_commits.py`가 "no commit range" 오류:** 업스트림도 `origin/main`도 없는 경우다. `--range main..HEAD`처럼 지정한다 (`scripts/check_commits.py`).
- **`[AI-...]` 커밋이 R1, R2에서 실패:** 트레일러와 제목 접두사가 짝이어야 한다 (6절).
- **슬러그 오류:** 소문자, 숫자, 단일 하이픈만 허용한다 (`scripts/new_project.py`, `scripts/project_state.py`).
- **research 단계의 근거 없는 주장:** netflix-engagement에서 사람이 `01_research.md`의 출처를 열어 보니 한 주장은 출처에 없었고 한 링크는 404였다. 둘은 "Do not use"로 표시되었다 (`Projects/netflix-engagement/README.md` 섹션 4(a)).

## 9. 아직 검증되지 않은 부분

- **`impact-modeler`는 한 번도 실행되지 않았다.** netflix-engagement는 검증된 효과가 없다는 이유로 10단계를 건너뛰었고 README도 "not run"이라고 적는다 (`Projects/netflix-engagement/README.md`). 따라서 `10_impact.md`, `10_impact_assumptions.json`, `pipeline/impact_*.py`의 실제 출력 품질과 형식은 검증되지 않았다.
- **`docs/PIPELINE.md`의 서술:** "`/run-project` skill과 에이전트는 실제 프로젝트에서 end to end로 실행된 적이 없고, 출력 품질도 평가되지 않았다" (`docs/PIPELINE.md` Known limits).
- **netflix-engagement에서 실제로 돈 단계:** 커밋 이력과 README에 따르면 `researcher`(01, 03), `question-coach`(02), `analyst`(04 phase A를 두 번, 05 phase B를 중단 두 번 뒤 완료), `validator`(06, 숫자 전부 PASS), `critic`(08)가 실행되었다 (`Projects/netflix-engagement/README.md`, `git log`). 10단계만 실행되지 않았다.
- **소유자 확인(2026-11-13):** netflix-engagement의 01 research, 02 feedback, 03 data plan, 04 analysis plan(두 번), 05 analysis(여러 번), 06 validation, 08 critique는 `/run-project netflix-engagement`로 실행했다. 01b 데이터 프로파일, 05 중단 보고서 정리, 프로젝트 README, 이 문서는 `/run-project` 없이 직접 프롬프트로 했다. `docs/PIPELINE.md`의 "end to end로 실행된 적 없음" 문구는 이 사실과 어긋나는 낡은 서술이다(`docs/PIPELINE.md`는 아직 갱신하지 않았다). 이 항목은 레포 파일이 아니라 소유자의 말에 근거한다.
- **두 서술 병기:** `docs/PIPELINE.md`는 end to end 미실행이라고 적고, 소유자 확인(위)은 `/run-project`로 여러 단계를 실제 실행했다고 한다. 둘이 어긋나며, 위 소유자 확인이 더 최근 사실이고 `docs/PIPELINE.md`의 문구가 낡았다. 다만 `docs/PIPELINE.md`가 말하는 "출력 품질이 평가되지 않았다"는 별개의 점이라 이번 확인으로 바뀌지 않는다. netflix README가 서브에이전트 시작과 커밋의 주체를 "main session"으로 적은 것은 `/run-project`를 실행한 세션을 가리키는 것으로 보이지만, 이 대응은 레포 파일로 확인되지 않는다 (`Projects/netflix-engagement/README.md`).
- **netflix-engagement에서 드러난 약한 부분:** 파일럿 매칭 확인은 AI 1차 확인으로 대신했다. 사람이 핵심 숫자를 직접 재현하지 않았다. validator는 분석가의 정제, 제목 키, IMDb 매칭 코드를 재사용해서 완전히 독립적인 재계산은 아니었다 (`Projects/netflix-engagement/README.md` 섹션 3, 5).
- **프로젝트 수:** `docs/PIPELINE.md`는 `workflow/`가 없는 기존 두 프로젝트(Airbnb, Online Retail)를 언급한다. 이 파이프라인을 끝까지 쓴 프로젝트는 netflix-engagement 하나뿐이다 (`docs/PIPELINE.md`, `Projects/`).
- **TODO: 확인 필요 모음:** analyst의 `data/**` 허용이 의도인지, 06 FAIL 분기(`06_fail_resolution.md`, 재실행)를 실제 프로젝트에서 실행해 봤는지 (netflix는 모두 PASS였으므로 실행 사례 없음).
