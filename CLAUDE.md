# CLAUDE.md — 코드 폴더 구조와 파일 배치 규칙

이 저장소에서 코드를 고치거나 더할 때 지키는 규칙이다. 협업·기록 규칙은 [agents.md](agents.md)를 따른다.

## 1. 원칙

- **모든 소스 코드는 `src/` 아래에 둔다.** 루트에는 문서(README·SERVICE·CLAUDE·agents·planning·history), 설정(`.env.example`, `requirements.txt`, `.streamlit/`), 데이터(`data/`), 평가 입력·결과(`evaluation/`)만 둔다.
- **폴더는 기술 역할(utils, models)이 아니라 에이전트의 도메인(기능)으로 나눈다.** 한 도메인의 실행 로직·프롬프트·입출력 스키마는 그 도메인 폴더 안에 함께 둔다.
- **여러 도메인이 함께 쓰는 LLM 클라이언트 설정과 범용 유틸리티만 `src/utils/`에 둔다.** 특정 도메인 규칙이 들어간 코드는 utils에 넣지 않는다.
- **import는 저장소 루트 기준 절대 경로로 쓴다.** 예: `from src.workflow.entry import handle_query`, `from src import tenant`. 상대 import(`from .x import`)와 `sys.path`에 `src/`를 넣는 방식은 쓰지 않는다.
- **명령은 저장소 루트에서 실행한다.** 스크립트로 직접 실행하는 파일(`src/ui/app.py`, `src/evaluation/*.py`)은 맨 위에서 저장소 루트를 `sys.path`에 넣는다.

## 2. 폴더 구조와 역할

```
src/
├── agent.py · tools.py · retriever.py   과제 규약(3-1) 진입 파일: 코드 없이 도메인 폴더의 것을 다시 내보내기만 한다
├── utils/          공통: LLM 클라이언트(Bedrock 모델 ID·대체 프로필), 경로, 메시지 본문 꺼내기
├── guardrails/     가드레일 R1~R3: 개인정보·시크릿 마스킹, 인젝션 탐지, 비밀값 요청 거절
├── knowledge/      공식 문서 RAG: 문서 수집, 하이브리드 검색(Chroma+BM25+RRF), retrieve_docs 도구, contexts 항목 형식
├── tenant/         가상 테넌트: 상태 저장소·장애 주입·조치 적용, 코드 점검(checks), check_tenant_state·propose_fix 도구
├── diagnosis/      진단 에이전트: 입출력 스키마, 프롬프트, 문의 분석(LCEL), ReAct 에이전트, 진단 구조화·검증(Plan)
├── approval/       HITL 승인 게이트: interrupt, 승인했을 때만 조치 적용
├── workflow/       그래프 조립: State, 입구·출구 가드 노드, 답변 조립, build_graph, 단일 진입점 handle_query
├── api/            FastAPI 서버: POST /query
├── ui/             Streamlit 화면
└── evaluation/     평가 실행 코드(인-아웃 18건·RAGAS, LLM-as-Judge, 불일치·힌트 점검, 반복 실행 집계)
```

| 폴더 | 파일 | 담는 것 |
|---|---|---|
| `utils/` | `llm.py` · `paths.py` · `text.py` | Bedrock 클라이언트(`llm_main`·`llm_fast`와 global 대체), `ROOT`·`DATA_DIR`·`EVAL_DIR`, `text_of` |
| `guardrails/` | `policies.py` (`__init__`에서 공개) | `mask_pii`, `residual_pii`, `detect_injection`, `SECRET_REQUEST`, `REFUSE_SECRET` |
| `knowledge/` | `retriever.py` · `tools.py` · `collect_docs.py` | `HybridRetriever`·`warm_up`, `retrieve_docs`·`ctx_entry`·`DOC_DATE`, 문서 수집 스크립트 |
| `tenant/` | `store.py` · `checks.py` · `tools.py` (`__init__`에서 공개) | 기준 구성·시나리오·조치 목록 로드와 thread별 상태, `compute_checks`·`supported_faults`, 에이전트 도구 |
| `diagnosis/` | `schemas.py` · `prompts.py` · `analyze.py` · `react.py` · `plan.py` | `Analysis`·`Cause`·`Step`·`Diagnosis`, 세 프롬프트, 그래프 노드 `analyze`·`agent`·`plan_runbook`, 도구 목록 `TOOLS` |
| `approval/` | `gate.py` | 노드 `approval_gate` (그래프에서 유일한 interrupt) |
| `workflow/` | `state.py` · `guards.py` · `answer.py` · `graph.py` · `entry.py` | `State`·`trace_entry`·`CHECK`, `input_guard`·`output_guard`, `compose_answer`, `build_graph`, `handle_query`·체크포인트 |
| `api/` | `server.py` | FastAPI 앱 |
| `ui/` | `app.py` | Streamlit 화면 |
| `evaluation/` | `run_eval.py` 등 | 평가 실행 코드. **입력(`test_queries.csv`)과 결과(보고서·JSON)는 루트 `evaluation/`에 쓴다** |

- **규약 진입 파일**: `src/agent.py`(그래프·`handle_query`), `src/tools.py`(도구 3개), `src/retriever.py`(RAG)는 과제 산출물 규약이 요구하는 이름이다. 여기에 로직을 쓰지 않고 import 만 둔다. 내부 코드는 이 파일들을 import 하지 않는다(도메인 모듈을 직접 import).

## 3. 의존 방향

```
api, ui, evaluation  →  workflow  →  diagnosis, approval  →  knowledge, tenant  →  guardrails, utils
```

- 화살표 반대 방향 import는 하지 않는다. 예: `tenant`가 `diagnosis`를 부르면 안 된다.
- `workflow/state.py`(State·trace)는 노드를 가진 도메인(`diagnosis`, `approval`)이 함께 쓰는 예외다. `workflow/__init__.py`는 비워 두어 순환 import를 막는다.
- 바깥(화면·API·평가)은 에이전트를 **`src.workflow.entry.handle_query` 하나로만** 부른다(D-7). 그래프를 직접 부르지 않는다.
- 상태를 바꾸는 함수(`tenant.apply_fix`)는 `approval/gate.py`만 부른다. 에이전트 도구 목록(`diagnosis/react.py`의 `TOOLS`)에는 읽기·제안 도구만 넣는다(D-3·D-8).

## 4. 새 코드를 넣을 때

| 넣을 것 | 위치 |
|---|---|
| 새 에이전트 도구 | 그 도구가 다루는 도메인 폴더의 `tools.py`, 그리고 `diagnosis/react.py`의 `TOOLS`에 등록 |
| 새 프롬프트 | 그 프롬프트를 쓰는 도메인의 `prompts.py` |
| 새 구조화 출력·입출력 타입 | 그 도메인의 `schemas.py` |
| 새 그래프 노드 | 노드가 속한 도메인 폴더, 연결은 `workflow/graph.py` |
| 새 장애·조치·시나리오 | 코드가 아니라 `data/*.json`. 판정 규칙은 `tenant/checks.py` |
| 새 커넥터(예: Confluence) | 새 도메인 폴더(`src/confluence/`)에 상태·점검·도구를 모은다 |
| 여러 도메인이 쓰는 LLM 설정·범용 함수 | `utils/` (도메인 규칙이 들어가면 해당 도메인으로) |

- 원래 과제 TODO 주석은 지우지 않고, 추가 구현은 `[추가 구현]` 표시로 구분한다.
- 파일을 옮기면 README의 "핵심 코드 위치"와 실행 명령, 이 파일의 표를 함께 고친다.
