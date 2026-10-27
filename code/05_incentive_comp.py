"""
05_incentive_comp.py
---------------------
Module 3: Incentive Compensation (IC) Analysis.

Business question: "Are rep quotas fair, and is our bonus payout
structure rewarding performance rather than territory luck?"

Approach:
1. Territory potential = sum of our-brand claims currently written in
   that rep's book (a proxy for market opportunity).
2. Set quota proportional to territory potential (fair quotas), not a
   flat number across all reps.
3. Simulate "actual" quarterly performance with some execution noise
   (skill/effort varies rep to rep, not just territory).
4. Apply a standard 3-tier payout curve: Threshold (90% attainment) /
   Target (100%) / Excellence (120%+).
5. Flag reps who are over- or under-incentivized relative to a
   difficulty-adjusted view (i.e., quota attainment vs. territory
   potential, not just raw attainment).
"""
import sqlite3
import pandas as pd
import numpy as np

DB_PATH = "/home/claude/procdna_project/data/pharma_analytics.db"
np.random.seed(7)

conn = sqlite3.connect(DB_PATH)
call_plan = pd.read_sql("SELECT * FROM call_plan", conn)
conn.close()

rep_potential = call_plan.groupby("rep_id").agg(
    n_hcps=("npi", "count"),
    territory_potential=("our_brand_claims", "sum"),       # current our-brand volume in book
    market_opportunity=("total_claims_all_drugs", "sum"),  # total category volume in book
).reset_index()

# --- Fair quota: proportional to territory potential, normalized to a
#     company-wide average quota so total quota = total historical volume x growth target
GROWTH_TARGET = 1.12  # company wants 12% YoY brand growth
company_avg_potential = rep_potential["territory_potential"].mean()
rep_potential["quota"] = (rep_potential["territory_potential"] * GROWTH_TARGET).round(0)
# floor for tiny territories so nobody has a near-zero quota
rep_potential["quota"] = rep_potential["quota"].clip(lower=company_avg_potential * 0.3).round(0)

# --- Simulated actual performance: territory potential x execution factor (skill/effort noise) ---
rep_potential["execution_factor"] = np.random.normal(1.0, 0.15, size=len(rep_potential)).clip(0.6, 1.5)
rep_potential["actual_claims"] = (rep_potential["territory_potential"] * rep_potential["execution_factor"] * GROWTH_TARGET).round(0)
rep_potential["attainment_pct"] = (rep_potential["actual_claims"] / rep_potential["quota"] * 100).round(1)

# --- Payout curve ---
def payout_pct(attainment):
    if attainment < 90:
        return 0.0
    elif attainment < 100:
        return 50.0 + (attainment - 90) * 2.5     # 50%-75% of target bonus, ramping
    elif attainment < 120:
        return 75.0 + (attainment - 100) * 1.25   # 75%-100%+ ramping to cap
    else:
        return 125.0  # capped excellence payout

BASE_BONUS = 15000  # illustrative quarterly bonus target ($), documented assumption
rep_potential["payout_pct_of_target_bonus"] = rep_potential["attainment_pct"].apply(payout_pct)
rep_potential["bonus_payout"] = (rep_potential["payout_pct_of_target_bonus"] / 100 * BASE_BONUS).round(0)

# --- Fairness diagnostic: correlation between territory potential and attainment.
#     A strong POSITIVE correlation would suggest reps in bigger territories attain
#     more easily regardless of skill -- a sign quotas aren't fully potential-adjusted.
corr = rep_potential["territory_potential"].corr(rep_potential["attainment_pct"])

# Flag reps: high potential + low attainment (under-performing despite easy territory)
# vs. low potential + high attainment (over-performing despite hard territory - reward/retain)
median_potential = rep_potential["territory_potential"].median()
rep_potential["flag"] = np.select(
    [
        (rep_potential["territory_potential"] >= median_potential) & (rep_potential["attainment_pct"] < 90),
        (rep_potential["territory_potential"] < median_potential) & (rep_potential["attainment_pct"] >= 110),
    ],
    ["Underperforming (easy territory)", "High performer (hard territory)"],
    default="Normal",
)

print(f"Correlation between territory potential and attainment %: {corr:.2f}")
print(f"(Near 0 = quotas are well difficulty-adjusted; strongly positive = quotas favor big territories)\n")

print("=== IC Summary (first 10 reps) ===")
print(rep_potential[["rep_id", "n_hcps", "territory_potential", "quota", "actual_claims",
                       "attainment_pct", "payout_pct_of_target_bonus", "bonus_payout", "flag"]].head(10))

print("\n=== Flag distribution ===")
print(rep_potential["flag"].value_counts())

print(f"\nTotal simulated quarterly bonus payout across {len(rep_potential)} reps: ${rep_potential['bonus_payout'].sum():,.0f}")

rep_potential.to_csv("/home/claude/procdna_project/data/incentive_comp.csv", index=False)
conn = sqlite3.connect(DB_PATH)
rep_potential.to_sql("incentive_comp", conn, if_exists="replace", index=False)
conn.close()
print("\nSaved incentive_comp.csv and SQL table.")
