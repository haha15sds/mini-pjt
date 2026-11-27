"""가상 테넌트 코드 점검 (D-15·D-16): 값 비교와 문제 판정을 코드로 계산한다. 장애 ID는 에이전트에 보여 주지 않는다."""
from __future__ import annotations

from src.tenant.store import BASELINE, diff


# ---------- [추가 구현] 코드로 계산한 점검 결과 (강사 피드백 반영, D-15) ----------
# 값 비교로 갈리는 원인(대소문자, 그룹 수 한도 등)은 LLM이 원본 JSON을 눈으로 비교하면 흔들릴 수 있으므로
# 비교는 코드가 하고 결과만 돌려준다. 장애 ID·장애 이름은 넣지 않는다.
GROUP_CLAIM_LIMIT = {"OIDC": 200, "SAML": 150}   # Entra ID 토큰 그룹 클레임 한도 (공식 문서 ge-idp)


def compute_checks(state: dict) -> dict:
    ref = BASELINE
    checks: dict = {"reference": "권장 구성(data/tenant_baseline.json)과 비교한 결과. 원인 판단은 findings만 근거로 한다"}

    changed = [{"path": c["path"], "reference": c["before"], "current": c["after"]}
               for c in diff(ref, state) if not c["path"].startswith("recent_errors")]
    checks["diff_from_reference"] = changed

    provider = state.get("wif_mapping", {}).get("provider", "")
    proto = "SAML" if "SAML" in provider.upper() else "OIDC"
    limit = GROUP_CLAIM_LIMIT[proto]
    filt = state.get("wif_mapping", {}).get("group_claims_filter")
    over = [{"user_id": u["user_id"], "group_count": u.get("group_count", 0)}
            for u in state.get("users", []) if u.get("group_count", 0) > limit]
    checks["group_claim_check"] = {"protocol": proto, "limit": limit, "group_claims_filter": filt,
                                   "filter_limits_to_assigned_groups": filt == "groups_assigned_to_application",
                                   "users_over_limit": over}

    ids = []
    for u in state.get("users", []):
        vals = {k: u.get(k, "") for k in ("email", "upn", "subject_seen")}
        exact = len(set(vals.values())) == 1
        lower_same = len({v.lower() for v in vals.values()}) == 1
        ref_u = next((x for x in ref.get("users", []) if x["user_id"] == u["user_id"]), {})
        ids.append({"user_id": u["user_id"],
                    "email_upn_subject": "일치" if exact else ("대소문자만 다름" if lower_same else "값이 다름"),
                    "email_changed_from_reference": bool(ref_u) and ref_u.get("email") != u.get("email"),
                    "has_uppercase": any(c.isupper() for c in vals["subject_seen"])})
    checks["identifier_check"] = ids

    subj = state.get("wif_mapping", {}).get("google_subject", "")
    checks["subject_mapping_check"] = {"google_subject": subj, "email_based": "email" in subj or "upn" in subj,
                                       "lowercased": "lowerAscii" in subj, "uses_object_id": "oid" in subj}

    sp = state.get("sharepoint", {})
    checks["sites_check"] = {"permission_mode": sp.get("permission_mode"),
                             "sites_without_fullcontrol": [s["site_id"] for s in sp.get("sites", [])
                                                           if s.get("selected") and not s.get("fullcontrol_granted")]}

    app = state.get("entra_app", {})
    checks["entra_app_check"] = {"admin_consent": app.get("admin_consent"),
                                 "write_actions_enabled": app.get("write_actions_enabled"),
                                 "write_scopes_present": bool(app.get("write_scopes"))}

    # [추가 구현] findings: 차이 중 '실제로 문제인 것'만 코드 규칙으로 판정한 문장 (장애 ID·이름 없음).
    # 강사 힌트 점검(변형 20개)에서 권장 구성과 다르기만 해도 원인으로 삼는 오진(대조군 1/5)이 나와 추가했다.
    f, ok = [], []
    if app.get("admin_consent") is False:
        f.append("Entra 앱에 테넌트 전체 관리자 동의가 없다(admin_consent=false).")
    if app.get("write_actions_enabled") and not app.get("write_scopes"):
        f.append("쓰기 동작(actions)이 켜져 있는데 쓰기 권한(scope)이 없다.")
    if checks["subject_mapping_check"]["uses_object_id"] or not checks["subject_mapping_check"]["email_based"]:
        f.append(f"google.subject 매핑이 이메일 기반이 아니다({subj}).")
    for i in ids:
        if i["email_upn_subject"] != "일치":
            f.append(f"{i['user_id']}의 email·upn·subject_seen이 서로 다르다({i['email_upn_subject']}).")
        elif i["email_changed_from_reference"]:
            f.append(f"{i['user_id']}의 이메일(식별자 값)이 이전 기록과 달라졌다 — 식별자가 바뀌면 새 사용자로 처리된다.")
        elif i["has_uppercase"]:
            f.append(f"{i['user_id']}의 식별자에 대문자가 있다 — 식별자는 대소문자를 구분한다.")
    if over and filt == "groups_assigned_to_application":
        ok.append(f"{', '.join(o['user_id'] for o in over)}의 그룹 수는 {limit}개를 넘지만, 그룹 클레임을 '앱에 할당된 그룹'으로 제한해 토큰 한도 문제는 아니다.")
    elif over:
        f.append(f"{', '.join(o['user_id'] for o in over)}의 그룹 수가 {proto} 토큰 한도 {limit}개를 넘는다(그룹 클레임이 빠질 수 있음).")
    else:
        ok.append(f"그룹 수가 {proto} 토큰 한도 {limit}개를 넘는 사용자는 없다(최대 {max((u.get('group_count', 0) for u in state.get('users', [])), default=0)}개) — 그룹 클레임 한도 문제는 아니다.")
    if checks["sites_check"]["sites_without_fullcontrol"]:
        f.append(f"Sites.Selected 대상 사이트 중 fullcontrol이 없는 곳: {', '.join(checks['sites_check']['sites_without_fullcontrol'])}.")
    checks["findings"] = f or ["코드 점검에서 문제로 판정된 설정이 없다."]
    checks["not_a_problem"] = ok
    order = ["findings", "not_a_problem"] + [k for k in checks if k not in ("findings", "not_a_problem")]
    return {k: checks[k] for k in order}


def supported_faults(checks: dict) -> set[str]:
    """[불일치 대응] 코드 점검 결과로 근거가 확인되는 장애 ID 집합. 에이전트에게는 보여 주지 않고,
    계획 단계가 낸 원인 후보를 검증하는 데만 쓴다(테넌트에 근거 없는 원인 제거, 빠진 실제 문제 보충)."""
    out = set()
    app = checks.get("entra_app_check", {})
    if app.get("admin_consent") is False:
        out.add("F1")
    if app.get("write_actions_enabled") and not app.get("write_scopes_present"):
        out.add("F2")
    sm = checks.get("subject_mapping_check", {})
    if sm.get("uses_object_id") or not sm.get("email_based", True):
        out.add("F3")
    # subject가 객체 ID로 매핑되면 모든 사용자의 식별자가 이메일과 달라 보이는데, 이는 F3의 결과이므로 F4로 따로 세지 않는다
    if "F3" not in out and any(i["email_upn_subject"] != "일치" or i["email_changed_from_reference"] or i["has_uppercase"]
                               for i in checks.get("identifier_check", [])):
        out.add("F4")
    g = checks.get("group_claim_check", {})
    if g.get("users_over_limit") and not g.get("filter_limits_to_assigned_groups"):
        out.add("F5")
    if checks.get("sites_check", {}).get("sites_without_fullcontrol"):
        out.add("F6")
    return out
