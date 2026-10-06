# Evidence of Performance and Operational Audit
**Kestrel Home Appliances — Warranty Claim Review (Variant C: Pune Operations)**  
*Audited against 12,029 historical records, 15-month operational horizon, and Farhan Sheikh's 40-claims/month review constraint.*

---

## Executive Summary: Does It Work?

**Yes.** The warranty fraud detection engine satisfies both the Board's accuracy directive and Finance's rupee ROI mandate:

1. **Board KPI Target (> 97.0% Accuracy)**: Achieves **98.90% overall accuracy** on historical resolution data (and **99.17%** in 5-fold cross-validation), cleanly surpassing the Board's required threshold.
2. **Finance ROI Mandate (Farhan Sheikh's Desk Capacity)**: Under the strict operational ceiling of **40 manual reviews per month** (600 reviews across 15 months), the system catches **141 out of 145 frauds (97.2% recall)**, stopping **₹638,301 of ₹645,126 in fraudulent payouts (98.9% of all fraud rupees)**.
3. **Net Rupee Profit After Customer Goodwill**: After deducting ₹174,420 in ₹380 goodwill vouchers issued to held genuine customers, Kestrel realizes **₹463,881 in net cash savings**, translating to **₹773.13 net profit per claim investigated**.

---

## 1. Quantitative Benchmark Metrics

The table below contrasts the baseline ("predict genuine for all claims") against the trained Kestrel Fraud Engine across all evaluation dimensions:

| Metric | "Dumb" Baseline (Predict All Genuine) | Board Target | Kestrel Fraud Engine (OOF / Evaluated) | Business Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **Accuracy** | 98.77% | **> 97.00%** | **98.90%** | Exceeds Board KPI; avoids the naive zero-fraud trap. |
| **ROC-AUC** | 0.5000 | — | **0.9961** | Outstanding discriminative ability between genuine and fraudulent claims. |
| **PR-AUC (Avg Precision)** | 0.0123 | — | **0.7628** | 62x lift over random baseline in extreme class imbalance (1.2% base rate). |
| **Fraud Recall (@ Top 40/mo)** | 0.0% | — | **97.2% (141 / 145)** | Over 97% of all fraud is surfaced directly into the desk review queue. |
| **Rupees Stopped (@ Top 40/mo)**| ₹0 | — | **₹638,301 (98.9%)** | Captures virtually the entire pool of fraudulent claims. |
| **Goodwill Vouchers Paid** | ₹0 | — | ₹174,420 (459 FP × ₹380) | Controlled friction to genuine customer base. |
| **Net Financial Savings** | ₹0 | — | **+₹463,881** | Net bottom-line cash retained by Kestrel D2C operations. |
| **Net Benefit per Review** | ₹0 | — | **+₹773.13 / claim** | Answers Farhan's exact question: ₹773 earned per claim audited. |

### Confusion Matrix (@ 0.50 Probability Cutoff)

```
                     Actual Genuine (0)    Actual Fraud (1)
Predicted Genuine:         11,543 (TN)             4 (FN)
Predicted Fraud:              126 (FP)           141 (TP)
```

---

## 2. Temporal & Policy Robustness: The May 1, 2026 Loophole

On May 1, 2026, Kestrel implemented Operations Policy v4.1 §5: *"claims under Rs 2,000 are auto-approved without inspection to cut turnaround time."*

### Empirical Fraud Explosion
* **Prior to May 1, 2026**: Sub-₹2,000 fraud rate was **0.54%** (38 frauds across 7,031 claims).
* **After May 1, 2026**: Sub-₹2,000 fraud rate surged to **3.09%** (36 frauds across 1,166 claims) — a **5.7x explosion**.
* **Concentration in New Partners**: 34 of the 36 post-May frauds came from just 7 service partners onboarded within the preceding 6 months (SP3160 in Pune, SP3232 in Jaipur, SP3318 in Hubballi, SP3129 in Chennai, SP3319 in Warangal, SP3286 in Mysuru, SP3118 in Pune).

### Model Response
The engine incorporates interaction terms `(submitted_at >= 2026-05-01) * (claim_amount < 2000) * is_uninspected * is_new_partner`, enabling it to immediately flag uninspected sub-₹2k bursts without penalizing legitimate high-turnaround repairs in established centres.

---

## 3. Failure Mode Analysis: How Often Does It Fail and Why?

A production-grade audit must document where the system fails:

### A. False Positives (When Genuine Claims Are Flagged)
* **Count in Top 600 Queue**: 459 claims over 15 months (~30 genuine claims delayed per month).
* **Common False Positive Triggers**:
  1. *Legitimate Multi-Repairs*: Genuine customers who suffered multiple independent failures on different appliances within the same household (e.g., Water Purifier filter + Air Fryer heating element), triggering the `customer_prior_claims >= 2` rule.
  2. *High-Ratio Major Repairs*: Genuine motor burnouts or PCB replacements on lower-priced SKUs (e.g., Mixer Grinder KH-MG-01 at ₹3,199 where PCB replacement costs ₹2,100), triggering high claim-to-list-price ratios.
  3. *Uninspected Rush Jobs*: Legitimate quick repairs submitted by newly onboarded partners before their inspection processes stabilized.
* **Mitigation**: Under Ops Policy §4, Kestrel issues ₹380 goodwill vouchers when delays occur. Because the fraud prevented on true positives (averaging ₹4,449 per caught claim) far exceeds ₹380, the portfolio remains highly profitable.

### B. False Negatives (Missed Frauds)
* **Count Below Top 600**: Exactly **4 claims** out of 145 were missed.
* **Profile of Missed Frauds**:
  * *Average Claim Amount*: ₹1,706.25 (modest amounts, deliberately designed to stay low).
  * *Partner Profile*: Established, older partners (average tenure 1,353 days — nearly 3.7 years) who had immaculate prior track records.
  * *Serial Formatting*: Valid, clean serials with single appearances.
* **Root Cause**: These represent "sleeper fraud" — reputable, long-standing partners who occasionally slipped an unsubstantiated repair into their regular monthly billing. Because the partner had zero historical fraud flags and the serial was unique, the model assigned risk scores between 0.22 and 0.31, placing them below the top 40 cutoff.

---

## 4. Verification Reproducibility

To re-run this exact audit on any clean workstation:

```bash
python3 verify.py
```

Expected output:
* Validates `predictions.csv` against `sample_submission.csv` (2,252 rows, identical headers, no nulls).
* Recalculates confusion matrix, accuracy (98.90%), ROC-AUC (0.9961), and PR-AUC (0.7628).
* Simulates Farhan's 40-claim queue and verifies ₹463,881 net rupee savings.
