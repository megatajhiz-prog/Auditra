#!/usr/bin/env python3
"""Build app/index.html (the offline Windows viewer) from the YAML knowledge bank. Needs: pip install pyyaml"""
import base64, glob, json
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
F, K = [], []
for f in sorted(glob.glob(str(ROOT / "knowledge" / "calculations" / "CAL-*.yaml"))):
    d = yaml.safe_load(open(f, encoding="utf-8"))
    for r in d["records"]:
        r = {**d.get("defaults", {}), **r}
        F.append({"id": r["id"], "e": d["engine"], "fa": r["fa"], "en": r["en"], "x": r["expr"], "v": [{k: v[k] for k in ("s", "fa", "u", "k")} for v in r["vars"]],
                  "r": r["res"], "va": r["valid"], "er": r["err"], "l": r["lvl"], "rv": r.get("status") in ("expert_reviewed", "approved")})
for f in sorted(glob.glob(str(ROOT / "knowledge" / "indicators" / "KPI-*.yaml"))):
    d = yaml.safe_load(open(f, encoding="utf-8"))
    for r in d["records"]:
        r = {**d.get("defaults", {}), **r}
        K.append({"id": r["id"], "g": d["group"], "fa": r["fa"], "en": r["en"], "f": r["frm"], "u": r["unit"], "p": r["per"], "l": r["lvl"], "d": r["dir"],
                  "rv": r.get("status") in ("expert_reviewed", "approved")})
pick = lambda rows: [{"id": x["id"], "fa": x["fa"], "en": x["en"]} for x in rows]
D = {"meta": {"v": "0.4.0", "built": str(date.today())}, "S": pick(load("systems.yaml")), "I": pick(load("industries.yaml")),
     "T": pick(load("stream_types.yaml")), "X": pick(load("other_flows.yaml")), "R": pick(load("roles.yaml")),
     "P": [{"id": x["id"], "fa": x["fa"], "en": x["en"], "u": x["unit"]} for x in load("parameters.yaml")], "E": recs, "F": F, "K": K, "CE": pick(load("calc_engines.yaml")), "KG": pick(load("kpi_groups.yaml"))}
uri = lambda f: "data:image/png;base64," + base64.b64encode((ROOT / "assets" / f).read_bytes()).decode()
html = (ROOT / "tools" / "app_template.html").read_text(encoding="utf-8").replace("/*DATA*/", "const D=" + json.dumps(D, ensure_ascii=False) + ";").replace("/*ECON*/", (ROOT / "tools" / "econ.js").read_text(encoding="utf-8")).replace("/*LOGO*/", uri("logo.png")).replace("/*ICON*/", uri("icon-64.png"))
out = ROOT / "app" / "index.html"; out.parent.mkdir(exist_ok=True); out.write_text(html, encoding="utf-8")
print(f"app/index.html written: {len(recs)} records, {len(html)//1024} KB")
