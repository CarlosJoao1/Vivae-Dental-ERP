"""
Quick backend smoke test.

Usage:
  python backend/scripts/smoke_test.py --base http://127.0.0.1:5000 \
      --user admin --password admin123 --tenant <tenant_id_optional>

This script checks:
  - /api/health and /api/health/info
  - /auth/login -> token retrieval
  - /auth/me and /auth/stats (with Authorization)
  - /api/tenants (scoped)

It prints PASS/FAIL for each step and exits non-zero on failure.
"""

from __future__ import annotations

import sys
import json
import argparse
from typing import Any, Dict, Optional

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - lightweight inline guidance
    print("requests package not found. Install with: pip install requests", file=sys.stderr)
    sys.exit(2)


def _get(url: str, headers: Optional[Dict[str, str]] = None):  # type: ignore
    import requests
    return requests.get(url, headers=headers, timeout=10)


def _post(url: str, json_body: Dict[str, Any], headers: Optional[Dict[str, str]] = None):  # type: ignore
    import requests
    return requests.post(url, json=json_body, headers=headers, timeout=10)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:5000", help="Base URL for backend, e.g., http://127.0.0.1:5000")
    ap.add_argument("--user", default="admin", help="Username to login")
    ap.add_argument("--password", default="admin123", help="Password to login")
    ap.add_argument("--tenant", default=None, help="Optional tenant id for X-Tenant-Id header")
    args = ap.parse_args()

    base = args.base.rstrip("/")
    ok_all = True

    # 1) Health
    try:
        r = _get(f"{base}/api/health")
        r.raise_for_status()
        data = r.json()
        print("[PASS] /api/health:", data)
    except Exception as e:
        print("[FAIL] /api/health:", e)
        return 1

    # 2) Health info
    try:
        r = _get(f"{base}/api/health/info")
        r.raise_for_status()
        data = r.json()
        print("[PASS] /api/health/info:", {k: data.get(k) for k in ("ok", "version")})
    except Exception as e:
        print("[FAIL] /api/health/info:", e)
        return 1

    # 3) Login
    token = None
    try:
        r = _post(f"{base}/auth/login", {"username": args.user, "password": args.password})
        r.raise_for_status()
        data = r.json()
        token = data.get("access_token")
        assert token, "missing access_token"
        print("[PASS] /auth/login: token acquired")
    except Exception as e:
        print("[FAIL] /auth/login:", e)
        return 1

    # Common headers
    headers = {"Authorization": f"Bearer {token}"}
    if args.tenant:
        headers["X-Tenant-Id"] = args.tenant

    # 4) /auth/me
    try:
        r = _get(f"{base}/auth/me", headers=headers)
        r.raise_for_status()
        data = r.json()
        print("[PASS] /auth/me:", {k: data.get(k) for k in ("username", "role", "tenant_id")})
    except Exception as e:
        print("[FAIL] /auth/me:", e)
        return 1

    # 5) /auth/stats
    try:
        r = _get(f"{base}/auth/stats", headers=headers)
        r.raise_for_status()
        data = r.json()
        print("[PASS] /auth/stats:", {k: data.get(k) for k in ("tenants_accessible", "users_in_tenant", "total_users")})
    except Exception as e:
        print("[FAIL] /auth/stats:", e)
        return 1

    # 6) /api/tenants
    try:
        r = _get(f"{base}/api/tenants", headers=headers)
        r.raise_for_status()
        data = r.json()
        print(f"[PASS] /api/tenants: {len(data)} tenants returned")
    except Exception as e:
        print("[FAIL] /api/tenants:", e)
        return 1

    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
