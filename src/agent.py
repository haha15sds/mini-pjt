"""[과제 규약 3-1] 메인 에이전트 그래프 — 진입 파일.

실제 코드는 도메인 폴더에 있다(배치 규칙은 CLAUDE.md). 이 파일은 규약의 `src/agent.py` 자리에서 그 위치를 알려 주고 다시 내보낸다.
- 그래프 조립 `build_graph`        : src/workflow/graph.py (input_guard → analyze → agent → plan_runbook → approval_gate → output_guard)
- 단일 진입점 `handle_query`       : src/workflow/entry.py
- 노드: 분석·ReAct·진단            : src/diagnosis/analyze.py · react.py · plan.py
- 노드: 승인 게이트(HITL)          : src/approval/gate.py
"""
from src.approval.gate import approval_gate  # noqa: F401
from src.diagnosis.analyze import analyze  # noqa: F401
from src.diagnosis.plan import plan_runbook  # noqa: F401
from src.diagnosis.react import agent  # noqa: F401
from src.workflow.entry import graph, handle_query, reset_checkpoints  # noqa: F401
from src.workflow.graph import build_graph  # noqa: F401
