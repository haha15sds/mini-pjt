"""LangGraph 그래프 조립 (D-8).

input_guard → analyze(LCEL 구조화 출력) → agent(ReAct) → plan_runbook(Plan) → approval_gate(interrupt, HITL) → output_guard
입력에서 개인정보가 남아 차단되면 input_guard 에서 바로 output_guard 로 간다.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from src.approval.gate import approval_gate
from src.diagnosis.analyze import analyze
from src.diagnosis.plan import plan_runbook
from src.diagnosis.react import agent
from src.workflow.guards import input_guard, output_guard
from src.workflow.state import State


def build_graph(checkpointer):
    g = StateGraph(State)
    for name, fn in [("input_guard", input_guard), ("analyze", analyze), ("agent", agent),
                     ("plan_runbook", plan_runbook), ("approval_gate", approval_gate), ("output_guard", output_guard)]:
        g.add_node(name, fn)
    g.add_edge(START, "input_guard")
    g.add_conditional_edges("input_guard", lambda s: "output_guard" if s.get("blocked") else "analyze")
    g.add_edge("analyze", "agent")
    g.add_edge("agent", "plan_runbook")
    g.add_edge("plan_runbook", "approval_gate")
    g.add_edge("approval_gate", "output_guard")
    g.add_edge("output_guard", END)
    return g.compile(checkpointer=checkpointer)
