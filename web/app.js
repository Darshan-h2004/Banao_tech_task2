// Kestrel Home Appliances - Frontend Client Logic

let samplesCache = [];

document.addEventListener("DOMContentLoaded", () => {
  fetchSamples();
  fetchTopQueue();
  // Automatically trigger prediction on default prefilled sample
  submitCurrentForm();
});

async function fetchSamples() {
  try {
    const res = await fetch("/api/samples");
    const data = await res.json();
    samplesCache = data.samples || [];
  } catch (err) {
    console.error("Failed to load samples:", err);
  }
}

function loadSample(index) {
  if (!samplesCache || !samplesCache[index]) return;
  const s = samplesCache[index];

  document.getElementById("claim_id").value = s.claim_id || "WC700000";
  document.getElementById("submitted_at").value = s.submitted_at || "2026-08-01 12:00:00";
  document.getElementById("partner_id").value = s.partner_id || "";
  document.getElementById("sku").value = s.sku || "KH-AF-01";
  document.getElementById("product_serial").value = s.product_serial || "";
  document.getElementById("claim_amount_inr").value = s.claim_amount_inr || 1500;
  document.getElementById("days_since_purchase").value = s.days_since_purchase || 100;
  document.getElementById("customer_prior_claims").value = s.customer_prior_claims || 0;
  document.getElementById("photo_attached").value = s.photo_attached || "Y";
  document.getElementById("partner_inspected").value = s.partner_inspected || "Y";
  document.getElementById("claim_description").value = s.claim_description || "unit not heating";
  document.getElementById("inspector_note").value = s.inspector_note || "";

  submitCurrentForm();
}

async function handleClaimSubmit(event) {
  if (event) event.preventDefault();
  await submitCurrentForm();
}

async function submitCurrentForm() {
  const submitBtn = document.getElementById("submitBtn");
  if (submitBtn) submitBtn.disabled = true;

  const payload = {
    claim_id: document.getElementById("claim_id").value.trim(),
    submitted_at: document.getElementById("submitted_at").value.trim(),
    partner_id: document.getElementById("partner_id").value.trim(),
    sku: document.getElementById("sku").value.trim(),
    product_serial: document.getElementById("product_serial").value.trim(),
    claim_amount_inr: parseFloat(document.getElementById("claim_amount_inr").value) || 0,
    days_since_purchase: parseInt(document.getElementById("days_since_purchase").value) || 0,
    customer_prior_claims: parseInt(document.getElementById("customer_prior_claims").value) || 0,
    photo_attached: document.getElementById("photo_attached").value,
    partner_inspected: document.getElementById("partner_inspected").value,
    claim_description: document.getElementById("claim_description").value.trim(),
    inspector_note: document.getElementById("inspector_note").value.trim(),
    source: "crm"
  };

  try {
    const res = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(`Server returned ${res.status}`);
    }

    const data = await res.json();
    updateVerdictUI(data);
  } catch (err) {
    console.error("Prediction error:", err);
    alert("Error scoring claim: " + err.message);
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

function updateVerdictUI(data) {
  // Claim Badge
  document.getElementById("claimIdBadge").textContent = data.claim_id || "CLAIM";

  // Score value
  const score = data.score || 0;
  document.getElementById("scoreValue").textContent = score.toFixed(3);

  // SVG Gauge Animation (Circumference: 2 * PI * 50 ~= 314.15)
  const circumference = 314.15;
  const offset = circumference * (1 - score);
  const gaugeFill = document.getElementById("gaugeFill");
  gaugeFill.style.strokeDashoffset = offset;

  // Gauge & Badge Colors
  const badge = document.getElementById("decisionBadge");
  badge.className = "decision-badge";

  if (score >= 0.70) {
    gaugeFill.style.stroke = "var(--status-red)";
    badge.classList.add("high");
    badge.textContent = "HOLD & INVESTIGATE";
  } else if (score >= 0.35) {
    gaugeFill.style.stroke = "var(--status-amber)";
    badge.classList.add("medium");
    badge.textContent = "DESK REVIEW QUEUE";
  } else {
    gaugeFill.style.stroke = "var(--status-green)";
    badge.classList.add("low");
    badge.textContent = "AUTO APPROVE";
  }

  // Recommended Action
  document.getElementById("decisionAction").textContent = data.recommended_action || "";

  // Financial Strip
  document.getElementById("finClaimAmt").textContent = "₹" + (data.claim_amount_inr || 0).toLocaleString("en-IN");
  document.getElementById("finExposure").textContent = "₹" + (data.potential_fraud_exposure_inr || 0).toLocaleString("en-IN");
  document.getElementById("finGoodwill").textContent = "₹" + (data.goodwill_risk_inr || 0).toLocaleString("en-IN");

  // Reasons list
  const reasonsList = document.getElementById("reasonsList");
  reasonsList.innerHTML = "";
  if (data.reasons && data.reasons.length > 0) {
    data.reasons.forEach(r => {
      const li = document.createElement("li");
      li.textContent = r;
      reasonsList.appendChild(li);
    });
  } else {
    const li = document.createElement("li");
    li.textContent = "Claim verified within standard operational limits.";
    reasonsList.appendChild(li);
  }
}

async function fetchTopQueue() {
  const tbody = document.getElementById("queueTableBody");
  try {
    tbody.innerHTML = `<tr><td colspan="10" class="loading-cell">Refreshing queue from predictions.csv...</td></tr>`;
    const res = await fetch("/api/top_flagged");
    const data = await res.json();
    const rows = data.top_flagged || [];

    if (rows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="10" class="loading-cell">No flagged claims available.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    rows.forEach((r, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>#${idx + 1}</strong></td>
        <td><strong>${r.claim_id}</strong></td>
        <td class="score-cell">${(r.score || 0).toFixed(4)}</td>
        <td>${r.partner_id}</td>
        <td>${r.sku}</td>
        <td><code>${r.product_serial}</code></td>
        <td>₹${(r.claim_amount_inr || 0).toLocaleString("en-IN")}</td>
        <td><span class="badge ${r.partner_inspected === 'Y' ? 'low' : 'high'}">${r.partner_inspected}</span></td>
        <td>${r.customer_prior_claims || 0}</td>
        <td><button class="btn-inspect-mini" onclick="loadQueueRow(${idx})">Inspect</button></td>
      `;
      tbody.appendChild(tr);
    });
    window.topQueueCache = rows;
  } catch (err) {
    console.error("Queue fetch error:", err);
    tbody.innerHTML = `<tr><td colspan="10" class="loading-cell">Failed to load queue.</td></tr>`;
  }
}

function loadQueueRow(idx) {
  if (!window.topQueueCache || !window.topQueueCache[idx]) return;
  const r = window.topQueueCache[idx];

  document.getElementById("claim_id").value = r.claim_id || "";
  document.getElementById("submitted_at").value = r.submitted_at || "";
  document.getElementById("partner_id").value = r.partner_id || "";
  document.getElementById("sku").value = r.sku || "KH-AF-01";
  document.getElementById("product_serial").value = r.product_serial || "";
  document.getElementById("claim_amount_inr").value = r.claim_amount_inr || 0;
  document.getElementById("days_since_purchase").value = r.days_since_purchase || 0;
  document.getElementById("customer_prior_claims").value = r.customer_prior_claims || 0;
  document.getElementById("photo_attached").value = r.photo_attached || "Y";
  document.getElementById("partner_inspected").value = r.partner_inspected || "Y";
  document.getElementById("claim_description").value = r.claim_description || "";
  document.getElementById("inspector_note").value = r.inspector_note || "";

  window.scrollTo({ top: 0, behavior: "smooth" });
  submitCurrentForm();
}
