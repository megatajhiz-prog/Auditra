#!/usr/bin/env python3
"""Create the data-import templates (Excel, CSV zip) and the made-up training-sample workbook from templates/sample.json.
Needs: pip install pyyaml openpyxl"""
import csv, glob, io, json, zipfile
from pathlib import Path
import yaml
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
ROOT = Path(__file__).resolve().parent.parent; OUT = ROOT / "templates"; V = ROOT / "knowledge" / "vocab"
load = lambda n: yaml.safe_load((V / n).read_text(encoding="utf-8"))
SPEC = {
 "Site": [("name_fa","نام مجتمع (فارسی)","مجتمع نمونه",1),("name_en","نام مجتمع (انگلیسی)","Sample Complex",0),("owner","شرکت یا سازمان مالک","",0),("industry_group","گروه صنعتی (کد IND یا نام)","IND-09",0),("status","وضعیت فعالیت (active, stopped, building)","active",0),("climate_zone","منطقه اقلیمی","",0),("lat","عرض جغرافیایی","35.7",0),("lon","طول جغرافیایی","51.4",0),("calendar","تقویم نمایش (jalali یا gregorian)","jalali",0),("lang","زبان (fa یا en)","fa",0),("is_sample","نمونه‌ی آموزشی است؟ (yes یا no)","no",0),("note","یادداشت","",0)],
 "Units": [("unit_id","شناسه‌ی واحد","U1",1),("name","نام واحد","تأسیسات",1),("type","نوع واحد (production, service, utilities, admin)","utilities",0),("parent_unit","شناسه‌ی واحد بالاتر","",0)],
 "Nodes": [("node_id","شناسه‌ی گره","N1",1),("name","نام گره","مخزن آب تازه",1),("kind","نوع گره (source, storage, equipment, junction, boundary)","equipment",1),("unit_id","شناسه‌ی واحد","U1",0),("equipment_code","کد تجهیز از بانک (EQP-…) یا USR-…","EQP-08-009",0),("consumption_class","دسته‌ی مصرف (product, process, utility, sanitary, nonbeneficial)","utility",0),("required_basis","مبنای مقدار لازم (design, standard, balance, coc, best)","",0)],
 "Streams": [("stream_id","شناسه‌ی جریان","S1",1),("from_node","گره‌ی مبدأ","N1",0),("to_node","گره‌ی مقصد","N2",0),("stream_type","نوع جریان (کد یا نام)","fresh_water",1),("permitted_use","کاربرد مجاز (با ; جدا کنید)","",0),("recycle_status","وضعیت بازیافت (none, reused, recycled, reclaimed)","none",0),("note","یادداشت","",0)],
 "Meters": [("meter_id","شناسه‌ی نقطه‌ی اندازه‌گیری","M1",1),("node_id","گره (یکی از گره یا جریان)","",0),("stream_id","جریان (یکی از گره یا جریان)","S1",0),("parameter","پارامتر (کد یا نام)","volume",1),("unit","واحد","m3",0),("accuracy","دقت نسبی (مثلاً 0.02 یا 2%)","0.02",0),("method","روش اندازه‌گیری (direct, estimated, bill, lab)","direct",0)],
 "Readings": [("meter_id","شناسه‌ی نقطه‌ی اندازه‌گیری","M1",1),("period","شروع دوره (شمسی 1405/01/01 یا میلادی 2026-03-21)","1405/01/01",1),("granularity","گام (day, month, year)","month",1),("value","مقدار","1000",0),("quality","کیفیت (valid, estimated, suspect, invalid, missing)","valid",0)],
}
LISTS = {"kind":["source","storage","equipment","junction","boundary"],"status":["active","stopped","building"],"consumption_class":["product","process","utility","sanitary","nonbeneficial"],
 "recycle_status":["none","reused","recycled","reclaimed"],"quality":["valid","estimated","suspect","invalid","missing"],"granularity":["day","month","year"],"method":["direct","estimated","bill","lab"],"calendar":["jalali","gregorian"],"yesno":["yes","no"]}
SAMPLE = json.loads((OUT / "sample.json").read_text(encoding="utf-8"))
def help_rows(n):
    c = SPEC[n]; return [["#" + c[0][1]] + [x[1] for x in c[1:]], ["#"] + [("مثال: " + x[2]) if x[2] else "" for x in c[1:]]]
def csv_bytes(rows):
    b = io.StringIO(newline=""); w = csv.writer(b, lineterminator="\r\n"); [w.writerow(r) for r in rows]; return ("\ufeff" + b.getvalue()).encode("utf-8")
with zipfile.ZipFile(OUT / "Auditra-CSV-Templates.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for n in SPEC: z.writestr(f"{n}.csv", csv_bytes([[c[0] for c in SPEC[n]]] + help_rows(n)))
eq = []
for f in sorted(glob.glob(str(ROOT / "knowledge" / "equipment" / "SYS-*.yaml"))):
    d = yaml.safe_load(open(f, encoding="utf-8")); eq += [(r["id"], r["fa"], r["en"], d["system"]) for r in d["records"]]
st, pa = load("stream_types.yaml"), load("parameters.yaml")
def workbook(path, data):
    wb = Workbook(); g = wb.active; g.title = "Guide"
    for i, t in enumerate(["راهنمای الگوی ورود داده‌ی Auditra", "ردیف اول هر برگه عنوان ستون‌هاست و نباید تغییر کند. ردیف‌هایی که با # شروع می‌شوند توضیح‌اند و نادیده گرفته می‌شوند.",
        "ستون‌های با عنوان آبی الزامی‌اند: شناسه‌ها، نام، نوع گره، نوع جریان، پارامتر، دوره و گام.", "تاریخ را شمسی (1405/01/01) یا میلادی (2026-03-21) بنویسید. ماه و سال بر اساس همان تقویم محاسبه می‌شوند.",
        "جریان و نقطه‌ی اندازه‌گیری را با شناسه‌ی گره و جریان وصل کنید. کد تجهیز را از برگه‌ی Lists بردارید.", "مقدار خالی یعنی داده‌ی گمشده. کیفیت را valid, estimated, suspect, invalid یا missing بنویسید.",
        "Rows starting with # are comments. Row 1 holds the column keys. Dates: Jalali or Gregorian. Empty value = missing."]):
        g.cell(i + 1, 1, t); g.cell(i + 1, 1).font = Font(bold=(i == 0), size=13 if i == 0 else 11)
    g.column_dimensions["A"].width = 120
    for n, cols in SPEC.items():
        ws = wb.create_sheet(n); rows = [[c[0] for c in cols]] + (data[n][1:] if data else help_rows(n))
        for r in rows: ws.append(r)
        for j, c in enumerate(cols, 1):
            cell = ws.cell(1, j); cell.font = Font(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor="0E7490" if c[3] else "5B7A8A")
            ws.column_dimensions[cell.column_letter].width = max(16, min(40, len(c[1]) // 2 + 8))
        if not data:
            for r in (2, 3):
                for j in range(1, len(cols) + 1): ws.cell(r, j).font = Font(italic=True, color="6B7B88")
        ws.freeze_panes = "A2"
    L = wb.create_sheet("Lists"); col = [1]; ref = {}
    def put(title, vals, key=None):
        c = L.cell(1, col[0], title); c.font = Font(bold=True)
        for i, v in enumerate(vals, 2): L.cell(i, col[0], v)
        if key: ref[key] = f"Lists!${c.column_letter}$2:${c.column_letter}${len(vals) + 1}"
        col[0] += 1
    for k, v in LISTS.items(): put(k, v, k)
    put("stream_type", [x["id"] for x in st], "stream_type"); put("stream_type_fa", [x["fa"] for x in st]); put("parameter", [x["id"] for x in pa], "parameter"); put("parameter_unit", [x["unit"] for x in pa])
    put("equipment_code", [e[0] for e in eq], "equipment"); put("equipment_fa", [e[1] for e in eq]); put("equipment_en", [e[2] for e in eq]); put("system", [e[3] for e in eq])
    for sh, ck, rk in (("Nodes","kind","kind"),("Nodes","consumption_class","consumption_class"),("Nodes","equipment_code","equipment"),("Streams","stream_type","stream_type"),("Streams","recycle_status","recycle_status"),
                       ("Meters","parameter","parameter"),("Meters","method","method"),("Readings","granularity","granularity"),("Readings","quality","quality"),("Site","status","status"),("Site","calendar","calendar"),("Site","is_sample","yesno")):
        L_ = wb[sh].cell(1, [c[0] for c in SPEC[sh]].index(ck) + 1).column_letter
        dv = DataValidation(type="list", formula1="=" + ref[rk], allow_blank=True, showErrorMessage=False); dv.add(f"{L_}4:{L_}2000"); wb[sh].add_data_validation(dv)
    wb.save(path)
workbook(OUT / "Auditra-DataTemplate.xlsx", None); workbook(OUT / "Sample-TrainingPlant.xlsx", SAMPLE)
print("templates written")
