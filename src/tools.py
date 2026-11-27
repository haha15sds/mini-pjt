"""[과제 규약 3-1] 도메인 도구 — 진입 파일.

실제 코드는 각 도메인 폴더에 있다(배치 규칙은 CLAUDE.md). 에이전트가 쓰는 도구는 읽기·제안 3개뿐이다(D-8).
- retrieve_docs      : src/knowledge/tools.py  (공식 문서 하이브리드 검색)
- check_tenant_state : src/tenant/tools.py     (가상 테넌트 조회 + 코드 점검 결과)
- propose_fix        : src/tenant/tools.py     (조치 제안만, 적용은 승인 게이트가 승인 후에)
"""
from src.diagnosis.react import TOOLS  # noqa: F401
from src.knowledge.tools import ctx_entry, retrieve_docs  # noqa: F401
from src.tenant.tools import check_tenant_state, propose_fix  # noqa: F401
