-- 02_segmentation_base.sql
-- Business question: "Which prescribers should we prioritize for our
-- Type 2 Diabetes brand portfolio?"
-- Aggregates raw provider-and-drug level claims into one row per
-- prescriber with the metrics segmentation needs: total volume,
-- brand vs generic mix, and market share of our brand vs competitors.

DROP TABLE IF EXISTS hcp_base;

CREATE TABLE hcp_base AS
WITH prescriber_totals AS (
    SELECT
        npi,
        specialty,
        state,
        SUM(total_claims)                                   AS total_claims_all_drugs,
        SUM(total_drug_cost)                                 AS total_cost_all_drugs,
        SUM(beneficiary_count)                                AS total_beneficiaries,
        SUM(CASE WHEN drug_type = 'Brand' THEN total_claims ELSE 0 END)   AS brand_claims,
        SUM(CASE WHEN drug_type = 'Generic' THEN total_claims ELSE 0 END) AS generic_claims,
        -- "our" target brand = Glucotrol Advance
        SUM(CASE WHEN drug_name = 'Glucotrol Advance' THEN total_claims ELSE 0 END) AS our_brand_claims,
        COUNT(DISTINCT drug_name)                              AS distinct_drugs_written
    FROM part_d_claims
    GROUP BY npi, specialty, state
)
SELECT
    npi,
    specialty,
    state,
    total_claims_all_drugs,
    total_cost_all_drugs,
    total_beneficiaries,
    brand_claims,
    generic_claims,
    our_brand_claims,
    distinct_drugs_written,
    ROUND(1.0 * our_brand_claims / NULLIF(total_claims_all_drugs, 0), 3) AS our_brand_share,
    ROUND(1.0 * brand_claims / NULLIF(total_claims_all_drugs, 0), 3)     AS brand_mix_pct
FROM prescriber_totals;

-- Quick sanity checks
SELECT COUNT(*) AS n_prescribers FROM hcp_base;
SELECT specialty, COUNT(*) AS n, ROUND(AVG(total_claims_all_drugs),1) AS avg_claims
FROM hcp_base GROUP BY specialty ORDER BY avg_claims DESC;
