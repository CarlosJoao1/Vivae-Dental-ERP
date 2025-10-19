#!/usr/bin/env python3
"""
Refactor permission checks in masterdata.py to use _check_permission helper.
Reduces code duplication from permission check blocks.
"""

import re

def refactor_permissions():
    filepath = "backend/routes/masterdata.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern 1: Permission check with lab variable
    # Matches:
    #     # Permission: resource.action
    #     try:
    #         uid = get_jwt_identity()
    #         user = User.objects.get(id=uid)
    #         err = ensure(user, lab, 'resource', 'action')
    #         if err:
    #             return jsonify(err), 403
    #     except Exception:
    #         pass
    
    pattern1 = re.compile(
        r"    # Permission: ([\w_]+)\.([\w_]+)\n"
        r"    try:\n"
        r"        uid = get_jwt_identity\(\)\n"
        r"        user = User\.objects\.get\(id=uid\)\n"
        r"        err = ensure\(user, lab, '([\w_]+)', '([\w_]+)'\)\n"
        r"        if err:\n"
        r"            return jsonify\(err\), 403\n"
        r"    except Exception:\n"
        r"        pass",
        re.MULTILINE
    )
    
    def replace1(match):
        resource = match.group(1)
        action = match.group(2)
        return (
            f"    # Permission: {resource}.{action}\n"
            f"    perm_err = _check_permission(lab, '{resource}', '{action}')\n"
            f"    if perm_err:\n"
            f"        return perm_err"
        )
    
    content = pattern1.sub(replace1, content)
    
    # Pattern 2: Permission check with None as lab (for laboratories endpoints)
    # Matches:
    #     # Permission: resource.action (comment variant)
    #     try:
    #         uid = get_jwt_identity()
    #         user = User.objects.get(id=uid)
    #         err = ensure(user, None, 'resource', 'action')
    #         if err:
    #             return jsonify(err), 403
    #     except Exception:
    #         pass
    
    pattern2 = re.compile(
        r"    # Permission: ([\w_]+)\.([\w_]+)(?:\s+\([^)]*\))?\n"
        r"    try:\n"
        r"        uid = get_jwt_identity\(\)\n"
        r"        (?:from models\.user import User\s+)?"
        r"        user = User\.objects\.get\(id=uid\)\n"
        r"        err = ensure\(user, None, '([\w_]+)', '([\w_]+)'\)\n"
        r"        if err:\n"
        r"            return jsonify\(err\), 403",
        re.MULTILINE
    )
    
    def replace2(match):
        resource = match.group(1)
        action = match.group(2)
        return (
            f"    # Permission: {resource}.{action}\n"
            f"    perm_err = _check_permission(None, '{resource}', '{action}')\n"
            f"    if perm_err:\n"
            f"        return perm_err"
        )
    
    content = pattern2.sub(replace2, content)
    
    # Pattern 3: Inline permission checks without comment
    pattern3 = re.compile(
        r"    try:\n"
        r"        uid = get_jwt_identity\(\)\n"
        r"        (?:from models\.user import User\s+)?"
        r"        user = User\.objects\.get\(id=uid\)\n"
        r"        err = ensure\(user, (?:lab|None), '([\w_]+)', '([\w_]+)'\)\n"
        r"        if err:\n"
        r"            return jsonify\(err\), 403\n"
        r"    except Exception:\n"
        r"        pass",
        re.MULTILINE
    )
    
    def replace3(match):
        resource = match.group(1)
        action = match.group(2)
        lab_arg = "lab" if "lab" in match.group(0) else "None"
        return (
            f"    perm_err = _check_permission({lab_arg}, '{resource}', '{action}')\n"
            f"    if perm_err:\n"
            f"        return perm_err"
        )
    
    content = pattern3.sub(replace3, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Refactored {filepath}")
    print("   - Replaced permission check blocks with _check_permission() calls")
    print("   - Reduced code duplication significantly")

if __name__ == "__main__":
    refactor_permissions()
