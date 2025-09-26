import os
import re
import chardet

def read_script_auto_encode(path):
    with open(path, "rb") as f:
        raw_data = f.read()
    detected = chardet.detect(raw_data)
    encoding = detected.get('encoding', 'utf-8') or 'utf-8'
    try:
        return raw_data.decode(encoding)
    except Exception:
        return raw_data.decode("utf-8", errors="ignore")

def generate_code(intent, params):
    file_map = {
        "block": "nx_examples/block.py",
        "unite": "nx_examples/unite.py",
        "extract_region": "nx_examples/extract_region.py",
        "fillet": "nx_examples/fillet.py",
        "extrude": "nx_examples/extrude.py"
    }
    if intent not in file_map:
        return "# ❌ Unknown intent. Try: block, unite, extract_region, fillet, extrude."
    filepath = file_map[intent]
    if not os.path.exists(filepath):
        return f"# ❌ File not found: {filepath}"
    code = read_script_auto_encode(filepath)
    matches = re.findall(r"\{param(\d+)\}", code)
    max_param = max([int(m) for m in matches], default=0)
    for i in range(1, max_param + 1):
        param_val = params[i-1] if len(params) >= i else "0"
        code = code.replace(f"{{param{i}}}", param_val)
    return code
