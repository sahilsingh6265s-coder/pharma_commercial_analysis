# US Pharma Commercial Analytics Suite
### HCP Targeting, Call Planning, Incentive Design & Marketing Mix for a Simulated Diabetes Brand

**Built for**: procdna Business Analyst application
**Stack**: SQL (SQLite) → Python (pandas, scikit-learn) → Excel (openpyxl, live formulas) → Interactive dashboard (HTML/Chart.js)

---

## 1. Business Problem

A pharma client is launching/growing a Type 2 Diabetes brand ("Glucotrol Advance") in a
crowded category with ~5,000 prescribers, 39 sales territories, and a fixed marketing
budget. The commercial ops question, broken into the four workstreams named in the
procdna Business Analyst JD:

1. **Segmentation** — Which prescribers matter most?
2. **Call Planning** — Given limited rep time, who gets visited, and how often?
3. **Incentive Compensation** — Are rep quotas and bonus payouts fair?
4. **Marketing Mix** — Beyond rep visits, which promotional channels are worth the spend?

## 2. Data

Real CMS **Medicare Part D Prescribers – by Provider and Drug** Public Use File schema
(NPI, specialty, state, drug name, brand/generic, total claims, total drug cost, day
supply, beneficiary count) was replicated with a synthetic generator that preserves the
real-world statistical shape of the data — a Pareto/power-law prescriber-volume
distribution, specialty-driven prescribing propensity, and CMS's own low-count
suppression rule (<11 claims excluded). **The downstream pipeline (SQL → segmentation →
call plan → IC → marketing mix) requires zero changes to run on the real CMS CSV** —
only the input file swaps.

## 3. Methodology by Module

### Module 1 — HCP Segmentation (SQL + Python/scikit-learn)
- SQL aggregates provider-and-drug-level claims into one row per prescriber: total
  volume, brand-vs-generic mix, and our-brand market share.
- K-means (k=4) clusters on volume, our-brand share, and brand-mix %, then clusters are
  ranked into business tiers: **Champion, Growth, Maintain, Low-Priority**.
- **Finding**: Champions are 0.4% of HCPs but drive 11.9% of brand volume; combined with
  Growth (36.9% of HCPs), the top two tiers drive 93.6% of volume — a classic Pareto
  pattern that justifies concentrated rep effort.

### Module 2 — Call Plan Optimization (Python)
- HCPs assigned to 39 simulated territories (~130 HCPs/rep).
- Target visit frequency set by tier (Champion 6/qtr → Low-Priority 0/qtr).
- Under a deliberately tight capacity (200 calls/rep/qtr), a priority-ranked greedy
  allocation protects Champion and Growth coverage at 100% and lets the shortfall land on
  the Maintain tier (89.6% coverage) — a capacity-honest plan rather than one that assumes
  unlimited rep time.

### Module 3 — Incentive Compensation Analysis (Python + Excel)
- Quotas set proportional to territory potential (current our-brand volume) × a 12%
  growth target — not flat quotas, so territory size doesn't automatically inflate or
  deflate a rep's target.
- A 3-tier payout curve (Threshold 90% / Target 100% / Excellence 120%+, capped at 125%
  of target bonus) is applied to simulated attainment.
- **Fairness diagnostic**: correlation between territory potential and attainment is
  **0.22** — close enough to zero that quotas are reasonably difficulty-adjusted. Five
  reps are flagged (3 over-, 2 under-incentivized relative to territory difficulty) for a
  1:1 review.
- Delivered as a **live-formula Excel model** (`IC_Quota_Payout_Model.xlsx`) — quota,
  attainment %, payout %, and fairness flags recalculate automatically if actual claims or
  assumptions change (growth target, bonus size, payout curve breakpoints all sit on a
  separate Assumptions tab).

### Module 4 — Marketing Mix / Channel Effectiveness (Python/scikit-learn)
- Simulated channel exposure (email opens, digital ad impressions, congress attendance)
  correlated with tier, mirroring how real commercial teams over-index promotion on
  higher-value HCPs.
- Standardized multiple linear regression of Rx-lift on rep calls + 3 non-personal
  channels (R² = 0.42).
- **Finding**: Email and Congress/Conference exposure have the largest standardized
  effect on Rx-lift; Digital Ads show the weakest marginal effect (diminishing returns).
  Suggested reallocation: shift ~33 percentage points of budget share away from digital
  toward email and congress presence.

## 4. Deliverables

| File | What it is |
|---|---|
| `part_d_prescribers_by_provider_drug.csv` | Synthetic raw data, real CMS schema |
| `02_segmentation_base.sql` | SQL aggregation query (business logic layer) |
| `03_segmentation.py` … `06_marketing_mix.py` | Python modules for each workstream |
| `IC_Quota_Payout_Model.xlsx` | Live-formula Excel IC model (Assumptions / Rep IC Model / Diagnostics tabs) |
| `Commercial_Analytics_Dashboard.html` | Interactive 4-module BI-style dashboard |
| This README | Case study write-up |

## 5. Assumptions & Limitations (state these openly in an interview)

- Data is **synthetic**, built to the real CMS schema and real statistical patterns —
  chosen because the actual CMS file requires a direct download and is 25M+ rows; the
  synthetic version keeps the project reproducible and fast to iterate on, while every
  query/model is written to run unchanged against the real file.
- Call activity, quota attainment, and marketing exposure are **simulated** — no real
  CRM/call-activity or marketing-spend data is public, so this layer demonstrates the
  *method* (allocation logic, fairness diagnostics, regression approach) rather than
  real client numbers.
- Rep capacity (200 calls/qtr), bonus size ($15,000/qtr), and payout curve breakpoints
  are illustrative, standard pharma commercial-model assumptions, documented in the Excel
  Assumptions tab and in each Python module's docstring — not claimed as any real client's
  actual figures.

## 6. How to Extend

- Swap the synthetic CSV for the real CMS download — same column names, zero code changes.
- Replace simulated call/marketing data with real CRM/Veeva or marketing-automation exports.
- Move the SQL layer from SQLite to the client's actual warehouse (Snowflake/Redshift) —
  the aggregation query is standard ANSI SQL.
- Swap the HTML dashboard for Power BI/Tableau, pointing at the same `hcp_segmented`,
  `call_plan`, `incentive_comp`, and `marketing_mix` tables.
