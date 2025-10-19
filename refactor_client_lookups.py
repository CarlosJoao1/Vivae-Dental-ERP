#!/usr/bin/env python3
"""
Refactor client lookup patterns in masterdata.py to use _get_client_or_404 helper.
"""

import re

def refactor_client_lookups():
    filepath = "backend/routes/masterdata.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern: try/except block for Client.objects.get
    # Matches:
    #     try:
    #         cli = Client.objects.get(id=cid, lab=lab)
    #     except DoesNotExist:
    #         return jsonify({"error": ERROR_CLIENT_NOT_FOUND}), 404
    
    pattern = re.compile(
        r"    try:\n"
        r"        cli = Client\.objects\.get\(id=(\w+), lab=lab\)\n"
        r"    except DoesNotExist:\n"
        r"        return jsonify\(\{\"error\": ERROR_CLIENT_NOT_FOUND\}\), 404",
        re.MULTILINE
    )
    
    def replace_match(match):
        var_name = match.group(1)
        return (
            f"    cli, err = _get_client_or_404(lab, {var_name})\n"
            f"    if err:\n"
            f"        return err"
        )
    
    original_count = len(pattern.findall(content))
    content = pattern.sub(replace_match, content)
    
    # También hay este patrón más corto sin el jsonify completo:
    # except DoesNotExist:
    #     return jsonify({"error": "client not found"}), 404
    
    pattern2 = re.compile(
        r"    try:\n"
        r"        cli = Client\.objects\.get\(id=(\w+), lab=lab\)\n"
        r"    except DoesNotExist:\n"
        r"        return jsonify\(\{\"error\": \"client not found\"\}\), 404",
        re.MULTILINE
    )
    
    original_count2 = len(pattern2.findall(content))
    content = pattern2.sub(replace_match, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    total_replaced = original_count + original_count2
    print(f"✅ Refactored {filepath}")
    print(f"   - Replaced {total_replaced} Client lookup patterns")
    print(f"   - Using _get_client_or_404() helper")
    print(f"   - Significantly reduced code duplication")

if __name__ == "__main__":
    refactor_client_lookups()
