"""
Kestrel Home Appliances - Warranty Fraud Detection Engine
Variant C Submission
"""

import os
import re
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

MODEL_PATH = os.path.join(os.path.dirname(__file__), "fraud_model.pkl")
META_PATH = os.path.join(os.path.dirname(__file__), "engine_meta.json")

def clean_serial(s):
    """Normalize serial number: remove spaces, punctuation, uppercase."""
    if pd.isna(s):
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", str(s)).upper()

class WarrantyFraudEngine:
    def __init__(self):
        self.model = None
        self.partners_df = None
        self.products_df = None
        self.serial_freq = {}
        self.partner_risk_map = {}
        self.city_risk_map = {}
        self.global_prior = 0.0123
        self.is_fitted = False
        
        # Base directory
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.load_reference_data()

    def load_reference_data(self):
        partners_file = os.path.join(self.base_dir, "partners.csv")
        products_file = os.path.join(self.base_dir, "products.csv")
        if os.path.exists(partners_file):
            self.partners_df = pd.read_csv(partners_file)
            self.partners_df['onboarded_date'] = pd.to_datetime(self.partners_df['onboarded_date'])
        if os.path.exists(products_file):
            self.products_df = pd.read_csv(products_file)

    def fit(self, train_path=None, test_path=None):
        if train_path is None:
            train_path = os.path.join(self.base_dir, "train.csv")
        if test_path is None:
            test_path = os.path.join(self.base_dir, "test_unlablled.csv")

        train_raw = pd.read_csv(train_path)
        test_raw = pd.read_csv(test_path) if os.path.exists(test_path) else None

        train_raw['clean_serial'] = train_raw['product_serial'].apply(clean_serial)
        if test_raw is not None:
            test_raw['clean_serial'] = test_raw['product_serial'].apply(clean_serial)
            all_serials = pd.concat([train_raw['clean_serial'], test_raw['clean_serial']])
        else:
            all_serials = train_raw['clean_serial']

        self.serial_freq = all_serials.value_counts().to_dict()

        # Merge reference data
        df = train_raw.merge(self.partners_df, on='partner_id', how='left').merge(self.products_df, on='sku', how='left')
        df['submitted_at'] = pd.to_datetime(df['submitted_at'])

        # Filter strictly labeled records (Tanmay note: Zoho legacy stored undecided as 0, CRM stores as blank)
        labeled = df[df['is_fraud'].notnull()].copy()
        labeled['is_fraud'] = labeled['is_fraud'].astype(int)

        self.global_prior = float(labeled['is_fraud'].mean())

        # Empirical Bayes smoothed partner fraud rates
        p_stats = labeled.groupby('partner_id')['is_fraud'].agg(['count', 'sum'])
        smooth = 5.0
        p_risk = (p_stats['sum'] + smooth * self.global_prior) / (p_stats['count'] + smooth)
        self.partner_risk_map = p_risk.to_dict()

        # City risk map
        c_stats = labeled.groupby('city')['is_fraud'].agg(['count', 'sum'])
        c_risk = (c_stats['sum'] + smooth * self.global_prior) / (c_stats['count'] + smooth)
        self.city_risk_map = c_risk.to_dict()

        X = self._extract_features_df(labeled)
        y = labeled['is_fraud'].values

        self.model = HistGradientBoostingClassifier(
            random_state=42,
            max_iter=150,
            min_samples_leaf=20,
            class_weight='balanced',
            l2_regularization=1.0
        )
        self.model.fit(X, y)
        self.is_fitted = True

        # Save metadata and trained weights
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(self.model, f)

        meta = {
            "global_prior": self.global_prior,
            "serial_freq": self.serial_freq,
            "partner_risk_map": self.partner_risk_map,
            "city_risk_map": self.city_risk_map,
            "fitted": True
        }
        with open(META_PATH, "w") as f:
            json.dump(meta, f)

        print(f"Engine fitted successfully on {len(labeled)} claims. Prior: {self.global_prior:.4f}")

    def load(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(META_PATH):
            with open(MODEL_PATH, "rb") as f:
                self.model = pickle.load(f)
            with open(META_PATH, "r") as f:
                meta = json.load(f)
            self.global_prior = meta["global_prior"]
            self.serial_freq = meta["serial_freq"]
            self.partner_risk_map = meta["partner_risk_map"]
            self.city_risk_map = meta["city_risk_map"]
            self.is_fitted = True
            return True
        return False

    def _extract_features_df(self, data):
        X = pd.DataFrame(index=data.index)
        
        # Financial
        claim_amt = data['claim_amount_inr'].astype(float)
        list_price = data['list_price_inr'].astype(float)
        X['claim_amount_inr'] = claim_amt
        X['list_price_inr'] = list_price
        X['claim_ratio'] = claim_amt / (list_price + 1e-5)
        
        # Time and warranty
        days = data['days_since_purchase'].astype(float)
        w_days = data['warranty_months'].astype(float) * 30.5
        X['days_since_purchase'] = days
        X['warranty_days'] = w_days
        X['warranty_exhaustion_ratio'] = days / (w_days + 1e-5)
        X['days_past_warranty'] = np.maximum(0, days - w_days)
        
        # Partner age & profile
        sub_time = pd.to_datetime(data['submitted_at'])
        onboard_time = pd.to_datetime(data['onboarded_date'])
        partner_age = (sub_time - onboard_time).dt.days.clip(lower=0)
        X['partner_age_days'] = partner_age
        X['is_new_partner'] = (partner_age < 365).astype(int)
        X['is_very_new_partner'] = (partner_age < 180).astype(int)
        
        # Policy May 1 loophole
        is_post_may = (sub_time >= '2026-05-01').astype(int)
        is_sub_2000 = (claim_amt < 2000).astype(int)
        X['is_post_may'] = is_post_may
        X['is_sub_2000'] = is_sub_2000
        X['may_sub_2000'] = is_post_may * is_sub_2000
        X['may_new_sub_2000'] = is_post_may * is_sub_2000 * X['is_new_partner']
        
        # Inspection & Evidence
        X['photo_attached_n'] = (data['photo_attached'] == 'N').astype(int)
        X['partner_inspected_n'] = (data['partner_inspected'] == 'N').astype(int)
        X['has_inspector_note'] = data['inspector_note'].notnull().astype(int)
        X['customer_prior_claims'] = data['customer_prior_claims'].astype(int)
        
        # Clean serial frequency
        clean_s = data['clean_serial'] if 'clean_serial' in data else data['product_serial'].apply(clean_serial)
        repeats = clean_s.map(self.serial_freq).fillna(1).astype(int)
        X['serial_repeat_count'] = repeats
        X['is_serial_repeated'] = (repeats > 1).astype(int)
        
        # Partner type
        X['is_franchise'] = (data['partner_type'] == 'franchise').astype(int)
        X['is_asc'] = (data['partner_type'] == 'authorised_service_centre').astype(int)
        X['is_freelance'] = (data['partner_type'] == 'freelance_technician').astype(int)
        
        # Risk priors
        X['partner_risk'] = data['partner_id'].map(self.partner_risk_map).fillna(self.global_prior)
        X['city_risk'] = data['city'].map(self.city_risk_map).fillna(self.global_prior)
        
        return X

    def predict_record(self, record):
        """
        Take a single record dict/JSON and return score + plain-English reasons.
        """
        if not self.is_fitted:
            if not self.load():
                self.fit()

        rec = dict(record)
        # Defaults if missing
        rec.setdefault('submitted_at', '2026-09-01 12:00:00')
        rec.setdefault('days_since_purchase', 180)
        rec.setdefault('claim_amount_inr', 1500.0)
        rec.setdefault('photo_attached', 'Y')
        rec.setdefault('partner_inspected', 'N')
        rec.setdefault('claim_description', 'Fault reported')
        rec.setdefault('inspector_note', None)
        rec.setdefault('customer_prior_claims', 0)
        rec.setdefault('source', 'crm')

        # Clean serial
        raw_serial = str(rec.get('product_serial', 'UNKNOWN'))
        c_serial = clean_serial(raw_serial)
        rec['clean_serial'] = c_serial

        # Partner lookup
        p_id = rec.get('partner_id', '')
        p_row = self.partners_df[self.partners_df['partner_id'] == p_id]
        if not p_row.empty:
            rec['city'] = p_row.iloc[0]['city']
            rec['onboarded_date'] = p_row.iloc[0]['onboarded_date']
            rec['partner_type'] = p_row.iloc[0]['partner_type']
        else:
            rec['city'] = 'Unknown'
            rec['onboarded_date'] = pd.to_datetime('2025-01-01')
            rec['partner_type'] = 'authorised_service_centre'

        # Product lookup
        sku = rec.get('sku', '')
        prod_row = self.products_df[self.products_df['sku'] == sku]
        if not prod_row.empty:
            rec['family'] = prod_row.iloc[0]['family']
            rec['list_price_inr'] = prod_row.iloc[0]['list_price_inr']
            rec['warranty_months'] = prod_row.iloc[0]['warranty_months']
        else:
            rec['family'] = 'Appliance'
            rec['list_price_inr'] = 5000.0
            rec['warranty_months'] = 12

        df_single = pd.DataFrame([rec])
        X = self._extract_features_df(df_single)
        
        # Predict probability
        score = float(self.model.predict_proba(X)[0, 1])

        # Generate human-readable reasons
        reasons = []
        claim_amt = float(rec['claim_amount_inr'])
        list_price = float(rec['list_price_inr'])
        claim_ratio = claim_amt / (list_price + 1e-5)
        submitted_at = pd.to_datetime(rec['submitted_at'])
        onboarded_date = pd.to_datetime(rec['onboarded_date'])
        partner_age = (submitted_at - onboarded_date).days
        serial_count = self.serial_freq.get(c_serial, 1)
        prior_claims = int(rec.get('customer_prior_claims', 0))
        partner_risk = self.partner_risk_map.get(p_id, self.global_prior)

        # 1. May 1 loophole rule check
        if submitted_at >= pd.to_datetime('2026-05-01') and claim_amt < 2000:
            if rec['partner_inspected'] == 'N':
                reasons.append(
                    f"Sub-Rs 2,000 Auto-Approval Rule: Claim amount (Rs {claim_amt:,.0f}) is below the Rs 2,000 inspection threshold "
                    f"under the May 1 policy change, submitted without partner inspection."
                )
            else:
                reasons.append(f"Sub-Rs 2,000 Claim: Claim amount is Rs {claim_amt:,.0f}, below the inspection waiver threshold.")

        # 2. Partner risk factor
        if partner_risk > 0.10:
            reasons.append(
                f"High-Risk Service Partner ({p_id} - {rec['partner_type'].replace('_', ' ').title()} in {rec['city']}): "
                f"Historical fraud rate of {partner_risk:.1%} (benchmark average is {self.global_prior:.1%})."
            )
        elif partner_age < 180:
            reasons.append(
                f"Recently Onboarded Partner: Partner {p_id} was onboarded {partner_age} days ago. "
                f"New partners exhibit elevated risk under the revised warranty policy."
            )

        # 3. Serial repeat check
        if serial_count > 1:
            reasons.append(
                f"Repeated Product Serial: Clean serial '{c_serial}' has appeared {serial_count} times in the claims database. "
                f"Possible duplicate or recycled warranty claim."
            )

        # 4. Customer prior claims
        if prior_claims >= 2:
            reasons.append(
                f"High Customer Prior Claim Velocity: Customer has filed {prior_claims} previous warranty claims. "
                f"Fraud probability increases significantly for repeat claimants."
            )

        # 5. Claim to price ratio
        if claim_ratio > 0.60:
            reasons.append(
                f"High Repair-to-Price Ratio: Claim amount of Rs {claim_amt:,.0f} represents {claim_ratio:.1%} "
                f"of the product's list price (Rs {list_price:,.0f}). Normal repairs average 31%."
            )

        # 6. Documentation and notes
        if rec.get('photo_attached') == 'N':
            reasons.append("Missing Evidence: No photographic documentation attached to the claim.")
        if rec.get('partner_inspected') == 'N' and claim_amt >= 2000:
            reasons.append("Missing Inspection Sign-Off: Policy requires partner inspection for claims over Rs 2,000.")

        # Decision category
        if score >= 0.70:
            decision = "HOLD & INVESTIGATE"
            severity = "HIGH"
            action = "Forward claim immediately to Farhan's investigation desk before issuing payout."
        elif score >= 0.35:
            decision = "DESK REVIEW QUEUE"
            severity = "MEDIUM"
            action = "Add to monthly 40-claim manual review queue. Verify customer invoice and serial photo."
        else:
            decision = "AUTO APPROVE"
            severity = "LOW"
            action = "Approve for settlement within standard 3-day turnaround SLA."

        return {
            "claim_id": rec.get("claim_id", "TEST_CLAIM"),
            "score": round(score, 4),
            "severity": severity,
            "decision": decision,
            "recommended_action": action,
            "claim_amount_inr": claim_amt,
            "potential_fraud_exposure_inr": claim_amt if score >= 0.35 else 0.0,
            "goodwill_risk_inr": 380.0 if score >= 0.35 else 0.0,
            "reasons": reasons if reasons else ["Standard claim profile within normal operational parameters."]
        }

    def generate_predictions_csv(self, test_path=None, output_path=None):
        if not self.is_fitted:
            if not self.load():
                self.fit()

        if test_path is None:
            test_path = os.path.join(self.base_dir, "test_unlablled.csv")
        if output_path is None:
            output_path = os.path.join(self.base_dir, "predictions.csv")

        test_raw = pd.read_csv(test_path)
        test_raw['clean_serial'] = test_raw['product_serial'].apply(clean_serial)

        df = test_raw.merge(self.partners_df, on='partner_id', how='left').merge(self.products_df, on='sku', how='left')
        X = self._extract_features_df(df)

        scores = self.model.predict_proba(X)[:, 1]
        
        # Round to 4 decimal places
        preds_df = pd.DataFrame({
            "claim_id": test_raw["claim_id"],
            "score": np.round(scores, 4)
        })

        preds_df.to_csv(output_path, index=False)
        print(f"Generated predictions for {len(preds_df)} rows saved to {output_path}")
        return preds_df

if __name__ == "__main__":
    engine = WarrantyFraudEngine()
    engine.fit()
    preds = engine.generate_predictions_csv()
    print("Predictions sample:")
    print(preds.head(10))
    print("\nScore statistics:")
    print(preds['score'].describe())
