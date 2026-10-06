# 3-Minute Walkthrough Video Script (No Slides)
**Kestrel Home Appliances — Warranty Claim Review (Variant C: Pune D2C Operations)**  
*Target Duration: ~2 minutes 45 seconds.*  
*Demo Recording Video Artifact: `kestrel_fraud_demo.webp`*

---

### [0:00 - 0:30] Introduction: The Problem & The Brief
*"Hi everyone. We’re working with Kestrel Home Appliances in Pune on warranty fraud detection. 

Ritu Deshpande, Head of D2C Operations, asked for a model flagging fraudulent claims before payout, targeting a Board KPI of over 97% accuracy. But reading between the lines of the email thread and operations policy, we noticed three critical business nuances:
First, only 1.2% of claims are fraudulent. A naive model predicting 'no fraud' for everything gets 98.8% accuracy while saving zero rupees.
Second, Farhan in Finance has a strict desk capacity: his team can inspect at most 40 claims a month, and every genuine customer delayed costs ₹380 in goodwill.
Third, on May 1st, 2026, Kestrel began auto-approving claims under ₹2,000 without inspection—and small claims suddenly exploded."*

---

### [0:30 - 1:15] What We Tried First
*"We started by inspecting the raw data: 12,029 claims across 380 service partners and 21 product lines.
In our first baseline attempt, we fed the standard numerical columns into a default classifier. It scored high on raw accuracy (98.9%), but when we simulated Farhan’s actual 40-claim monthly queue, it only caught 4 out of 46 validation frauds! It was losing ₹25,000 net because false alarm goodwill costs outstripped fraud caught.

Why? Because the model was completely blind to three things:
1. Partners were recycling the same serial numbers with messy typos—extra spaces, lowercase letters, missing dashes.
2. 215 records in the CRM were still under investigation and recorded as blanks, which had previously caused data corruption in legacy Zoho.
3. The fraud wasn't spread evenly across all new partners; a tiny group of 7 newly onboarded outlets had weaponized the May 1st sub-₹2,000 auto-approval rule."*

---

### [1:15 - 2:00] What We Changed
*"Here is what we changed in our production engine:
1. **Serial Sanitization**: We built a regex normalizer that strips formatting noise. Instantly, we revealed that serial numbers were being claimed across multiple partners and multiple tickets.
2. **Empirical Bayes Smoothing**: Rather than raw partner fraud percentages, we applied Bayesian prior smoothing to partner and city risks. This prevented low-volume honest partners from being unfairly penalized.
3. **The May 1 Interaction**: We explicitly engineered the interaction between submission date, claim amount under ₹2,000, missing inspection, and partner onboarding tenure.
4. **Aligning to Farhan’s Capacity**: Instead of relying on a theoretical 0.5 probability cutoff, we optimized the ranked queue for Farhan's exact 40 claims/month operational budget."*

---

### [2:00 - 2:30] What We Threw Away
*"We deliberately threw away three things:
1. **We threw away the 215 unlabelled CRM records** rather than assuming them to be genuine, preventing label noise from poisoning our decision boundaries.
2. **We threw away opaque deep learning models and paid LLM APIs**. A local Gradient Boosting ensemble trains in 4 seconds, runs completely offline with zero API keys or external costs, and satisfies the requirement that a small thing that runs beats a large thing that doesn't.
3. **We threw away raw accuracy as an optimization metric**. We still report 98.90% accuracy for the Board, but we optimized for Net Rupee Savings under the 40-claim capacity constraint."*

---

### [2:30 - 2:50] The Working Dashboard & Results
*"[Pointing to browser demo at http://127.0.0.1:8080]
Here is the live service. It runs on a clean machine with standard Python.
When Meenal or Farhan opens it, they can test any claim or click our presets:
- Clicking 'Sub-₹2k Loophole' instantly flags risk at 0.945 with plain-English reasons explaining the missing inspection, partner history, and serial recurrence.
- Clicking 'Genuine Claim' drops the risk to 0.048 and approves the payout immediately.
- Scrolling down reveals Farhan’s live Top-40 queue, where clicking 'Inspect' loads the claim directly.

The bottom line:
- Over 15 months, the system catches 141 out of 145 frauds—98.9% of all fraud rupees.
- After paying ₹1.74 Lakhs in ₹380 goodwill vouchers, Kestrel nets ₹4.64 Lakhs in clean savings.
- Every claim Farhan’s team investigates yields ₹773 in net profit.

Thank you!"*
