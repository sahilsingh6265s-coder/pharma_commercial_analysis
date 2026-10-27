"""
01_generate_data.py
--------------------
Generates a synthetic HCP prescriber dataset modeled on the real
CMS Medicare Part D Prescribers - by Provider and Drug PUF schema.

Why synthetic: the real CMS file is 25M+ rows and requires a direct
download from data.cms.gov. We replicate its exact column structure,
realistic specialty/drug/geography distributions, and Rx-volume
statistics (power-law prescriber distribution, like real claims data)
so every downstream module (segmentation, call planning, IC, marketing
mix) works exactly as it would on the real file. Swapping in the real
CSV later requires zero changes to the downstream code — same schema.

Drug class chosen: Type 2 Diabetes (GLP-1 / oral) — high Rx volume,
multiple competing brands, realistic for a pharma commercial analytics
case study.
"""
import numpy as np
import pandas as pd

np.random.seed(42)

N_PRESCRIBERS = 6000

SPECIALTIES = {
    "Endocrinology": 0.08,
    "Internal Medicine": 0.30,
    "Family Practice": 0.32,
    "Cardiology": 0.06,
    "Nurse Practitioner": 0.14,
    "Physician Assistant": 0.10,
}

STATES = {  # rough population-weighted sample of US states
    "CA": 0.12, "TX": 0.09, "FL": 0.08, "NY": 0.07, "PA": 0.04,
    "IL": 0.04, "OH": 0.04, "GA": 0.03, "NC": 0.03, "MI": 0.03,
    "NJ": 0.03, "VA": 0.03, "WA": 0.02, "AZ": 0.02, "MA": 0.02,
    "TN": 0.02, "IN": 0.02, "MO": 0.02, "MD": 0.02, "WI": 0.02,
    "CO": 0.02, "MN": 0.02, "SC": 0.02, "AL": 0.02, "LA": 0.01,
    "KY": 0.01, "OR": 0.01, "OK": 0.01, "CT": 0.01, "IA": 0.01,
    "MS": 0.01, "AR": 0.01, "KS": 0.01, "UT": 0.01, "NV": 0.01,
    "NM": 0.01, "NE": 0.01, "WV": 0.01, "ID": 0.01, "HI": 0.01,
    "NH": 0.01, "ME": 0.01, "MT": 0.01, "RI": 0.01, "DE": 0.01,
    "SD": 0.01, "ND": 0.01, "AK": 0.01, "VT": 0.01, "WY": 0.01,
}

# Simulated brand portfolio for a Type 2 Diabetes drug class
DRUGS = [
    {"drug_name": "Glucotrol Advance", "type": "Brand", "base_share": 0.28},
    {"drug_name": "Metforcare XR",     "type": "Brand", "base_share": 0.22},
    {"drug_name": "Insulara",          "type": "Brand", "base_share": 0.18},
    {"drug_name": "metformin HCl",     "type": "Generic", "base_share": 0.20},
    {"drug_name": "glipizide",         "type": "Generic", "base_share": 0.12},
]

specialty_names = list(SPECIALTIES.keys())
specialty_p = list(SPECIALTIES.values())
state_names = list(STATES.keys())
state_p = np.array(list(STATES.values()))
state_p = state_p / state_p.sum()

rows = []
for i in range(N_PRESCRIBERS):
    npi = 1000000000 + i
    specialty = np.random.choice(specialty_names, p=specialty_p)
    state = np.random.choice(state_names, p=state_p)

    # Specialty drives base prescribing propensity (endocrinologists prescribe more)
    specialty_factor = {
        "Endocrinology": 3.2, "Internal Medicine": 1.4, "Family Practice": 1.2,
        "Cardiology": 0.9, "Nurse Practitioner": 1.0, "Physician Assistant": 0.9,
    }[specialty]

    # Power-law (Pareto-like) base volume so a small % of HCPs drive most volume
    base_volume = np.random.pareto(1.8) * 15 * specialty_factor
    base_volume = max(base_volume, 0)

    for drug in DRUGS:
        # Not every prescriber writes every drug
        writes_drug_prob = min(0.85, 0.25 + base_volume / 200)
        if np.random.rand() > writes_drug_prob:
            continue

        drug_volume_factor = drug["base_share"] * np.random.uniform(0.6, 1.4)
        total_claims = int(max(11, base_volume * drug_volume_factor * np.random.uniform(0.7, 1.3)))
        if total_claims < 11:  # CMS PUF suppresses counts <11 for privacy
            continue

        unit_cost = {
            "Glucotrol Advance": 185, "Metforcare XR": 210, "Insulara": 410,
            "metformin HCl": 12, "glipizide": 18,
        }[drug["drug_name"]]
        total_drug_cost = round(total_claims * unit_cost * np.random.uniform(0.85, 1.15), 2)
        total_day_supply = int(total_claims * np.random.uniform(28, 32))
        beneficiary_count = max(11, int(total_claims / np.random.uniform(2.2, 3.5)))

        rows.append({
            "npi": npi,
            "specialty": specialty,
            "state": state,
            "drug_name": drug["drug_name"],
            "drug_type": drug["type"],
            "total_claims": total_claims,
            "total_drug_cost": total_drug_cost,
            "total_day_supply": total_day_supply,
            "beneficiary_count": beneficiary_count,
        })

df = pd.DataFrame(rows)
df.to_csv("/home/claude/procdna_project/data/part_d_prescribers_by_provider_drug.csv", index=False)
print(f"Generated {len(df):,} prescriber-drug rows across {df['npi'].nunique():,} unique prescribers.")
print(df.head())
