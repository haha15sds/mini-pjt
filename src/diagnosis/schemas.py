"""진단 도메인 입출력 스키마 (패턴 1, 구조화 출력): 문의 분석 결과와 진단 결과."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Analysis(BaseModel):
    intent: Literal["sharepoint_issue", "other_connector", "general_question", "out_of_scope", "secret_request"] = Field(
        description="sharepoint_issue=SharePoint 커넥터 연동 장애, other_connector=다른 커넥터, general_question=일반 질문, "
        "out_of_scope=가격·견적 등 범위 밖, secret_request=비밀값을 알려 달라는 요청")
    symptoms: list[str] = Field(description="관찰된 증상 (짧은 한국어 구절)")
    ko_query: str = Field(description="문서 검색용 한국어 검색어")
    en_query: str = Field(description="문서 검색용 영어 검색어 (Entra, WIF, SharePoint 공식 용어 사용)")


class Cause(BaseModel):
    fault_id: Literal["F1", "F2", "F3", "F4", "F5", "F6", "none"]
    reason: str
    confidence: float = Field(ge=0, le=1)
    evidence_doc_ids: list[str] = Field(description="근거가 된 문서 청크 ID (검색 결과에 있는 것만)")


class Step(BaseModel):
    action: str
    risk: Literal["low", "med", "high"]
    source: str = Field(description="근거 문서 청크 ID 또는 fix_id")


class Diagnosis(BaseModel):
    causes: list[Cause] = Field(description="가능성 높은 순. 근거가 없으면 빈 목록")
    steps: list[Step] = Field(description="조치 런북 단계")
    fix_id: Optional[str] = Field(default=None, description="1순위 원인에 맞는 fix catalog 조치. 없으면 null")
    summary_ko: str = Field(description="관리자에게 보여 줄 한국어 요약 (2~4문장, 근거 doc_id 표기)")
    symptom_matches: bool = Field(default=True, description="문의에 적힌 증상을 테넌트 점검(findings)에서 확인된 문제로 설명할 수 있으면 true, "
                                  "증상과 findings가 맞지 않으면 false")
