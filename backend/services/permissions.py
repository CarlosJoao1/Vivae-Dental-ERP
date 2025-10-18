from __future__ import annotations

from typing import Optional
from flask import request
from models.user import User
from models.laboratory import Laboratory
from models.role_policy import RolePolicy


def _resolve_lab_for_user(user: User) -> Optional[Laboratory]:
    """Resolve active lab using X-Tenant-Id header if allowed, else user's tenant_id."""
    tid = (request.headers.get("X-Tenant-Id") or "").strip()
    if tid:
        try:
            if getattr(user, 'is_sysadmin', False):
                return Laboratory.objects.get(id=tid)
            allowed_ids = [str(getattr(x, 'id', '')) for x in (getattr(user, 'allowed_labs', []) or [])]
            if tid in allowed_ids:
                return Laboratory.objects.get(id=tid)
        except Exception:
            return None
    return getattr(user, 'tenant_id', None)


def can(user: User, lab: Optional[Laboratory], feature: str, action: str) -> bool:
    """Evaluate if user can perform action on feature within lab scope.

    Rules:
    - Sysadmin: allow all
    - If no lab provided, try resolve from header/user
    - Load RolePolicy for lab; if missing, fallback:
        - role == 'admin' → allow all
        - else → allow read, deny create/update/delete
    - If policy exists and role entry present → check feature[action]
    """
    if getattr(user, 'is_sysadmin', False):
        return True

    role = (getattr(user, 'role', '') or '').lower()
    if lab is None:
        lab = _resolve_lab_for_user(user)

    try:
        rp = RolePolicy.objects(lab=lab).first() if lab is not None else None
    except Exception:
        rp = None

    if not rp:
        # Sensible defaults when no explicit policy exists
        if role == 'admin':
            return True
        # read allowed for everyone; mutations denied
        return action == 'read'

    try:
        policies = rp.policies or {}
        role_map = policies.get(role, {})
        feat = role_map.get(feature, {})
        val = feat.get(action)
        if isinstance(val, bool):
            return val
        # if unspecified, default like above
        if role == 'admin':
            return True
        return action == 'read'
    except Exception:
        return False


def ensure(user: User, lab: Optional[Laboratory], feature: str, action: str) -> Optional[dict]:
    """Return an error dict if not allowed; None otherwise."""
    if not can(user, lab, feature, action):
        return {"error": "not allowed", "feature": feature, "action": action}
    return None
