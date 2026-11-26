"""가상 테넌트 (D-1·D-2·D-3).

- 정상 상태 data/tenant_baseline.json 에 시나리오 patch(data/scenarios.json)를 덮어써 장애를 주입한다.
  장애 주입은 그래프 밖에서 thread 를 처음 만들 때 한 번만 한다(D-2).
- thread_id 마다 메모리 복사본을 따로 둔다. 서버를 다시 켜면 사라진다(범위 밖, C-8).
- apply_fix 는 fix_catalog.json 의 patch 만 적용하고, 같은 thread·fix_id 는 한 번만 적용한다.
"""
from __future__ import annotations

import copy
import json
import re
import threading
import uuid
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
_lock = threading.Lock()


def _load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


BASELINE = _load("tenant_baseline.json")["tenant"]
SCENARIOS = {s["scenario_id"]: s for s in _load("scenarios.json")["scenarios"]}
FIXES = {f["fix_id"]: f for f in _load("fix_catalog.json")["fixes"]}
FAULTS = {f["fault_id"]: f for f in _load("faults.json")["faults"]}

_TENANTS: dict[str, dict] = {}
_APPLIED: dict[str, set[str]] = {}
_SCENARIO_OF: dict[str, str] = {}


# ---------- patch 적용 ----------
_SEG = re.compile(r"^(\w+)(?:\[(\*|\w+=[\w.\-@]+)\])?$")


def _special(value, item: dict):
    if value == "=object_id":
        return str(uuid.uuid5(uuid.NAMESPACE_URL, "oid-" + item.get("user_id", "")))
    if value == "=email_lower":
        return item.get("email", "").lower()
    return copy.deepcopy(value)


def _apply_path(obj: dict, path: str, value) -> None:
    segs = path.split(".")
    targets = [obj]
    for i, seg in enumerate(segs):
        m = _SEG.match(seg)
        if not m:
            raise ValueError(f"bad patch path: {path}")
        key, sel = m.group(1), m.group(2)
        last = i == len(segs) - 1
        nxt = []
        for t in targets:
            if sel is None:
                if last:
                    t[key] = _special(value, t)
                else:
                    nxt.append(t.setdefault(key, {}))
            else:
                items = t.get(key, [])
                if sel != "*":
                    k, v = sel.split("=", 1)
                    items = [x for x in items if str(x.get(k)) == v]
                if last:
                    raise ValueError(f"list selector cannot be last: {path}")
                nxt.extend(items)
        targets = nxt
    # 리스트 원소의 마지막 키 처리: users[*].email 같은 경우 targets 가 원소들이고
    # 위 루프의 마지막 seg 에서 이미 할당되었다.


def apply_patch(tenant: dict, patch: dict) -> None:
    for path, value in patch.items():
        _apply_path(tenant, path, value)


# ---------- thread 별 상태 ----------
def ensure_thread(thread_id: str, scenario_id: str = "S00") -> dict:
    with _lock:
        if thread_id not in _TENANTS:
            if scenario_id not in SCENARIOS:
                raise KeyError(f"unknown scenario_id: {scenario_id}")
            t = copy.deepcopy(BASELINE)
            for inj in SCENARIOS[scenario_id]["inject"]:
                apply_patch(t, inj["patch"])
            _TENANTS[thread_id] = t
            _APPLIED[thread_id] = set()
            _SCENARIO_OF[thread_id] = scenario_id
        return _TENANTS[thread_id]


def has_thread(thread_id: str) -> bool:
    return thread_id in _TENANTS


def get_state(thread_id: str) -> dict:
    """check_tenant_state 가 돌려주는 값. 장애 ID 는 들어 있지 않다."""
    return copy.deepcopy(ensure_thread(thread_id))


def initial_state(scenario_id: str) -> dict:
    t = copy.deepcopy(BASELINE)
    for inj in SCENARIOS[scenario_id]["inject"]:
        apply_patch(t, inj["patch"])
    return t


def apply_fix(thread_id: str, fix_id: str) -> tuple[bool, str]:
    """승인 후 approval_gate 안에서만 부른다. (적용 여부, 안내 문구)"""
    if fix_id not in FIXES:
        return False, f"fix catalog에 없는 조치입니다: {fix_id}"
    with _lock:
        if fix_id in _APPLIED.setdefault(thread_id, set()):
            return False, f"이미 적용된 조치입니다: {fix_id}"
        apply_patch(_TENANTS[thread_id], FIXES[fix_id]["patch"])
        _APPLIED[thread_id].add(fix_id)
    return True, f"조치를 적용했습니다: {FIXES[fix_id]['action']}"


def diff(before: dict, after: dict, prefix: str = "") -> list[dict]:
    """두 상태의 바뀐 값만 [{path, before, after}] 로 돌려준다 (UI 전/후 비교용)."""
    out: list[dict] = []
    keys = set(before) | set(after) if isinstance(before, dict) and isinstance(after, dict) else set()
    if not keys:
        if before != after:
            out.append({"path": prefix, "before": before, "after": after})
        return out
    for k in sorted(keys):
        b, a = before.get(k), after.get(k)
        p = f"{prefix}.{k}" if prefix else k
        if isinstance(b, dict) and isinstance(a, dict):
            out += diff(b, a, p)
        elif isinstance(b, list) and isinstance(a, list) and all(isinstance(x, dict) for x in b + a) and len(a) == len(b):
            for i, (xb, xa) in enumerate(zip(b, a)):
                label = xb.get("user_id") or xb.get("site_id") or str(i)
                out += diff(xb, xa, f"{p}[{label}]")
        elif b != a:
            out.append({"path": p, "before": b, "after": a})
    return out


# ---------- [추가 구현] 코드로 계산한 점검 결과 (강사 피드백 반영, D-15) ----------
# 값 비교로 갈리는 원인(대소문자, 그룹 수 한도 등)은 LLM이 원본 JSON을 눈으로 비교하면 흔들릴 수 있으므로
# 비교는 코드가 하고 결과만 돌려준다. 장애 ID·장애 이름은 넣지 않는다.
GROUP_CLAIM_LIMIT = {"OIDC": 200, "SAML": 150}   # Entra ID 토큰 그룹 클레임 한도 (공식 문서 ge-idp)


def compute_checks(state: dict) -> dict:
    ref = BASELINE
    checks: dict = {"reference": "권장 구성(data/tenant_baseline.json)과 비교한 결과"}

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
    return checks
