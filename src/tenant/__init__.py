"""가상 테넌트 도메인: 상태 저장소(store), 코드 점검(checks), 에이전트 도구(tools).

화면·평가 스크립트는 `from src import tenant` 로 불러 `tenant.get_state(...)` 처럼 쓴다.
"""
from src.tenant.checks import GROUP_CLAIM_LIMIT, compute_checks, supported_faults  # noqa: F401
from src.tenant.store import (_APPLIED, _TENANTS, BASELINE, FAULTS, FIXES, SCENARIOS, apply_fix,  # noqa: F401
                              apply_patch, diff, ensure_thread, get_state, has_thread, initial_state)
