"""가드레일: 개인정보·시크릿 마스킹(G1·G2)과 프롬프트 인젝션 탐지(G3).

mask_pii 는 순수 함수다(D-6). handle_query 가 그래프 실행 전에 한 번 부르고,
그래프 안 input_guard 와 output_guard 가 같은 함수로 다시 검사한다.
이메일·전화번호·시크릿은 규칙으로 100% 가리는 것이 목표이고,
사람 이름은 '○○님', '팀 ○○○입니다/드림' 같은 규칙으로만 가린다(best-effort, 알려진 한계).
"""
from __future__ import annotations

import re

EMAIL_TOKEN, PHONE_TOKEN, SECRET_TOKEN, NAME_TOKEN = "[EMAIL]", "[PHONE]", "[SECRET]", "[NAME]"

_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
# 한국 휴대전화·유선전화 (하이픈·공백·점 허용), 국제번호 +82
_PHONE = re.compile(r"(?<!\d)(?:\+82[-\s.]?|0)(?:1[016789]|2|[3-6][1-5]|70)[-\s.]?\d{3,4}[-\s.]?\d{4}(?!\d)")
# 키=값 형태의 비밀값
_SECRET_KV = re.compile(
    r"(?i)\b(client[_\s-]?secret|secret(?:[_\s-]?value)?|password|passwd|api[_\s-]?key|access[_\s-]?key|token|비밀\s?값|비밀번호|시크릿)"
    r"(\s*(?:[:=]|은|는|이|가)?\s*)(?!\[(?:SECRET|EMAIL|PHONE|NAME)\])([^\s,;'\"]{6,})"   # [2차] 이미 가린 토큰은 제외
)
# 값만 있어도 알아볼 수 있는 형식: Entra 클라이언트 시크릿(xxx~...), AWS 키, sk- 키
_SECRET_RAW = re.compile(r"\b(?:[A-Za-z0-9]{3}\d?~[A-Za-z0-9_.~\-]{12,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_\-]{16,})\b")
# 이름 규칙: '홍길동님', '팀 홍길동입니다', '홍길동 드림'
_NAME_HONORIFIC = re.compile(r"(?<![가-힣])([가-힣]{2,4})(?=\s?님)")
_NAME_SIGN = re.compile(r"((?:팀|부|실|과|센터)\s+)([가-힣]{2,4})(?=\s?(?:입니다|드림|올림))")
_NAME_STOP = {"관리자", "담당자", "고객", "사용자", "직원", "본부장", "팀장", "대리", "과장", "부장", "여러분", "선생", "IT팀"}


def mask_pii(text: str) -> tuple[str, list[str]]:
    """개인정보·시크릿을 토큰으로 바꾼다. (가린 텍스트, 탐지된 종류 목록)"""
    if text is None:
        raise ValueError("text is None")
    found: list[str] = []
    out = text

    def sub(pattern, repl, kind):
        nonlocal out
        new, n = pattern.subn(repl, out)
        if n:
            found.append(kind)
        out = new

    sub(_SECRET_KV, lambda m: f"{m.group(1)}{m.group(2)}{SECRET_TOKEN}", "secret")
    sub(_SECRET_RAW, SECRET_TOKEN, "secret")
    sub(_EMAIL, EMAIL_TOKEN, "email")
    sub(_PHONE, PHONE_TOKEN, "phone")
    sub(_NAME_SIGN, lambda m: f"{m.group(1)}{NAME_TOKEN}", "name")
    out2, n = _NAME_HONORIFIC.subn(lambda m: m.group(0) if m.group(1) in _NAME_STOP else NAME_TOKEN, out)
    if out2 != out:
        found.append("name")
    out = out2
    return out, sorted(set(found))


def residual_pii(text: str) -> list[str]:
    """이미 가린 텍스트에 이메일·전화·시크릿이 남았는지 검사(이름 제외)."""
    _, kinds = mask_pii(text)
    return [k for k in kinds if k in ("email", "phone", "secret")]


_INJECTION = [
    r"이전\s*(의\s*)?지시(를|는)?\s*(모두\s*)?(무시|잊)",
    r"(시스템|system)\s*(프롬프트|prompt)",
    r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"승인\s*(절차\s*)?(없이|생략)",
    r"(AI|에이전트|어시스턴트)\s*(에게|님께)\s*[:：]",
    r"(바로|즉시)\s*(적용|실행)한\s*뒤",
    r"라고만\s*답하",
]


def detect_injection(text: str) -> list[str]:
    """문의에 붙여넣은 내용 속 지시문을 찾는다. 찾은 패턴 목록(없으면 빈 목록)."""
    return [p for p in _INJECTION if re.search(p, text)]


REFUSE_SECRET = "보안상 시크릿·비밀번호 같은 비밀값은 확인하거나 다시 알려 드릴 수 없습니다."
# [리뷰 수정] '확인하고'를 빼서 "시크릿이 만료됐는지 확인하고 싶어요" 같은 정상 문의는 거절하지 않는다.
SECRET_REQUEST = re.compile(r"(시크릿|비밀\s?값|비밀번호|secret|password|키\s?값).{0,40}(다시\s*알려|알려\s*주|보여\s*주|전체\s*값)", re.I | re.S)
