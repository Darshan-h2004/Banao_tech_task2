# Kestrel Home — Warranty Claim Review System (Variant C)
**D2C Operations & Warranty Fraud Prevention Platform**  
*Pune Operations & Authorised Service Partner Network*

---

## 🚀 Quick Start (Clean Machine Instructions)

This project starts on any clean workstation running standard Python 3.9+ without paid API keys.

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Automated Verification & Audit
Validates `predictions.csv`, verifies the 98.90% accuracy Board KPI, audits ROC-AUC (0.9961), and simulates Farhan's 40-claim monthly queue:
```bash
python verify.py
```

### 3. Launch the Web Service & Dashboard
```bash
python server.py
```
Open your browser to: **[http://127.0.0.1:8080](http://127.0.0.1:8080)**

---

## 📁 Repository Structure

```
├── engine.py                  # Core ML engine: sanitization, feature engineering, and inference
├── server.py                  # Lightweight HTTP API & static web server (zero external web frameworks)
├── verify.py                  # Comprehensive test, verification, and financial ROI audit script
├── predictions.csv            # Final predictions for all 2,252 rows of test_unlablled.csv
├── requirements.txt           # Python dependencies (pandas, numpy, scikit-learn)
│
├── web/                       # Modern responsive web dashboard
│   ├── index.html             # Interactive inspector & Farhan's Top 40 review queue
│   ├── app.js                 # Frontend state, API client, animated SVG gauge
│   └── style.css              # Dark aesthetic stylesheet, glassmorphism, responsive grid
│
├── EVIDENCE.md                # Quantitative performance evidence, confusion matrix, failure modes
├── MEMO_RITU_DESHPANDE.md     # One-page executive business memo to Ritu Deshpande
├── RECORDING_SCRIPT.md        # 3-minute video presentation script (what was tried, changed, thrown away)
├── kestrel_fraud_demo.webp    # Browser session recording showing end-to-end working product
├── submission-form.md         # Official completed submission form
│
├── train.csv                  # 12,029 historical warranty claims (April 2025 – June 2026)
├── test_unlablled.csv         # 2,252 unlabelled test claims (July 2026 – September 2026)
├── partners.csv               # Reference data: 380 authorised service centres and franchises
├── products.csv               # Reference data: 21 appliance SKUs and list prices
├── ops-policy.pdf             # Operations Policy v4.1 (costs, review capacity, rules)
└── email-thread.txt           # Stakeholder correspondence (Ritu, Farhan, Meenal, Tanmay)
```

---

## 🌐 API Endpoint Specification

### `POST /api/predict`
Takes a single warranty claim record as JSON and returns calibrated risk score, operational verdict, financial exposure, and human-readable operational reasons.

**Sample Request**:
```bash
curl -X POST http://127.0.0.1:8080/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "WC713056",
    "submitted_at": "2026-08-15 14:22:00",
    "partner_id": "SP3160",
    "sku": "KH-AF-01",
    "product_serial": "KH896633366",
    "days_since_purchase": 140,
    "claim_amount_inr": 1950.0,
    "photo_attached": "N",
    "partner_inspected": "N",
    "claim_description": "unit not heating",
    "inspector_note": "",
    "customer_prior_claims": 2,
    "source": "crm"
  }'
```

**Sample Response**:
```json
{
  "claim_id": "WC713056",
  "score": 0.9452,
  "severity": "HIGH",
  "decision": "HOLD & INVESTIGATE",
  "recommended_action": "Forward claim immediately to Farhan's investigation desk before issuing payout.",
  "claim_amount_inr": 1950.0,
  "potential_fraud_exposure_inr": 1950.0,
  "goodwill_risk_inr": 380.0,
  "reasons": [
    "Sub-Rs 2,000 Auto-Approval Rule: Claim amount (Rs 1,950) is below the Rs 2,000 inspection threshold under the May 1 policy change, submitted without partner inspection.",
    "High-Risk Service Partner (SP3160 - Authorised Service Centre in Pune): Historical fraud rate of 21.4% (benchmark average is 1.2%).",
    "Repeated Product Serial: Clean serial 'KH896633366' has appeared 4 times in the claims database. Possible duplicate or recycled warranty claim.",
    "High Customer Prior Claim Velocity: Customer has filed 2 previous warranty claims. Fraud probability increases significantly for repeat claimants.",
    "Missing Evidence: No photographic documentation attached to the claim."
  ]
}
```

---

## 📊 Business & Operational Highlights

1. **Board KPI Target (> 97.0% Accuracy)**:
   * **Delivered: 98.90% Accuracy** (and 99.17% in 5-fold cross-validation).
   * Surpasses the Board's required pass mark.

2. **Farhan Sheikh's Desk Capacity (40 claims / month)**:
   * Catches **97.2% of all historical fraud claims (141 of 145)**.
   * Stops **₹6,38,301 out of ₹6,45,126 in fraudulent payouts (98.9% of all fraud rupees)**.
   * After paying ₹1,74,420 in ₹380 goodwill vouchers for held genuine customers, Kestrel realizes **+₹4,63,881 in net cash savings**.
   * **Net Benefit per Review: ₹773.13 net profit per claim investigated**.

3. **May 1, 2026 Loophole Addressed**:
   * Prior to May 1, sub-₹2,000 fraud was 0.54%.
   * Following the inspection waiver on May 1, sub-₹2,000 fraud jumped 5.7x to 3.09%, heavily concentrated in 7 newly onboarded service partners.
   * The engine specifically flags these exploit bursts while maintaining high turnaround for legitimate regional partners.
