"""
Kestrel Home Appliances - Warranty Fraud Review Service
Variant C Submission
Lightweight HTTP API and Dashboard Server
"""

import os
import json
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from engine import WarrantyFraudEngine

PORT = 8080
engine = WarrantyFraudEngine()

# Ensure model is ready
if not engine.load():
    engine.fit()

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

class KestrelRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, data):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            self._send_json(200, {
                "status": "healthy",
                "service": "kestrel-fraud-engine-v3",
                "prior_fraud_rate": engine.global_prior,
                "model_fitted": engine.is_fitted
            })
            return

        elif path == "/api/samples":
            # Return realistic sample test cases for 1-click testing
            samples = [
                {
                    "name": "Sub-Rs 2,000 May Policy Exploit (High Risk)",
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
                },
                {
                    "name": "Repeated Serial Number Recycling (High Risk)",
                    "claim_id": "WC712642",
                    "submitted_at": "2026-07-28 11:05:00",
                    "partner_id": "SP3232",
                    "sku": "KH-RV-02",
                    "product_serial": "KH727846878",
                    "days_since_purchase": 210,
                    "claim_amount_inr": 5400.0,
                    "photo_attached": "N",
                    "partner_inspected": "N",
                    "claim_description": "motor not running",
                    "inspector_note": "",
                    "customer_prior_claims": 3,
                    "source": "crm"
                },
                {
                    "name": "Medium-Risk Franchise Review (Borderline)",
                    "claim_id": "WC711820",
                    "submitted_at": "2026-07-10 16:40:00",
                    "partner_id": "SP3376",
                    "sku": "KH-MG-01",
                    "product_serial": "KH491024819",
                    "days_since_purchase": 320,
                    "claim_amount_inr": 2450.0,
                    "photo_attached": "Y",
                    "partner_inspected": "Y",
                    "claim_description": "blade jammed",
                    "inspector_note": "Minor fault, part swapped",
                    "customer_prior_claims": 1,
                    "source": "crm"
                },
                {
                    "name": "Standard Genuine Customer Repair (Low Risk)",
                    "claim_id": "WC711348",
                    "submitted_at": "2026-07-01 10:15:00",
                    "partner_id": "SP3033",
                    "sku": "KH-AF-01",
                    "product_serial": "KH119482710",
                    "days_since_purchase": 95,
                    "claim_amount_inr": 850.0,
                    "photo_attached": "Y",
                    "partner_inspected": "Y",
                    "claim_description": "filter indicator stuck",
                    "inspector_note": "Photos match fault, approved",
                    "customer_prior_claims": 0,
                    "source": "crm"
                }
            ]
            self._send_json(200, {"samples": samples})
            return

        elif path in ["/api/top_flagged", "/api/queue"]:
            # Load predictions and return the top 40 review queue
            preds_file = os.path.join(os.path.dirname(__file__), "predictions.csv")
            test_file = os.path.join(os.path.dirname(__file__), "test_unlablled.csv")
            if os.path.exists(preds_file) and os.path.exists(test_file):
                import pandas as pd
                preds = pd.read_csv(preds_file)
                test = pd.read_csv(test_file)
                merged = preds.merge(test, on="claim_id").sort_values("score", ascending=False)
                merged = merged.fillna("")
                top_items = merged.head(40).to_dict(orient="records")
                self._send_json(200, {"top_flagged": top_items, "count": len(top_items)})
                return
            self._send_json(200, {"top_flagged": [], "count": 0})
            return

        # Serve static web files
        if path == "/" or path == "":
            path = "/index.html"

        file_path = os.path.join(WEB_DIR, path.lstrip("/"))
        if os.path.exists(file_path) and os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = "application/octet-stream"
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/predict":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len).decode("utf-8")
                record = json.loads(body) if body else {}

                result = engine.predict_record(record)
                self._send_json(200, result)
            except Exception as e:
                self._send_json(400, {
                    "error": str(e),
                    "message": "Failed to score record. Ensure valid JSON payload."
                })
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Endpoint not found")

def run(port=PORT):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, KestrelRequestHandler)
    print(f"Kestrel Fraud Review Service running on http://127.0.0.1:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    run()
