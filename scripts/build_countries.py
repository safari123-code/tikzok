# ---------------------------
# Build countries Tikzok format
# ---------------------------

import json
from pathlib import Path

src = Path("static/data/countries_raw.json")
dst = Path("static/data/countries.json")

data = json.loads(src.read_text(encoding="utf-8"))

def flag(iso):
    return "".join(chr(ord(c)+127397) for c in iso)

out = []

for c in data:
    iso = c.get("cca2")
    name = c.get("name",{}).get("common")
    dial = None

    root = c.get("idd",{}).get("root")
    suffix = (c.get("idd",{}).get("suffixes") or [None])[0]

    if root and suffix:
        dial = f"{root}{suffix}"

    if iso and name and dial:
        out.append({
            "iso": iso,
            "name": name,
            "dial": dial,
            "flag": flag(iso)
        })

dst.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

print("✅ countries.json generated:", len(out))