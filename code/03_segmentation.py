"""
03_segmentation.py
-------------------
Module 1: HCP Segmentation.

Business question: "Which of our ~5,000 prescribers should sales reps
prioritize for our Type 2 Diabetes brand (Glucotrol Advance)?"

Approach: K-means on three normalized features per prescriber -
  1. total_claims_all_drugs   -> overall prescribing volume (size of opportunity)
  2. our_brand_share          -> how loyal they already are to our brand
  3. brand_mix_pct            -> brand-vs-generic prescribing tendency (openness to branded Rx)
Clusters are then ranked by (volume x brand_mix) into business-readable
tiers: Champion, Growth, Maintain, Low-Priority.
"""
import sqlite3
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

DB_PATH = "/home/claude/procdna_project/data/pharma_analytics.db"

conn = sqlite3.connect(DB_PATH)
hcp = pd.read_sql("SELECT * FROM hcp_base", conn)
conn.close()

hcp = hcp.dropna(subset=["total_claims_all_drugs", "our_brand_share", "brand_mix_pct"]).copy()

features = ["total_claims_all_drugs", "our_brand_share", "brand_mix_pct"]
X = hcp[features].fillna(0)
X_scaled = StandardScaler().fit_transform(X)

kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
hcp["cluster"] = kmeans.fit_predict(X_scaled)

# Rank clusters by a business "opportunity score" = volume * (1 + our_brand_share)
# so we can label them meaningfully rather than by arbitrary cluster id
cluster_score = (
    hcp.groupby("cluster")
    .apply(lambda d: (d["total_claims_all_drugs"] * (1 + d["our_brand_share"])).mean())
    .sort_values(ascending=False)
)
tier_labels = ["Champion", "Growth", "Maintain", "Low-Priority"]
cluster_to_tier = {cluster_id: tier_labels[i] for i, cluster_id in enumerate(cluster_score.index)}
hcp["tier"] = hcp["cluster"].map(cluster_to_tier)

tier_order = pd.CategoricalDtype(categories=tier_labels, ordered=True)
hcp["tier"] = hcp["tier"].astype(tier_order)

summary = hcp.groupby("tier", observed=True).agg(
    n_hcps=("npi", "count"),
    avg_total_claims=("total_claims_all_drugs", "mean"),
    avg_our_brand_share=("our_brand_share", "mean"),
    total_our_brand_claims=("our_brand_claims", "sum"),
).round(2)
summary["pct_of_hcps"] = (summary["n_hcps"] / summary["n_hcps"].sum() * 100).round(1)
summary["pct_of_our_brand_volume"] = (
    summary["total_our_brand_claims"] / summary["total_our_brand_claims"].sum() * 100
).round(1)

print(summary)

hcp.to_csv("/home/claude/procdna_project/data/hcp_segmented.csv", index=False)

conn = sqlite3.connect(DB_PATH)
hcp.to_sql("hcp_segmented", conn, if_exists="replace", index=False)
conn.close()

print("\nSaved hcp_segmented.csv and hcp_segmented SQL table.")
