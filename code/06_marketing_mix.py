"""
06_marketing_mix.py
--------------------
Module 4: Marketing Mix / Channel Effectiveness.

Business question: "Beyond rep calls, which non-personal promotion
channels (email, digital/banner ads, conference/congress presence)
actually move prescribing, and how should we allocate next quarter's
marketing budget across them?"

Approach:
1. Simulate quarterly channel spend/exposure per HCP (email opens,
   digital ad impressions, conference exposure) correlated with tier
   (Champions get more marketing attention, as they do in real
   commercial models) plus noise.
2. Simulate incremental Rx lift as a function of rep calls (from
   Module 2) + channel exposures + tier baseline, with realistic
   diminishing returns and some pure noise (not everything is
   marketing-driven).
3. Fit a multiple linear regression of Rx lift on calls + channels to
   estimate each channel's marginal contribution ("ROI").
4. Rank channels by standardized coefficient to guide budget allocation.
"""
import sqlite3
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

DB_PATH = "/home/claude/procdna_project/data/pharma_analytics.db"
np.random.seed(21)

conn = sqlite3.connect(DB_PATH)
call_plan = pd.read_sql("SELECT npi, tier, allocated_calls_per_qtr, our_brand_claims, opportunity_score FROM call_plan", conn)
conn.close()

df = call_plan.copy()
tier_multiplier = {"Champion": 3.0, "Growth": 1.6, "Maintain": 1.0, "Low-Priority": 0.5}
df["tier_mult"] = df["tier"].map(tier_multiplier)

# Simulated channel exposure per HCP this quarter (spend proxies)
df["email_opens"] = (np.random.poisson(4, len(df)) * df["tier_mult"]).round(0)
df["digital_ad_impressions"] = (np.random.poisson(120, len(df)) * df["tier_mult"]).round(0)
df["congress_exposure"] = np.random.binomial(1, 0.15 * df["tier_mult"].clip(upper=1) + 0.05, len(df))

# Simulated incremental Rx lift: calls matter most, email has modest effect,
# digital has small effect with diminishing returns (log), congress has a
# meaningful one-time bump if attended. Plus noise.
df["rx_lift"] = (
    2.2 * df["allocated_calls_per_qtr"]
    + 1.1 * df["email_opens"]
    + 0.35 * np.log1p(df["digital_ad_impressions"])
    + 9.0 * df["congress_exposure"]
    + np.random.normal(0, 8, len(df))
).clip(lower=0).round(1)

# --- Regression ---
features = ["allocated_calls_per_qtr", "email_opens", "digital_ad_impressions", "congress_exposure"]
X = df[features]
y = df["rx_lift"]

X_scaled = StandardScaler().fit_transform(X)  # standardize so coefficients are comparable "importance"
model = LinearRegression()
model.fit(X_scaled, y)

coef_df = pd.DataFrame({
    "channel": ["Rep Calls", "Email", "Digital Ads (log impressions)", "Congress/Conference"],
    "standardized_coefficient": model.coef_.round(2),
    "raw_coefficient": LinearRegression().fit(X, y).coef_.round(3),
}).sort_values("standardized_coefficient", ascending=False)

r2 = model.score(X_scaled, y)

print(f"Model R^2: {r2:.3f}  (share of Rx-lift variance explained by these 4 channels)\n")
print("=== Channel Effectiveness Ranking (by standardized coefficient) ===")
print(coef_df.to_string(index=False))

total_std_coef = coef_df["standardized_coefficient"].clip(lower=0).sum()
coef_df["suggested_budget_share_pct"] = (
    coef_df["standardized_coefficient"].clip(lower=0) / total_std_coef * 100
).round(1)
print("\n=== Suggested Relative Budget Allocation ===")
print(coef_df[["channel", "suggested_budget_share_pct"]].to_string(index=False))

df.to_csv("/home/claude/procdna_project/data/marketing_mix.csv", index=False)
coef_df.to_csv("/home/claude/procdna_project/data/marketing_mix_channel_ranking.csv", index=False)
conn = sqlite3.connect(DB_PATH)
df.to_sql("marketing_mix", conn, if_exists="replace", index=False)
conn.close()
print("\nSaved marketing_mix.csv, marketing_mix_channel_ranking.csv, and SQL table.")
