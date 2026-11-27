"""가상 테넌트 도구 (패턴 2·4): check_tenant_state(읽기), propose_fix(제안만).

실제 적용(apply_fix)은 에이전트 도구가 아니고, 승인 게이트(src/approval/gate.py)가 관리자 승인 후에만 부른다(D-3).
"""
from __future__ import annotations

import json
import os

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from src import tenant


def _thread_id(config: RunnableConfig) -> str:
    return (config or {}).get("configurable", {}).get("thread_id", "default")


@tool
def check_tenant_state(config: RunnableConfig) -> str:
    """현재 고객 테넌트(가상)의 Entra 앱 권한, WIF 매핑, 그룹 클레임, SharePoint 사이트 권한, 사용자 식별자, 최근 오류를 읽는다. 읽기 전용.
    결과의 checks는 코드로 계산한 비교 결과(권장 구성 대비 차이, 그룹 수 한도, 식별자 대소문자 등)이므로 값 비교는 checks를 우선 근거로 쓴다."""
    state = tenant.get_state(_thread_id(config))
    # [추가 구현] 값 비교는 코드가 하고 결과(checks)를 함께 돌려준다 (강사 피드백, D-15). 장애 ID는 넣지 않는다.
    if os.getenv("DISABLE_CHECKS") == "1":   # 비교 실험용: checks 없이 원본만 (강사 힌트 효과 측정)
        return json.dumps(state, ensure_ascii=False, indent=1)
    return json.dumps({"checks": tenant.compute_checks(state), "state": state}, ensure_ascii=False, indent=1)


@tool
def propose_fix(fix_id: str, reason: str) -> str:
    """조치를 '제안'한다. 실제 적용은 관리자가 승인한 뒤에만 시스템이 한다. 직접 적용했다고 말하지 말 것.

    Args:
        fix_id: 다음 중 하나 - grant_admin_consent, disable_write_actions, remap_subject_to_lower_email,
                align_user_identifier, restrict_group_claims, grant_site_fullcontrol
        reason: 이 조치를 제안하는 근거 (문서 doc_id 포함)
    """
    if fix_id not in tenant.FIXES:
        return f"오류: fix catalog에 없는 fix_id입니다({fix_id}). 목록 안에서만 제안할 수 있습니다."
    f = tenant.FIXES[fix_id]
    return f"제안 기록됨: {fix_id} (위험도 {f['risk']}) - {f['action']}. 관리자 승인 전까지 적용되지 않습니다."

