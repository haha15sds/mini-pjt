"""FastAPI 서버: POST /query (과제 규약).

실행: uvicorn api:app --app-dir src --port 8000
요청 본문 {"question"} 만으로 동작하고, 승인 흐름에는 thread_id·decision 을 함께 보낸다.
scenario_id 는 가상 테넌트에 주입할 장애 시나리오(S00~S08, 시연·평가용 선택 필드)다.
uvicorn 접근 로그에는 본문이 남지 않으며, 이 모듈도 질문 원문을 로그로 쓰지 않는다(D-6).
"""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agent import handle_query

app = FastAPI(title="Gemini Enterprise 설정 지원 에이전트", version="1.0")


class QueryRequest(BaseModel):
    question: str = ""
    thread_id: Optional[str] = None
    decision: Optional[Literal["approve", "reject"]] = None
    scenario_id: Optional[str] = None


@app.exception_handler(RequestValidationError)
async def _validation(_: Request, exc: RequestValidationError):
    # 규약 3필드를 유지한다 (AC-7). 입력값 원문은 응답에 넣지 않는다.
    fields = sorted({".".join(str(x) for x in e["loc"][1:]) for e in exc.errors()})
    msg = f"요청 형식 오류: {', '.join(fields) or '본문'}"
    return JSONResponse(status_code=200, content={"answer": msg, "contexts": [], "trace": [{"step": "validate", "input": "", "output": msg}]})


@app.post("/query")
def query(req: QueryRequest) -> dict:
    return handle_query(req.question, thread_id=req.thread_id, decision=req.decision, scenario_id=req.scenario_id)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
