"""
Synthetic Auto Insurance Dataset Generator
==========================================
Senior Insurance Data Engineer / Actuarial Analyst specification.

Actuarial logic:
  - Base rate anchored to ISO pure premium benchmarks (~$800–$1,200 for standard risk)
  - Age relativities calibrated to industry loss cost studies
  - Mileage relativities based on usage-based insurance (UBI) research
  - Vehicle age curve: slight premium increase for older cars (parts cost, reliability)
  - Risk segment thresholds derived from combined ratio analysis
  - All multipliers are multiplicative (reflecting ISO rating engine structure)
"""

import os
import numpy as np
import pandas as pd 

# ── Reproducibility ─────────────────────────────────────────────────────────
RNG_SEED = 42
rng = np.random.default_rng(RNG_SEED)

N = 5_000
os.makedirs("data", exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# 1. DRIVER / VEHICLE CHARACTERISTICS
#    Distributions calibrated to reflect real US licensed-driver population
#    (FHWA, Census, ISO driver data)
# ─────────────────────────────────────────────────────────────────────────────

# Age: skewed toward working-age adults (25–60 peak)
# Modeled as a mixture: young drivers + main working population + seniors
age_raw = np.concatenate([
    rng.uniform(18, 25, size=int(N * 0.12)),   # young drivers ~12 %
    rng.normal(40, 10, size=int(N * 0.70)),     # main cohort   ~70 %
    rng.uniform(60, 75, size=int(N * 0.18)),    # seniors       ~18 %
])
rng.shuffle(age_raw)
customer_age = np.clip(age_raw[:N].round().astype(int), 18, 75)

# Vehicle age: most vehicles on road are 3–12 years old (Experian data)
vehicle_age_raw = rng.gamma(shape=2.2, scale=3.5, size=N)
vehicle_age = np.clip(vehicle_age_raw.round().astype(int), 0, 20)

# Annual mileage: log-normal reflecting commuter/leisure split (FHWA avg ~13,500 mi)
log_mileage = rng.normal(loc=np.log(13_500), scale=0.45, size=N)
annual_mileage = np.clip(np.exp(log_mileage).round(-2).astype(int), 5_000, 30_000)

# ─────────────────────────────────────────────────────────────────────────────
# 2. BASE RATE
#    Territory / coverage-level proxy; varies by simulated "territory class"
#    (urban/suburban/rural) which correlates weakly with age & mileage
# ─────────────────────────────────────────────────────────────────────────────
# Territory class: 0=rural, 1=suburban, 2=urban
# Urban skews younger + higher mileage (city commuters)
def get_territory_weights(age):
    if age < 30:
        return [0.15, 0.40, 0.45]
    elif age < 50:
        return [0.25, 0.50, 0.25]
    else:
        return [0.35, 0.45, 0.20]

territory_class = np.array([
    rng.choice([0, 1, 2], p=get_territory_weights(customer_age[i]))
    for i in range(N)
])

# Base rate per territory (reflects liability + comp/collision split)
territory_base = {0: 820, 1: 950, 2: 1_120}
base_rate_core = np.array([territory_base[t] for t in territory_class])

# Add small carrier-level noise (±5 %) to simulate book-of-business variation
base_rate_noise = rng.uniform(0.95, 1.05, size=N)
base_rate = (base_rate_core * base_rate_noise).round(2)

# ─────────────────────────────────────────────────────────────────────────────
# 3. RATING FACTORS (multiplicative relativities)
#    Each relativity is anchored at 1.000 for the "standard" risk class.
# ─────────────────────────────────────────────────────────────────────────────

# ── 3a. Age relativity ───────────────────────────────────────────────────────
# Industry studies (HLDI, ISO): drivers <25 carry 1.5–2.5× the loss cost of
# a 40-year-old; gradual decrease to ~0.85× for ages 50–60, then slight uptick.
def age_relativity(age: np.ndarray) -> np.ndarray:
    rel = np.where(
        age < 20, 2.40,
        np.where(age < 22, 2.10,
        np.where(age < 25, 1.75,
        np.where(age < 30, 1.35,
        np.where(age < 40, 1.05,
        np.where(age < 50, 1.00,
        np.where(age < 60, 0.92,
        np.where(age < 65, 0.95,
        np.where(age < 70, 1.08, 1.18)))))))))
    return rel.astype(float)

age_rel = age_relativity(customer_age)

# ── 3b. Mileage relativity ───────────────────────────────────────────────────
# UBI research (LexisNexis, Verisk): exposure scales ~0.65 power of mileage;
# anchored at 13,500 mi = 1.000
ANCHOR_MILES = 13_500.0
mileage_rel = (annual_mileage / ANCHOR_MILES) ** 0.65

# ── 3c. Vehicle age relativity ───────────────────────────────────────────────
# New vehicles (0–2 yrs): higher comp/collision cost → slight premium increase
# Mid-age (3–8 yrs): lowest cost, often drop comprehensive
# Old vehicles (9+ yrs): parts availability, reliability risk; modest uptick
def vehicle_age_relativity(vage: np.ndarray) -> np.ndarray:
    rel = np.where(
        vage <= 2,  1.18,
        np.where(vage <= 5,  1.00,
        np.where(vage <= 8,  0.95,
        np.where(vage <= 12, 0.97,
        np.where(vage <= 16, 1.05, 1.12)))))
    return rel.astype(float)

vehicle_rel = vehicle_age_relativity(vehicle_age)

# ─────────────────────────────────────────────────────────────────────────────
# 4. CURRENT PREMIUM  (fully derived, no arbitrary randomness)
#    premium = base_rate × age_rel × mileage_rel × vehicle_rel × (1 + expense_load)
#    Expense load: 28 % (industry average: commissions 12 %, overhead 16 %)
# ─────────────────────────────────────────────────────────────────────────────
EXPENSE_LOAD = 1.28

current_premium_raw = (
    base_rate
    * age_rel
    * mileage_rel
    * vehicle_rel
    * EXPENSE_LOAD
)

# Round to nearest dollar (standard carrier practice)
current_premium = current_premium_raw.round(2)

# ─────────────────────────────────────────────────────────────────────────────
# 5. RISK SEGMENT
#    Derived from combined relativity score (age × mileage × vehicle).
#    Thresholds set so that low ≈ 45 %, medium ≈ 35 %, high ≈ 20 %
#    (reflects typical personal-lines book distribution).
# ─────────────────────────────────────────────────────────────────────────────
combined_rel = age_rel * mileage_rel * vehicle_rel

p45 = np.percentile(combined_rel, 45)
p80 = np.percentile(combined_rel, 80)

risk_segment = np.where(
    combined_rel <= p45, "low",
    np.where(combined_rel <= p80, "medium", "high")
)

# ─────────────────────────────────────────────────────────────────────────────
# 6. AGE GROUP  (standard actuarial banding)
# ─────────────────────────────────────────────────────────────────────────────
age_group = np.where(
    customer_age < 25, "<25",
    np.where(customer_age <= 40, "25-40", ">40")
)

# ─────────────────────────────────────────────────────────────────────────────
# 7. POLICY IDs
# ─────────────────────────────────────────────────────────────────────────────
policy_id = [f"POL-{str(i+1).zfill(6)}" for i in range(N)]

# ─────────────────────────────────────────────────────────────────────────────
# 8. ASSEMBLE DATAFRAME
# ─────────────────────────────────────────────────────────────────────────────
df = pd.DataFrame({
    "policy_id":      policy_id,
    "customer_age":   customer_age,
    "vehicle_age":    vehicle_age,
    "annual_mileage": annual_mileage,
    "base_rate":      base_rate,
    "current_premium": current_premium,
    "risk_segment":   risk_segment,
    "age_group":      age_group,
})

# ─────────────────────────────────────────────────────────────────────────────
# 9. VALIDATION CHECKS
# ─────────────────────────────────────────────────────────────────────────────
assert df.isnull().sum().sum() == 0, "ERROR: Missing values detected"
assert df["customer_age"].between(18, 75).all(), "ERROR: Age out of range"
assert df["vehicle_age"].between(0, 20).all(), "ERROR: Vehicle age out of range"
assert df["annual_mileage"].between(5_000, 30_000).all(), "ERROR: Mileage out of range"
assert set(df["risk_segment"].unique()).issubset({"low", "medium", "high"}), \
    "ERROR: Invalid risk segment values"
assert set(df["age_group"].unique()).issubset({"<25", "25-40", ">40"}), \
    "ERROR: Invalid age group values"

# Correlation sanity checks (actuarial direction)
corr_age_prem = df["customer_age"].corr(df["current_premium"])
corr_mil_prem = df["annual_mileage"].corr(df["current_premium"])
assert corr_age_prem < 0, \
    f"ERROR: Older age should reduce premium on average (got corr={corr_age_prem:.3f})"
assert corr_mil_prem > 0, \
    f"ERROR: Higher mileage should increase premium (got corr={corr_mil_prem:.3f})"

# Risk segment premium ordering
seg_means = df.groupby("risk_segment")["current_premium"].mean()
assert seg_means["low"] < seg_means["medium"] < seg_means["high"], \
    f"ERROR: Risk segment premium ordering violated:\n{seg_means}"

# ─────────────────────────────────────────────────────────────────────────────
# 10. SAVE + SUMMARY REPORT
# ─────────────────────────────────────────────────────────────────────────────
output_path = "data/dataset.csv"
df.to_csv(output_path, index=False)

print("=" * 60)
print("  AUTO INSURANCE SYNTHETIC DATASET — GENERATION COMPLETE")
print("=" * 60)
print(f"\n  Output : {output_path}")
print(f"  Rows   : {len(df):,}")
print(f"  Cols   : {len(df.columns)}")

print("\n── Premium Statistics ──────────────────────────────────────")
p = df["current_premium"]
print(f"  Min    : ${p.min():>8,.2f}")
print(f"  Mean   : ${p.mean():>8,.2f}")
print(f"  Median : ${p.median():>8,.2f}")
print(f"  Max    : ${p.max():>8,.2f}")
print(f"  StdDev : ${p.std():>8,.2f}")

print("\n── Risk Segment Distribution ───────────────────────────────")
seg_dist = df["risk_segment"].value_counts(normalize=True).reindex(["low", "medium", "high"])
for seg, pct in seg_dist.items():
    mean_prem = seg_means[seg]
    print(f"  {seg:<8}: {pct*100:5.1f}%   avg premium ${mean_prem:,.2f}")

print("\n── Age Group Distribution ──────────────────────────────────")
ag_dist = df["age_group"].value_counts(normalize=True).reindex(["<25", "25-40", ">40"])
ag_means = df.groupby("age_group")["current_premium"].mean()
for ag, pct in ag_dist.items():
    print(f"  {ag:<8}: {pct*100:5.1f}%   avg premium ${ag_means[ag]:,.2f}")

print("\n── Correlation with Premium ────────────────────────────────")
for col in ["customer_age", "vehicle_age", "annual_mileage", "base_rate"]:
    print(f"  {col:<20}: {df[col].corr(df['current_premium']):+.4f}")

print("\n── All Validation Checks Passed ✓ ──────────────────────────\n")