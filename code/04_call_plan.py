"""
04_call_plan.py
----------------
Module 2: Call Plan Optimization.

Business question: "Given limited rep time, how many visits ('calls')
should each HCP get per quarter to maximize reach to our highest-value
prescribers?"

Approach:
1. Assign each HCP to a simulated rep based on state (territory = state,
   grouped into rep books of ~120-160 HCPs, mirroring real territory sizes).
2. Set a target call frequency per tier (Champion visited most often).
3. Given each rep's fixed capacity (calls/quarter), allocate visits
   greedily by tier priority, then by within-tier opportunity score,
   so capacity-constrained reps still cover their highest-value HCPs first.
4. Report planned coverage vs. capacity, and flag reps whose Champion/
   Growth HCPs are under-covered due to territory overload.
"""
import sqlite3
import pandas as pd
import numpy as np

DB_PATH = "/home/claude/procdna_project/data/pharma_analytics.db"
np.random.seed(42)

conn = sqlite3.connect(DB_PATH)
hcp = pd.read_sql("SELECT * FROM hcp_segmented", conn)
conn.close()

# --- 1. Assign reps: ~1 rep per 130 HCPs within a state, chained across small states ---
hcp = hcp.sort_values(["state", "npi"]).reset_index(drop=True)
REP_BOOK_SIZE = 130
hcp["rep_id"] = "REP-" + (hcp.index // REP_BOOK_SIZE + 1).astype(str).str.zfill(3)

# --- 2. Target call frequency (visits per quarter) by tier ---
TIER_TARGET_FREQ = {"Champion": 6, "Growth": 3, "Maintain": 1, "Low-Priority": 0}
hcp["target_calls_per_qtr"] = hcp["tier"].map(TIER_TARGET_FREQ)

# --- 3. Opportunity score for within-tier prioritization ---
hcp["opportunity_score"] = hcp["total_claims_all_drugs"] * (1 + hcp["our_brand_share"])

# --- 4. Rep capacity: 200 calls/quarter (assumes ~8 calls/day x 5 days/wk x 5 wks/qtr,
#     net of admin time) — set deliberately tight so the allocation logic has to make
#     real tradeoffs, which is the point of "optimization" rather than a fully-slack plan.
REP_CAPACITY_PER_QTR = 200

results = []
for rep_id, grp in hcp.groupby("rep_id"):
    grp = grp.sort_values(["tier", "opportunity_score"], ascending=[True, False]).copy()
    # tier is ordered categorical Champion < Growth < ... alphabetically won't work,
    # so sort using the explicit tier priority rank
    tier_rank = {"Champion": 0, "Growth": 1, "Maintain": 2, "Low-Priority": 3}
    grp["tier_rank"] = grp["tier"].map(tier_rank)
    grp = grp.sort_values(["tier_rank", "opportunity_score"], ascending=[True, False])

    remaining_capacity = REP_CAPACITY_PER_QTR
    allocated = []
    for _, row in grp.iterrows():
        wanted = row["target_calls_per_qtr"]
        given = min(wanted, remaining_capacity)
        remaining_capacity -= given
        allocated.append(given)
    grp["allocated_calls_per_qtr"] = allocated
    grp["coverage_pct"] = np.where(
        grp["target_calls_per_qtr"] > 0,
        (grp["allocated_calls_per_qtr"] / grp["target_calls_per_qtr"] * 100).round(1),
        np.nan,
    )
    results.append(grp)

call_plan = pd.concat(results, ignore_index=True)

# --- Rep-level rollup ---
rep_summary = call_plan.groupby("rep_id").agg(
    n_hcps=("npi", "count"),
    total_target_calls=("target_calls_per_qtr", "sum"),
    total_allocated_calls=("allocated_calls_per_qtr", "sum"),
    champion_hcps=("tier", lambda s: (s == "Champion").sum()),
    champion_coverage_pct=("coverage_pct", lambda s: s[call_plan.loc[s.index, "tier"] == "Champion"].mean()),
).round(1)
rep_summary["capacity_utilization_pct"] = (
    rep_summary["total_allocated_calls"] / REP_CAPACITY_PER_QTR * 100
).round(1)

print("=== Call Plan: Rep-Level Summary (first 10 reps) ===")
print(rep_summary.head(10))

print("\n=== Tier-Level Coverage ===")
tier_coverage = call_plan.groupby("tier", observed=True).agg(
    n_hcps=("npi", "count"),
    avg_target_calls=("target_calls_per_qtr", "mean"),
    avg_allocated_calls=("allocated_calls_per_qtr", "mean"),
    avg_coverage_pct=("coverage_pct", "mean"),
).round(2)
print(tier_coverage)

under_covered_reps = rep_summary[rep_summary["champion_coverage_pct"] < 90]
print(f"\nReps with <90% Champion-tier coverage (territory overload flag): {len(under_covered_reps)} of {len(rep_summary)}")

call_plan.to_csv("/home/claude/procdna_project/data/call_plan.csv", index=False)
conn = sqlite3.connect(DB_PATH)
call_plan.to_sql("call_plan", conn, if_exists="replace", index=False)
rep_summary.reset_index().to_sql("rep_summary", conn, if_exists="replace", index=False)
conn.close()
print("\nSaved call_plan.csv, call_plan & rep_summary SQL tables.")
