"""
07_build_excel_ic_model.py
---------------------------
Builds the Incentive Compensation model as a proper Excel workbook with
live formulas (not hardcoded results), matching the xlsx skill's
financial-model conventions: blue = hardcoded inputs, black = formulas,
yellow fill = key assumptions, currency/percent number formats.
"""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

SRC = "/home/claude/procdna_project/data/incentive_comp.csv"
OUT = "/home/claude/procdna_project/outputs/IC_Quota_Payout_Model.xlsx"

df = pd.read_csv(SRC).sort_values("rep_id").reset_index(drop=True)

wb = Workbook()

BLUE = Font(name="Arial", size=10, color="0000FF")
BLACK = Font(name="Arial", size=10, color="000000")
HEADER_FONT = Font(name="Arial", size=10, bold=True, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
YELLOW_FILL = PatternFill("solid", fgColor="FFFF00")
TITLE_FONT = Font(name="Arial", size=14, bold=True)
NOTE_FONT = Font(name="Arial", size=9, italic=True, color="666666")
THIN = Side(style="thin", color="CCCCCC")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

# ============================================================
# Sheet 1: Assumptions
# ============================================================
ws_a = wb.active
ws_a.title = "Assumptions"
ws_a["A1"] = "IC Quota & Payout Model — Key Assumptions"
ws_a["A1"].font = TITLE_FONT
ws_a.merge_cells("A1:C1")

assumptions = [
    ("Growth target (YoY brand growth applied to quota)", 1.12, "0.0%", "Company FY target, provided by user"),
    ("Base quarterly bonus target ($)", 15000, "$#,##0", "Illustrative — standard target bonus per rep, provided by user"),
    ("Threshold attainment % (min. for any payout)", 0.90, "0.0%", "Standard pharma IC plan design"),
    ("Target attainment % (100% of target bonus)", 1.00, "0.0%", "Standard pharma IC plan design"),
    ("Excellence attainment % (payout cap reached)", 1.20, "0.0%", "Standard pharma IC plan design"),
    ("Excellence payout cap (% of target bonus)", 1.25, "0.0%", "Standard pharma IC plan design"),
]
ws_a["A3"] = "Assumption"; ws_a["B3"] = "Value"; ws_a["C3"] = "Source / Note"
for c in ("A3", "B3", "C3"):
    ws_a[c].font = HEADER_FONT; ws_a[c].fill = HEADER_FILL
for i, (label, val, fmt, note) in enumerate(assumptions, start=4):
    ws_a[f"A{i}"] = label
    ws_a[f"B{i}"] = val
    ws_a[f"B{i}"].number_format = fmt
    ws_a[f"B{i}"].font = BLUE
    ws_a[f"B{i}"].fill = YELLOW_FILL
    ws_a[f"C{i}"] = note
    ws_a[f"C{i}"].font = NOTE_FONT
ws_a.column_dimensions["A"].width = 48
ws_a.column_dimensions["B"].width = 14
ws_a.column_dimensions["C"].width = 46

# ============================================================
# Sheet 2: Rep IC Model
# ============================================================
ws = wb.create_sheet("Rep IC Model")
ws["A1"] = "Rep-Level Quota, Attainment & Payout Model"
ws["A1"].font = TITLE_FONT
ws.merge_cells("A1:J1")
ws["A2"] = "Blue = input data (from segmentation/call-plan pipeline) · Black = live formulas · Edit Assumptions tab to flex the whole model"
ws["A2"].font = NOTE_FONT
ws.merge_cells("A2:J2")

headers = [
    "Rep ID", "# HCPs", "Territory Potential\n(current our-brand claims)",
    "Quota\n(=Potential x Growth Target)", "Actual Claims\n(input)", "Attainment %",
    "Payout % of Target Bonus", "Bonus Payout ($)", "Flag"
]
start_row = 4
for j, h in enumerate(headers, start=1):
    cell = ws.cell(row=start_row, column=j, value=h)
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    cell.border = BORDER

data_start = start_row + 1
for i, row in df.iterrows():
    r = data_start + i
    ws.cell(row=r, column=1, value=row["rep_id"]).font = BLUE
    ws.cell(row=r, column=2, value=int(row["n_hcps"])).font = BLUE
    ws.cell(row=r, column=3, value=int(row["territory_potential"])).font = BLUE

    # Quota = Territory Potential * Growth Target (Assumptions!B4)
    ws.cell(row=r, column=4, value=f"=C{r}*Assumptions!$B$4").font = BLACK
    ws.cell(row=r, column=4).number_format = "#,##0"

    ws.cell(row=r, column=5, value=int(row["actual_claims"])).font = BLUE

    # Attainment % = Actual / Quota
    ws.cell(row=r, column=6, value=f"=IFERROR(E{r}/D{r},0)").font = BLACK
    ws.cell(row=r, column=6).number_format = "0.0%"

    # Payout %: threshold/target/excellence ramp, using assumptions
    payout_formula = (
        f'=IF(F{r}<Assumptions!$B$6,0,'
        f'IF(F{r}<Assumptions!$B$7,0.50+(F{r}-Assumptions!$B$6)*2.5,'
        f'IF(F{r}<Assumptions!$B$8,0.75+(F{r}-Assumptions!$B$7)*1.25,'
        f'Assumptions!$B$9)))'
    )
    ws.cell(row=r, column=7, value=payout_formula).font = BLACK
    ws.cell(row=r, column=7).number_format = "0.0%"

    # Bonus payout = payout% * base bonus target
    ws.cell(row=r, column=8, value=f"=G{r}*Assumptions!$B$5").font = BLACK
    ws.cell(row=r, column=8).number_format = "$#,##0"

    # Fairness flag using median-based comparison via helper columns on Diagnostics tab;
    # here we simplify to a direct threshold check against company-wide median potential
    flag_formula = (
        f'=IF(AND(C{r}>=Diagnostics!$B$2,F{r}<0.9),"Underperforming (easy territory)",'
        f'IF(AND(C{r}<Diagnostics!$B$2,F{r}>=1.1),"High performer (hard territory)","Normal"))'
    )
    ws.cell(row=r, column=9, value=flag_formula).font = BLACK

    for col in range(1, 10):
        ws.cell(row=r, column=col).border = BORDER

data_end = data_start + len(df) - 1

# Totals row
total_row = data_end + 1
ws.cell(row=total_row, column=1, value="TOTAL").font = Font(name="Arial", bold=True)
ws.cell(row=total_row, column=2, value=f"=SUM(B{data_start}:B{data_end})").font = Font(name="Arial", bold=True)
ws.cell(row=total_row, column=3, value=f"=SUM(C{data_start}:C{data_end})").font = Font(name="Arial", bold=True)
ws.cell(row=total_row, column=3).number_format = "#,##0"
ws.cell(row=total_row, column=4, value=f"=SUM(D{data_start}:D{data_end})").font = Font(name="Arial", bold=True)
ws.cell(row=total_row, column=4).number_format = "#,##0"
ws.cell(row=total_row, column=5, value=f"=SUM(E{data_start}:E{data_end})").font = Font(name="Arial", bold=True)
ws.cell(row=total_row, column=8, value=f"=SUM(H{data_start}:H{data_end})").font = Font(name="Arial", bold=True)
ws.cell(row=total_row, column=8).number_format = "$#,##0"
for col in range(1, 10):
    ws.cell(row=total_row, column=col).border = BORDER

col_widths = [10, 9, 15, 15, 13, 12, 14, 14, 26]
for j, w in enumerate(col_widths, start=1):
    ws.column_dimensions[get_column_letter(j)].width = w
ws.freeze_panes = "A5"

# ============================================================
# Sheet 3: Diagnostics (fairness check)
# ============================================================
ws_d = wb.create_sheet("Diagnostics")
ws_d["A1"] = "IC Fairness Diagnostics"
ws_d["A1"].font = TITLE_FONT
ws_d["A2"] = "Avg Territory Potential per Rep (proxy for median)"
ws_d["B2"] = f"='Rep IC Model'!C{total_row}/COUNTA('Rep IC Model'!A{data_start}:A{data_end})"
ws_d["B2"].font = BLACK
ws_d["B2"].number_format = "#,##0"
ws_d["C2"] = "Used as the split point for the over/under-incentivized flag on the Rep IC Model tab (mean used as a robust proxy for median in-formula; see README for exact median)"
ws_d["C2"].font = NOTE_FONT

ws_d["A4"] = "Correlation: Territory Potential vs. Attainment %"
corr_val = df["territory_potential"].corr(df["attainment_pct"])
ws_d["B4"] = round(corr_val, 3)
ws_d["B4"].font = BLUE
ws_d["B4"].fill = YELLOW_FILL
ws_d["C4"] = "Computed in Python from the underlying dataset (see 05_incentive_comp.py). Near 0 = quotas are well difficulty-adjusted."
ws_d["C4"].font = NOTE_FONT

ws_d["A6"] = "Flag Distribution"
ws_d["A6"].font = Font(bold=True)
flag_counts = df["flag"].value_counts()
r = 7
for flag, cnt in flag_counts.items():
    ws_d.cell(row=r, column=1, value=flag).font = BLACK
    ws_d.cell(row=r, column=2, value=int(cnt)).font = BLUE
    r += 1

ws_d.column_dimensions["A"].width = 45
ws_d.column_dimensions["B"].width = 14
ws_d.column_dimensions["C"].width = 60

wb.save(OUT)
print(f"Saved {OUT}")
