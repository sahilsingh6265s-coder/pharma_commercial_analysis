"""
02_run_sql.py
-------------
Loads the raw prescriber-drug CSV into SQLite (standing in for the
client's data warehouse) and runs the SQL aggregation that builds
hcp_base — one row per prescriber with the volume/mix metrics that
feed segmentation.
"""
import sqlite3
import pandas as pd

DB_PATH = "/home/claude/procdna_project/data/pharma_analytics.db"

df = pd.read_csv("/home/claude/procdna_project/data/part_d_prescribers_by_provider_drug.csv")

conn = sqlite3.connect(DB_PATH)
df.to_sql("part_d_claims", conn, if_exists="replace", index=False)

with open("/home/claude/procdna_project/sql/02_segmentation_base.sql") as f:
    sql_script = f.read()

cur = conn.cursor()
cur.executescript(sql_script.split("-- Quick sanity checks")[0])
conn.commit()

check = pd.read_sql("SELECT COUNT(*) AS n_prescribers FROM hcp_base", conn)
print("hcp_base rows:", check.iloc[0, 0])

by_spec = pd.read_sql(
    "SELECT specialty, COUNT(*) AS n, ROUND(AVG(total_claims_all_drugs),1) AS avg_claims "
    "FROM hcp_base GROUP BY specialty ORDER BY avg_claims DESC", conn)
print(by_spec)

conn.close()
