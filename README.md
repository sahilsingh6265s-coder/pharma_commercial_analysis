# Pharma Commercial Analytics Suite

A simulated commercial analytics case study for a Type 2 diabetes brand. The project follows a prescriber dataset through four business workstreams: **HCP segmentation, sales call planning, incentive compensation, and marketing-channel analysis**. It includes Python and SQL analysis, a spreadsheet model, and an interactive dashboard.

> **Important:** This is a demonstration built with synthetic data and illustrative commercial assumptions. It does not contain real patient or prescriber activity, and its findings should not be treated as evidence of actual product or channel effectiveness.

## Contents

- [Business problem](#business-problem)
- [End-to-end workflow](#end-to-end-workflow)
- [Included deliverables](#included-deliverables)
- [Data dictionary](#data-dictionary)
- [View the dashboard and Excel model](#view-the-dashboard-and-excel-model)
- [Reproduce the analysis](#reproduce-the-analysis)
- [Project structure](#project-structure)
- [Assumptions and limitations](#assumptions-and-limitations)
- [Possible extensions](#possible-extensions)

## Business problem

The case study explores how a commercial team might organize its work for a fictional Type 2 diabetes brand, **Glucotrol Advance**:

1. Which healthcare professionals (HCPs) represent the greatest opportunity?
2. How should limited sales-representative capacity be allocated across those HCPs?
3. How can quotas and incentive payouts account for differences in territory potential?
4. How might a team compare personal promotion with non-personal marketing channels?

The data is synthetic, but its raw prescriber file follows a CMS Medicare Part D prescriber-by-drug-style schema. The results demonstrate analysis methods; they do not represent real market performance.

## End-to-end workflow

```text
Synthetic prescriber-drug data
              |
              v
      SQL aggregation (hcp_base)
              |
              v
     HCP segmentation (tiers)
              |
              v
       Quarterly call plan
          /           \
         v             v
 Incentive model    Marketing mix
      |                  |
      v                  v
 Excel workbook    Channel ranking
          \           /
           v         v
       Interactive dashboard
```

### 1. Generate the source data

`code/01_generate_data.py` creates prescriber-and-drug rows with synthetic NPI-like identifiers, specialty, state, drug, claims, cost, day supply, and beneficiary count. It simulates a skewed prescriber-volume distribution and applies a low-claim suppression rule.

**Output:** `data/part_d_prescribers_by_provider_drug.csv`

### 2. Aggregate claims with SQL

`code/02_run_sql.py` loads the raw CSV into SQLite and runs `code/02_segmentation_base.sql`. The SQL groups the drug-level rows into one row per HCP and calculates category claims, brand and generic claims, target-brand claims, brand mix, and target-brand share.

**Output:** the SQLite `hcp_base` table, which is the analytical starting point for segmentation.

### 3. Segment HCPs

`code/03_segmentation.py` standardizes category volume, target-brand share, and brand mix, then clusters HCPs with K-means (`k=4`). It ranks the resulting clusters by a business opportunity score and assigns readable tiers: **Champion, Growth, Maintain, and Low-Priority**.

**Outputs:** `data/hcp_segmented.csv` and the SQLite `hcp_segmented` table.

### 4. Allocate the call plan

`code/04_call_plan.py` assigns HCPs to simulated rep books of about 130 HCPs, sets a quarterly target frequency by tier, and allocates visits in tier-priority and opportunity-score order. The model caps each rep at 200 calls per quarter, so lower-priority coverage can be reduced when capacity runs out.

**Outputs:** `data/call_plan.csv`, plus `call_plan` and `rep_summary` SQLite tables.

### 5. Model incentive compensation

`code/05_incentive_comp.py` estimates territory potential from current target-brand claims, calculates quotas using a 12% growth assumption, and simulates performance with execution variability. It then applies an illustrative threshold/target/excellence payout curve, capped at 125% of target bonus, and flags selected territory/attainment combinations for review.

**Outputs:** `data/incentive_comp.csv` and the SQLite `incentive_comp` table.

`code/07_build_excel_ic_model.py` uses that CSV to build an Excel workbook with an **Assumptions** sheet, a formula-driven **Rep IC Model**, and a **Diagnostics** sheet.

**Output:** `IC_Quota_Payout_Model.xlsx`

### 6. Compare marketing channels

`code/06_marketing_mix.py` simulates email, digital-ad, and congress exposure alongside rep calls. It generates illustrative Rx lift, fits a linear regression, and ranks channels using standardized coefficients. The resulting suggested channel shares are a relative allocation derived from this simulation—not measured return on investment or causal evidence.

**Outputs:** `data/marketing_mix.csv`, `data/marketing_mix_channel_ranking.csv`, and the SQLite `marketing_mix` table.

### 7. Explore the results

`Commercial_Analytics_Dashboard.html` presents a browser-based overview of the four workstreams. It loads Chart.js from a CDN, so an internet connection is needed for the charts. The dashboard is a supplied project artifact; it is not automatically refreshed by running the analysis scripts.

## Included deliverables

| File | Purpose |
|---|---|
| `Commercial_Analytics_Dashboard.html` | Interactive, browser-viewable case-study dashboard |
| `IC_Quota_Payout_Model.xlsx` | Incentive-compensation workbook with assumptions, formulas, and diagnostics |
| `data/part_d_prescribers_by_provider_drug.csv` | Synthetic source data using a CMS-style prescriber-by-drug schema |
| `data/hcp_segmented.csv` | HCP-level metrics and assigned segment tiers |
| `data/call_plan.csv` | HCP-level quarterly target and allocated calls |
| `data/incentive_comp.csv` | Simulated rep-level quota, attainment, payout, and flag data |
| `data/marketing_mix.csv` | Simulated HCP channel exposures and Rx lift |
| `data/marketing_mix_channel_ranking.csv` | Regression coefficients and suggested relative channel shares |
| `code/01_generate_data.py`–`code/07_build_excel_ic_model.py` | Data generation, analysis, and Excel-building scripts |
| `code/02_segmentation_base.sql` | SQL aggregation from drug-level claims to HCP-level metrics |

## Data dictionary

### Source claims file

`part_d_prescribers_by_provider_drug.csv` has one record per simulated prescriber and drug. Important fields include:

| Field | Meaning |
|---|---|
| `npi` | Synthetic prescriber identifier |
| `specialty`, `state` | Simulated HCP attributes |
| `drug_name`, `drug_type` | Drug and Brand/Generic classification |
| `total_claims`, `total_drug_cost` | Simulated claims and cost |
| `total_day_supply`, `beneficiary_count` | Simulated utilization measures |

### Derived files

- `hcp_segmented.csv` adds aggregated claims and mix measures, cluster ID, and business tier.
- `call_plan.csv` adds rep assignment, target frequency, opportunity score, allocated calls, and coverage.
- `incentive_comp.csv` contains one row per simulated rep with territory potential, quota, simulated actual claims, attainment, payout, and review flag.
- `marketing_mix.csv` contains simulated channel exposures and response data; `marketing_mix_channel_ranking.csv` summarizes the model's channel ranking.

## View the dashboard and Excel model

Open `Commercial_Analytics_Dashboard.html` in a browser to view the dashboard. The page loads Chart.js from the internet.

Open `IC_Quota_Payout_Model.xlsx` in Excel or another compatible spreadsheet application to inspect the assumptions, rep-level formulas, and diagnostics. Spreadsheet applications may calculate formulas when the workbook is opened.

## Reproduce the analysis

The intended analysis order is:

```text
01_generate_data.py
02_run_sql.py
03_segmentation.py
04_call_plan.py
05_incentive_comp.py
06_marketing_mix.py
07_build_excel_ic_model.py
```

The scripts use Python with `pandas`, `numpy`, `scikit-learn`, and `openpyxl`; SQLite is included in Python's standard library. However, **the scripts are not currently portable or runnable from this extracted folder without path updates**:

- Data and database paths are hard-coded to `/home/claude/procdna_project/...`, rather than paths relative to the project.
- `02_run_sql.py` looks for the SQL file under a `sql/` directory, while this archive contains it under `code/`.
- The Excel builder writes to an `outputs/` directory that is not included in the archive.

The CSVs, workbook, and dashboard listed above are already included for review. Before regenerating them, update the scripts to resolve paths relative to the project root (or configure a project-root setting), point the SQL loader to `code/02_segmentation_base.sql`, and create the Excel output directory. No automated test suite is included.

## Project structure

```text
.
├── README.md
├── Commercial_Analytics_Dashboard.html
├── IC_Quota_Payout_Model.xlsx
├── code/
│   ├── 01_generate_data.py
│   ├── 02_run_sql.py
│   ├── 02_segmentation_base.sql
│   ├── 03_segmentation.py
│   ├── 04_call_plan.py
│   ├── 05_incentive_comp.py
│   ├── 06_marketing_mix.py
│   └── 07_build_excel_ic_model.py
└── data/
    ├── part_d_prescribers_by_provider_drug.csv
    ├── hcp_segmented.csv
    ├── call_plan.csv
    ├── incentive_comp.csv
    ├── marketing_mix.csv
    └── marketing_mix_channel_ranking.csv
```

## Assumptions and limitations

- All included prescriber, claim, territory, activity, performance, and marketing data is **synthetic**. NPI-like identifiers do not identify real clinicians.
- Call frequency by tier, rep capacity (200 calls per quarter), quota growth target (12%), target bonus ($15,000 per quarter), payout thresholds, and channel-response relationships are illustrative assumptions.
- Rep assignments are generated from sorted HCP rows in fixed-size books; they are not modeled geographic territories.
- The segmentation uses a fixed four-cluster K-means model. Cluster labels are assigned afterward using an opportunity score; the cluster numbers themselves have no business meaning.
- The marketing exposures and Rx lift are generated by the script before regression. The model therefore demonstrates an analytical workflow on simulated data; it does not establish causal channel impact.
- The dashboard is a supplied HTML artifact and is not wired to refresh from the CSVs or SQLite database.
- The analysis scripts contain machine-specific absolute paths and need path configuration before they can be rerun in a different environment.

## Possible extensions

- Replace synthetic claims with a licensed, appropriately prepared CMS extract and document its refresh process.
- Make data, database, SQL, and output paths configurable and relative to the project root.
- Use real CRM and marketing exposure data with suitable privacy and governance controls.
- Add validation for input schemas, missing data, model outputs, call-capacity constraints, and quota calculations.
- Connect the dashboard to generated outputs and automate its refresh.
- Compare segmentation approaches and evaluate the stability and business usefulness of their tiers.
- Test channel effectiveness with an appropriate causal design instead of interpreting simulated regression coefficients as ROI.
