#!/usr/bin/env python3
"""Build app/index.html (the offline Windows viewer) from the YAML knowledge bank. Needs: pip install pyyaml"""
import glob, json
from datetime import date
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parent.parent
V = ROOT / "knowledge" / "vocab"
load = lambda n: yaml.safe_load((V / n).read_text(encoding="utf-8"))
recs = []
for f in sorted(glob.glob(str(ROOT / "knowledge" / "equipment" / "SYS-*.yaml"))):
    d = yaml.safe_load(open(f, encoding="utf-8"))
    for r in d["records"]:
        r = {**d.get("defaults", {}), **r}
        recs.append({"id": r["id"], "sys": d["system"], "fa": r["fa"], "en": r["en"], "role": r["role"], "in": r.get("in", []),
                     "out": r.get("out", []), "fl": r.get("flows", []), "ind": r.get("ind", ["ALL"]), "pa": r["params"], "no": r["note"],
                     "rv": r.get("status") in ("expert_reviewed", "approved")})
pick = lambda rows: [{"id": x["id"], "fa": x["fa"], "en": x["en"]} for x in rows]
D = {"meta": {"v": "0.2.0", "built": str(date.today())}, "S": pick(load("systems.yaml")), "I": pick(load("industries.yaml")),
     "T": pick(load("stream_types.yaml")), "X": pick(load("other_flows.yaml")), "R": pick(load("roles.yaml")),
     "P": [{"id": x["id"], "fa": x["fa"], "en": x["en"], "u": x["unit"]} for x in load("parameters.yaml")], "E": recs}
html = (ROOT / "tools" / "app_template.html").read_text(encoding="utf-8").replace("/*DATA*/", "const D=" + json.dumps(D, ensure_ascii=False) + ";")
out = ROOT / "app" / "index.html"; out.parent.mkdir(exist_ok=True); out.write_text(html, encoding="utf-8")
print(f"app/index.html written: {len(recs)} records, {len(html)//1024} KB")
