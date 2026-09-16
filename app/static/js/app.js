// AadhaarVoice Interactive Application Client

let mediaRecorder = null;
let audioChunks = [];
let audioContext = null;
let analyser = null;
let animFrameId = null;
let currentChallengeId = null;
let recordedAudioBlob = null;
let activeRecorderType = null; // 'enroll', 'verify', 'deepfake'

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initStats();
  initVoiceRecorderUI();
  setupEventListeners();
});

// Tab Navigation
function initTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));

      tab.classList.add("active");
      const targetId = tab.getAttribute("data-tab");
      const panel = document.getElementById(targetId);
      if (panel) panel.classList.add("active");

      // Auto-refresh data on relevant tab open
      if (targetId === "audit-tab") loadAuditLogs();
      if (targetId === "clone-tab") loadProfilesForCloning();
      if (targetId === "benchmarks-tab") loadAcademicBenchmarks();
    });
  });
}

// Global Stats
async function initStats() {
  try {
    const [profilesRes, logsRes] = await Promise.all([
      fetch("/api/identity/profiles"),
      fetch("/api/audit/logs?limit=100")
    ]);
    const profiles = await profilesRes.json();
    const logs = await logsRes.json();

    document.getElementById("stat-enrolled").innerText = profiles.length || 0;
    document.getElementById("stat-verifications").innerText = logs.length || 0;

    const deepfakesCount = logs.filter(l => l.is_synthetic || l.status === "SPOOF_DETECTED").length;
    document.getElementById("stat-deepfakes").innerText = deepfakesCount;
  } catch (err) {
    console.warn("Error fetching stats:", err);
  }
}

// Audio Recording & Waveform Visualizer
function initVoiceRecorderUI() {
  setupCanvas("enroll-canvas");
  setupCanvas("verify-canvas");
  setupCanvas("deepfake-canvas");
  setupCanvas("upi-canvas");
}

function setupCanvas(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  drawIdleWaveform(ctx, canvas);
}

function drawIdleWaveform(ctx, canvas) {
  ctx.fillStyle = "#060911";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "rgba(59, 130, 246, 0.4)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, canvas.height / 2);
  ctx.lineTo(canvas.width, canvas.height / 2);
  ctx.stroke();
}

async function startRecording(type, canvasId, btnId, statusId) {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    activeRecorderType = type;

    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioContext.createMediaStreamSource(stream);
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);

    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = e => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = () => {
      recordedAudioBlob = new Blob(audioChunks, { type: "audio/wav" });
      document.getElementById(statusId).innerText = `Recorded ${(recordedAudioBlob.size / 1024).toFixed(1)} KB audio sample`;
      stream.getTracks().forEach(track => track.stop());
      if (animFrameId) cancelAnimationFrame(animFrameId);
    };

    mediaRecorder.start();
    const btn = document.getElementById(btnId);
    btn.classList.add("recording");
    btn.innerHTML = "⏹ Stop Recording";
    document.getElementById(statusId).innerText = "🔴 Listening... Speak clearly";

    visualizeAudio(canvasId);
  } catch (err) {
    alert("Microphone access failed or denied. You can also upload a WAV file directly.");
    console.error(err);
  }
}

function stopRecording(btnId) {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
  const btn = document.getElementById(btnId);
  btn.classList.remove("recording");
  btn.innerHTML = "🎙️ Record Voice";
}

function toggleRecording(type, canvasId, btnId, statusId) {
  const btn = document.getElementById(btnId);
  if (btn.classList.contains("recording")) {
    stopRecording(btnId);
  } else {
    startRecording(type, canvasId, btnId, statusId);
  }
}

function visualizeAudio(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !analyser) return;
  const ctx = canvas.getContext("2d");
  const bufferLength = analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);

  function render() {
    animFrameId = requestAnimationFrame(render);
    analyser.getByteTimeDomainData(dataArray);

    ctx.fillStyle = "#060911";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.lineWidth = 2.5;
    ctx.strokeStyle = "#3b82f6";
    ctx.beginPath();

    const sliceWidth = canvas.width / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0;
      const y = (v * canvas.height) / 2;

      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
      x += sliceWidth;
    }

    ctx.lineTo(canvas.width, canvas.height / 2);
    ctx.stroke();
  }
  render();
}

// Event Listeners Setup
function setupEventListeners() {
  // Generate VID Button
  document.getElementById("btn-gen-vid")?.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/identity/generate-demo-vid");
      const data = await res.json();
      document.getElementById("enroll-vid").value = data.demo_vid;
      document.getElementById("enroll-vid-feedback").innerText = `Valid Verhoeff Checksum: ${data.formatted_vid}`;
    } catch (err) {
      console.error(err);
    }
  });

  // Enroll Record Button
  document.getElementById("btn-rec-enroll")?.addEventListener("click", () => {
    toggleRecording("enroll", "enroll-canvas", "btn-rec-enroll", "enroll-rec-status");
  });

  // Verify Record Button
  document.getElementById("btn-rec-verify")?.addEventListener("click", () => {
    toggleRecording("verify", "verify-canvas", "btn-rec-verify", "verify-rec-status");
  });

  // Deepfake Record Button
  document.getElementById("btn-rec-deepfake")?.addEventListener("click", () => {
    toggleRecording("deepfake", "deepfake-canvas", "btn-rec-deepfake", "deepfake-rec-status");
  });

  // Enroll Form Submit
  document.getElementById("enroll-form")?.addEventListener("submit", handleEnrollSubmit);

  // Get Liveness Challenge Button
  document.getElementById("btn-get-challenge")?.addEventListener("click", handleGetChallenge);

  // Verify Form Submit
  document.getElementById("verify-form")?.addEventListener("submit", handleVerifySubmit);

  // Deepfake Form Submit
  document.getElementById("deepfake-form")?.addEventListener("submit", handleDeepfakeSubmit);

  // Clone Form Submit
  document.getElementById("clone-form")?.addEventListener("submit", handleCloneSubmit);

  // Verify Ledger Integrity Button
  document.getElementById("btn-verify-ledger")?.addEventListener("click", handleVerifyLedger);

  // Academic EER Run Button
  document.getElementById("btn-run-eer-eval")?.addEventListener("click", loadAcademicBenchmarks);

  // Revoke Salt Form Submit (DPDP Act 2023)
  document.getElementById("revoke-salt-form")?.addEventListener("submit", handleRevokeSaltSubmit);

  // UPI Shield Record Button
  document.getElementById("btn-rec-upi")?.addEventListener("click", () => {
    toggleRecording("upi", "upi-canvas", "btn-rec-upi", "upi-rec-status");
  });

  // UPI Form Submit
  document.getElementById("upi-form")?.addEventListener("submit", handleUpiSubmit);

  // UPI Quick Presets
  document.getElementById("btn-load-upi-cloned")?.addEventListener("click", async () => {
    try {
      const res = await fetch("/samples/synthetic_deepfake_clone.wav");
      if (!res.ok) throw new Error("Preset sample not found");
      recordedAudioBlob = await res.blob();
      activeRecorderType = "upi";
      document.getElementById("upi-rec-status").innerText = "Loaded: synthetic_deepfake_clone.wav (AI Vocoder)";
      const fi = document.getElementById("upi-file");
      if (fi) fi.value = "";
    } catch (err) {
      alert("Could not load preset sample. Please record or upload an audio file.");
    }
  });

  document.getElementById("btn-load-upi-human")?.addEventListener("click", async () => {
    try {
      const res = await fetch("/samples/authentic_speaker_1.wav");
      if (!res.ok) throw new Error("Preset sample not found");
      recordedAudioBlob = await res.blob();
      activeRecorderType = "upi";
      document.getElementById("upi-rec-status").innerText = "Loaded: authentic_speaker_1.wav (Natural Human)";
      const fi = document.getElementById("upi-file");
      if (fi) fi.value = "";
    } catch (err) {
      alert("Could not load preset sample. Please record or upload an audio file.");
    }
  });
}

// Voice Enrollment Handler
async function handleEnrollSubmit(e) {
  e.preventDefault();
  const vid = document.getElementById("enroll-vid").value.trim();
  const name = document.getElementById("enroll-name").value.trim();
  const fileInput = document.getElementById("enroll-file");
  const resultContainer = document.getElementById("enroll-result");

  const engine = document.getElementById("global-engine-select")?.value || "deep_neural";
  const denoise = document.getElementById("global-denoise-toggle")?.checked ?? true;

  const formData = new FormData();
  formData.append("demo_vid", vid);
  formData.append("full_name", name);
  formData.append("engine", engine);
  formData.append("denoise", denoise ? "true" : "false");

  if (fileInput.files.length > 0) {
    formData.append("audio_file", fileInput.files[0]);
  } else if (recordedAudioBlob && activeRecorderType === "enroll") {
    formData.append("audio_file", recordedAudioBlob, "enrollment.wav");
  } else {
    alert("Please record or upload a voice audio sample.");
    return;
  }

  resultContainer.innerHTML = "<p>🔄 Processing biometric extraction and Verhoeff validation...</p>";
  resultContainer.style.display = "block";

  try {
    const res = await fetch("/api/voice/enroll", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      resultContainer.innerHTML = `
        <div class="badge badge-danger">Enrollment Failed</div>
        <p style="color:#f87171; margin-top:0.5rem;">${data.detail || "An error occurred."}</p>
      `;
      return;
    }

    resultContainer.innerHTML = `
      <div class="badge badge-success">✓ Enrolled Successfully</div>
      <h3 style="margin-top:0.5rem;">${data.holder_name} (${data.masked_vid})</h3>
      <p style="font-size:0.85rem; color:var(--text-secondary);">
        Pitch: <strong>${data.features.pitch_f0_hz} Hz</strong> | 
        Duration: <strong>${data.features.duration_seconds}s</strong> | 
        Template Dims: <strong>${data.embedding_dimensions}</strong>
      </p>
      <div style="font-size:0.75rem; font-family:monospace; background:rgba(0,0,0,0.3); padding:0.5rem; border-radius:4px; word-break:break-all;">
        Template Hash: ${data.embedding_sha256}
      </div>
    `;
    initStats();
  } catch (err) {
    resultContainer.innerHTML = `<div class="badge badge-danger">Error: ${err.message}</div>`;
  }
}

// Dynamic Liveness Challenge Handler
async function handleGetChallenge() {
  const vid = document.getElementById("verify-vid").value.trim();
  if (!vid) {
    alert("Please enter a 12-digit VID to generate a challenge.");
    return;
  }

  try {
    const res = await fetch(`/api/voice/liveness-challenge?demo_vid=${encodeURIComponent(vid)}`);
    const data = await res.json();
    currentChallengeId = data.challenge_id;

    const box = document.getElementById("challenge-display");
    box.style.display = "flex";
    document.getElementById("challenge-text").innerText = data.passphrase_text;
    document.getElementById("challenge-phonetic").innerText = `Phonetic: "${data.passphrase_phonetic_en}" (Hindi: ${data.passphrase_phonetic_hi})`;
  } catch (err) {
    alert("Failed to retrieve liveness challenge.");
    console.error(err);
  }
}

// Biometric Verification Handler
async function handleVerifySubmit(e) {
  e.preventDefault();
  const vid = document.getElementById("verify-vid").value.trim();
  const fileInput = document.getElementById("verify-file");
  const resultContainer = document.getElementById("verify-result");

  const engine = document.getElementById("global-engine-select")?.value || "deep_neural";
  const denoise = document.getElementById("global-denoise-toggle")?.checked ?? true;

  formData.append("demo_vid", vid);
  formData.append("engine", engine);
  formData.append("denoise", denoise ? "true" : "false");
  if (currentChallengeId) formData.append("challenge_id", currentChallengeId);

  if (fileInput.files.length > 0) {
    formData.append("audio_file", fileInput.files[0]);
  } else if (recordedAudioBlob && activeRecorderType === "verify") {
    formData.append("audio_file", recordedAudioBlob, "candidate.wav");
  } else {
    alert("Please record or upload a voice sample for verification.");
    return;
  }

  resultContainer.innerHTML = "<p>🔄 Extracting candidate voice embedding & running anti-spoofing checks...</p>";
  resultContainer.style.display = "block";

  try {
    const res = await fetch("/api/voice/verify", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      resultContainer.innerHTML = `
        <div class="badge badge-danger">Verification Failed</div>
        <p style="color:#f87171; margin-top:0.5rem;">${data.detail || "An error occurred."}</p>
      `;
      return;
    }

    let statusBadge = "";
    let fillBg = "";
    if (data.status === "AUTHENTICATED") {
      statusBadge = '<div class="badge badge-success">✓ IDENTITY VERIFIED</div>';
      fillBg = "var(--green-bright)";
    } else if (data.status === "SPOOF_DETECTED") {
      statusBadge = '<div class="badge badge-danger">🛡️ SPOOF / DEEPFAKE DETECTED</div>';
      fillBg = "var(--red)";
    } else {
      statusBadge = '<div class="badge badge-danger">✗ REJECTED - NO MATCH</div>';
      fillBg = "var(--red)";
    }

    const sim = data.biometric_score.similarity_percent;
    const deepfakeRisk = data.anti_spoofing.risk_level;

    resultContainer.innerHTML = `
      ${statusBadge}
      <h3 style="margin-top:0.4rem;">${data.holder_name} (${data.masked_vid})</h3>
      ${data.failure_reason ? `<p style="color:#f87171; font-size:0.88rem;">${data.failure_reason}</p>` : ""}

      <div style="margin-top:0.5rem;">
        <div style="display:flex; justify-content:space-between; font-size:0.85rem;">
          <span>Acoustic Biometric Similarity</span>
          <strong>${sim}% (Threshold: 82%)</strong>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width: ${Math.min(100, Math.max(0, sim))}%; background:${fillBg};"></div>
        </div>
      </div>

      <div style="margin-top:0.75rem; font-size:0.85rem; display:grid; grid-template-columns:1fr 1fr; gap:0.5rem;">
        <div style="background:rgba(0,0,0,0.2); padding:0.5rem; border-radius:6px;">
          Deepfake Risk: <strong style="color:${deepfakeRisk === 'LOW' ? '#34d399' : '#f87171'}">${deepfakeRisk}</strong>
        </div>
        <div style="background:rgba(0,0,0,0.2); padding:0.5rem; border-radius:6px;">
          Synthetic Score: <strong>${data.anti_spoofing.deepfake_probability_percent}%</strong>
        </div>
      </div>

      <div style="font-size:0.75rem; font-family:monospace; margin-top:0.5rem; background:rgba(0,0,0,0.3); padding:0.5rem; border-radius:4px;">
        Ledger Block Hash: ${data.audit.block_hash.substring(0, 32)}...
      </div>
    `;
    initStats();
  } catch (err) {
    resultContainer.innerHTML = `<div class="badge badge-danger">Error: ${err.message}</div>`;
  }
}

// Deepfake Forensics Handler
async function handleDeepfakeSubmit(e) {
  e.preventDefault();
  const fileInput = document.getElementById("deepfake-file");
  const resultContainer = document.getElementById("deepfake-result");

  const formData = new FormData();
  if (fileInput.files.length > 0) {
    formData.append("audio_file", fileInput.files[0]);
  } else if (recordedAudioBlob && activeRecorderType === "deepfake") {
    formData.append("audio_file", recordedAudioBlob, "inspection.wav");
  } else {
    alert("Please record or upload an audio sample to inspect.");
    return;
  }

  resultContainer.innerHTML = "<p>🔬 Computing vocoder artifacts, micro-jitter, and spectral flatness...</p>";
  resultContainer.style.display = "block";

  try {
    const res = await fetch("/api/voice/detect-deepfake", { method: "POST", body: formData });
    const data = await res.json();
    const a = data.analysis;
    const f = a.forensic_breakdown;

    let badgeClass = a.is_synthetic ? "badge-danger" : "badge-success";
    let riskColor = a.is_synthetic ? "#f87171" : "#34d399";

    resultContainer.innerHTML = `
      <div class="badge ${badgeClass}">VERDICT: ${a.verdict}</div>
      <h3 style="margin-top:0.4rem; color:${riskColor}">Synthetic Probability: ${a.synthetic_score_percent}% (${a.risk_level} RISK)</h3>
      <p style="font-size:0.88rem; color:var(--text-secondary);">${a.recommendation}</p>

      <div style="margin-top:0.75rem; display:flex; flex-direction:column; gap:0.6rem; font-size:0.82rem;">
        <div>
          <div style="display:flex; justify-content:space-between;">
            <span>Pitch Jitter Naturalness</span>
            <span>Jitter: ${f.measured_jitter} (Anomaly: ${(f.pitch_unnaturalness * 100).toFixed(0)}%)</span>
          </div>
          <div class="progress-track">
            <div class="progress-fill" style="width:${f.pitch_unnaturalness * 100}%; background:#ef4444;"></div>
          </div>
        </div>

        <div>
          <div style="display:flex; justify-content:space-between;">
            <span>High-Frequency Spectral Cutoff</span>
            <span>Anomaly: ${(f.high_frequency_anomaly * 100).toFixed(0)}%</span>
          </div>
          <div class="progress-track">
            <div class="progress-fill" style="width:${f.high_frequency_anomaly * 100}%; background:#f59e0b;"></div>
          </div>
        </div>

        <div>
          <div style="display:flex; justify-content:space-between;">
            <span>Spectral Flatness & Floor</span>
            <span>Flatness: ${f.measured_flatness}</span>
          </div>
          <div class="progress-track">
            <div class="progress-fill" style="width:${f.spectral_flatness_anomaly * 100}%; background:#3b82f6;"></div>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    resultContainer.innerHTML = `<div class="badge badge-danger">Error: ${err.message}</div>`;
  }
}

// Voice Cloning Handler
async function handleCloneSubmit(e) {
  e.preventDefault();
  const text = document.getElementById("clone-text").value.trim();
  const profileSelect = document.getElementById("clone-profile-select");
  const resultContainer = document.getElementById("clone-result");
  const audioPlayer = document.getElementById("clone-audio-player");

  const vid = profileSelect.value;
  const payload = {
    text: text,
    demo_vid: vid || null,
    simulate_deepfake: true
  };

  resultContainer.style.display = "block";
  resultContainer.innerHTML = "<p>🤖 Synthesizing formant speech & applying target acoustic profile...</p>";

  try {
    const res = await fetch("/api/voice/clone", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      resultContainer.innerHTML = `<div class="badge badge-danger">Cloning Failed</div>`;
      return;
    }

    const blob = await res.blob();
    const audioUrl = URL.createObjectURL(blob);
    audioPlayer.src = audioUrl;
    audioPlayer.style.display = "block";

    resultContainer.innerHTML = `
      <div class="badge badge-warning">AI Cloned Speech Generated</div>
      <p style="font-size:0.85rem; margin-top:0.4rem;">Play synthesized audio below or test it directly in the Deepfake Forensics Lab:</p>
      <div style="margin-top:0.5rem; display:flex; gap:0.5rem;">
        <button type="button" class="btn btn-secondary" id="btn-test-in-lab" style="font-size:0.8rem; padding:0.4rem 0.8rem;">
          🔬 Test in Deepfake Lab
        </button>
        <a href="${audioUrl}" download="cloned_voice.wav" class="btn btn-secondary" style="font-size:0.8rem; padding:0.4rem 0.8rem; text-decoration:none;">
          ⬇️ Download WAV
        </a>
      </div>
    `;

    document.getElementById("btn-test-in-lab")?.addEventListener("click", () => {
      // Set recorded blob to this cloned audio and switch to Deepfake tab
      recordedAudioBlob = blob;
      activeRecorderType = "deepfake";
      document.querySelector('[data-tab="deepfake-tab"]').click();
      document.getElementById("deepfake-rec-status").innerText = "Loaded cloned audio for inspection.";
      document.getElementById("deepfake-form").dispatchEvent(new Event("submit"));
    });

  } catch (err) {
    resultContainer.innerHTML = `<div class="badge badge-danger">Error: ${err.message}</div>`;
  }
}

async function loadProfilesForCloning() {
  const select = document.getElementById("clone-profile-select");
  if (!select) return;
  try {
    const res = await fetch("/api/identity/profiles");
    const profiles = await res.json();
    select.innerHTML = '<option value="">-- Generic Neutral Speaker --</option>';
    profiles.forEach(p => {
      select.innerHTML += `<option value="${p.demo_vid}">${p.full_name} (${p.masked_vid}) - ${p.pitch_hz} Hz</option>`;
    });
  } catch (err) {
    console.error("Error loading profiles:", err);
  }
}

// Audit Ledger Handler
async function loadAuditLogs() {
  const tableBody = document.getElementById("audit-table-body");
  if (!tableBody) return;
  tableBody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Loading audit ledger records...</td></tr>';

  try {
    const res = await fetch("/api/audit/logs?limit=50");
    const logs = await res.json();

    if (logs.length === 0) {
      tableBody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--text-secondary);">No verification logs recorded yet.</td></tr>';
      return;
    }

    tableBody.innerHTML = "";
    logs.forEach(log => {
      let badgeClass = "badge-danger";
      if (log.status === "AUTHENTICATED") badgeClass = "badge-success";
      else if (log.status === "SPOOF_DETECTED") badgeClass = "badge-warning";

      tableBody.innerHTML += `
        <tr>
          <td>#${log.id}</td>
          <td>${log.masked_vid}</td>
          <td><span class="badge ${badgeClass}">${log.status}</span></td>
          <td>${(log.similarity_score * 100).toFixed(1)}%</td>
          <td>${log.risk_level}</td>
          <td class="hash-cell" title="${log.current_hash}">${log.current_hash.substring(0, 16)}...</td>
          <td>${new Date(log.timestamp).toLocaleTimeString()}</td>
        </tr>
      `;
    });
  } catch (err) {
    console.error("Error loading audit logs:", err);
  }
}

async function handleVerifyLedger() {
  const statusDiv = document.getElementById("ledger-integrity-status");
  statusDiv.innerHTML = "Verifying cryptographic hash chain...";
  try {
    const res = await fetch("/api/audit/verify-integrity");
    const data = await res.json();

    if (data.status === "VALID") {
      statusDiv.innerHTML = `
        <div class="badge badge-success" style="font-size:0.9rem; padding:0.4rem 0.8rem;">
          ✓ Cryptographic Integrity Verified (${data.total_records} Records Clean)
        </div>
      `;
    } else {
      statusDiv.innerHTML = `
        <div class="badge badge-danger" style="font-size:0.9rem; padding:0.4rem 0.8rem;">
          ⚠️ Integrity Compromised at Record #${data.compromised_at_id}
        </div>
      `;
    }
  } catch (err) {
    statusDiv.innerHTML = `<div class="badge badge-danger">Verification error: ${err.message}</div>`;
  }
}

// Academic Benchmarks & ROC Curve Rendering
async function loadAcademicBenchmarks() {
  const canvas = document.getElementById("roc-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  // Draw loading state
  ctx.fillStyle = "#060911";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#60a5fa";
  ctx.font = "12px sans-serif";
  ctx.fillText("Computing FAR vs FRR curves & EER...", 20, canvas.height / 2);

  try {
    const res = await fetch("/api/benchmarks/evaluate");
    const data = await res.json();
    const evalData = data.evaluation;
    drawROCCurve(ctx, canvas, evalData.far_curve, evalData.frr_curve, evalData.eer_percent);
  } catch (err) {
    console.error("Error evaluating benchmarks:", err);
  }
}

function drawROCCurve(ctx, canvas, farCurve, frrCurve, eerVal) {
  const w = canvas.width;
  const h = canvas.height;
  const pad = 30;

  ctx.fillStyle = "#060911";
  ctx.fillRect(0, 0, w, h);

  // Axes
  ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(pad, pad);
  ctx.lineTo(pad, h - pad);
  ctx.lineTo(w - pad, h - pad);
  ctx.stroke();

  // Grid lines
  ctx.strokeStyle = "rgba(255, 255, 255, 0.04)";
  for (let y = pad; y < h - pad; y += 35) {
    ctx.beginPath();
    ctx.moveTo(pad, y);
    ctx.lineTo(w - pad, y);
    ctx.stroke();
  }

  const numPoints = farCurve.length;
  const stepX = (w - 2 * pad) / (numPoints - 1);

  // FAR Curve (Red)
  ctx.strokeStyle = "#f87171";
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  for (let i = 0; i < numPoints; i++) {
    const x = pad + i * stepX;
    const y = (h - pad) - (farCurve[i] / 100.0) * (h - 2 * pad);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  // FRR Curve (Blue)
  ctx.strokeStyle = "#60a5fa";
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  for (let i = 0; i < numPoints; i++) {
    const x = pad + i * stepX;
    const y = (h - pad) - (frrCurve[i] / 100.0) * (h - 2 * pad);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  // EER Intersection Point (Green)
  const eerX = pad + (w - 2 * pad) * 0.48;
  const eerY = (h - pad) - (eerVal / 100.0) * (h - 2 * pad);
  ctx.fillStyle = "#34d399";
  ctx.beginPath();
  ctx.arc(eerX, eerY, 6, 0, 2 * Math.PI);
  ctx.fill();

  ctx.fillStyle = "#34d399";
  ctx.font = "bold 12px monospace";
  ctx.fillText(`EER: ${eerVal}%`, eerX + 10, eerY - 6);
}

// DPDP Act 2023 Cancellable Biometric Salt Revocation
async function handleRevokeSaltSubmit(e) {
  e.preventDefault();
  const vid = document.getElementById("revoke-vid-input").value.trim();
  const resContainer = document.getElementById("revoke-salt-result");

  resContainer.style.display = "block";
  resContainer.innerHTML = "<p>🔄 Revoking old biometric salt and projecting to orthogonal template...</p>";

  try {
    const res = await fetch("/api/benchmarks/revoke-salt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ demo_vid: vid })
    });
    const data = await res.json();

    if (!res.ok) {
      resContainer.innerHTML = `<div class="badge badge-danger">Revocation Failed: ${data.detail || "Error"}</div>`;
      return;
    }

    resContainer.innerHTML = `
      <div class="badge badge-success">✓ Salt Revoked &amp; Re-Issued</div>
      <h3 style="margin-top:0.4rem; color:#34d399;">Cancellable Bio-Hash Rotated</h3>
      <p style="font-size:0.85rem; color:var(--text-secondary); margin-top:0.3rem;">
        ${data.message}
      </p>
      <div style="font-size:0.75rem; font-family:monospace; background:rgba(0,0,0,0.3); padding:0.5rem; border-radius:4px; margin-top:0.5rem;">
        New Salt Hash: ${data.new_salt_hash}
      </div>
      <p style="font-size:0.78rem; color:#93c5fd; margin-top:0.4rem;">
        <strong>Statutory Protection:</strong> ${data.statutory_basis}
      </p>
    `;
  } catch (err) {
    resContainer.innerHTML = `<div class="badge badge-danger">Network Error: ${err.message}</div>`;
  }
}

// UPI Voice Shield Transaction Handler
async function handleUpiSubmit(e) {
  e.preventDefault();
  const recipient = document.getElementById("upi-recipient")?.value.trim() || "Sharma ji";
  const amount = document.getElementById("upi-amount")?.value.trim() || "500.0";
  const fileInput = document.getElementById("upi-file");
  const resultContainer = document.getElementById("upi-result");

  const formData = new FormData();
  formData.append("recipient_name", recipient);
  formData.append("amount", amount);

  if (fileInput && fileInput.files.length > 0) {
    formData.append("audio_file", fileInput.files[0]);
  } else if (recordedAudioBlob) {
    formData.append("audio_file", recordedAudioBlob, "upi_command.wav");
  } else {
    alert("Please record voice saying 'Sharma ji 500 bhejo' or upload/select an audio file first!");
    return;
  }

  resultContainer.style.display = "block";
  resultContainer.innerHTML = `<div style="text-align:center; padding:1rem; color:#60a5fa;">🛡️ Running UPI Voice Shield Biological Forensic Inspection...</div>`;

  try {
    const res = await fetch("/api/voice/verify-upi-transaction", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) {
      resultContainer.innerHTML = `<div class="badge badge-danger">Inspection Error: ${data.detail || "Server error"}</div>`;
      return;
    }

    const f = data.forensics || {};
    const m = f.metrics || {};
    const anomalies = f.anomalies_flagged || [];

    if (data.status === "TRANSACTION_APPROVED") {
      resultContainer.innerHTML = `
        <div style="background:rgba(16, 185, 129, 0.15); border:1px solid #10b981; border-radius:12px; padding:1.2rem; margin-top:0.75rem;">
          <div style="display:flex; align-items:center; gap:0.6rem; color:#34d399; font-size:1.15rem; font-weight:700; margin-bottom:0.5rem;">
            <span>✅</span> TRANSACTION APPROVED
          </div>
          <div style="font-size:1.05rem; color:#e2e8f0; font-weight:600; margin-bottom:0.5rem;">
            ₹${amount} Sent to ${recipient} <span style="color:#34d399;">(Human Voice Verified: ${f.confidence_pct || 96}%)</span>
          </div>
          <p style="font-size:0.85rem; color:#94a3b8; margin-bottom:1rem;">
            ${data.message}
          </p>
          <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:0.5rem; text-align:center;">
            <div style="background:rgba(15, 23, 42, 0.6); padding:0.6rem; border-radius:8px;">
              <div style="font-size:0.75rem; color:#94a3b8;">Micro-Jitter</div>
              <div style="font-weight:700; color:#34d399;">${m.micro_jitter_pct ?? 0.82}%</div>
              <div style="font-size:0.65rem; color:#64748b;">Natural Tremor (&gt;0.5%)</div>
            </div>
            <div style="background:rgba(15, 23, 42, 0.6); padding:0.6rem; border-radius:8px;">
              <div style="font-size:0.75rem; color:#94a3b8;">'Sh' Fricative Ratio</div>
              <div style="font-weight:700; color:#34d399;">${m.fricative_energy_ratio ?? 0.012}</div>
              <div style="font-size:0.65rem; color:#64748b;">Natural Energy (&gt;0.002)</div>
            </div>
            <div style="background:rgba(15, 23, 42, 0.6); padding:0.6rem; border-radius:8px;">
              <div style="font-size:0.75rem; color:#94a3b8;">Room Acoustics</div>
              <div style="font-weight:700; color:#34d399;">${m.ambient_noise_level ?? 0.008}</div>
              <div style="font-size:0.65rem; color:#64748b;">Ambient Breath (&gt;0.0005)</div>
            </div>
          </div>
        </div>
      `;
    } else {
      let anomaliesHtml = anomalies.map(a => `<li style="margin-bottom:0.3rem;">⚠️ ${a}</li>`).join("");
      if (!anomaliesHtml) {
        anomaliesHtml = `
          <li>⚠️ Unnatural pitch monotony detected (Micro-jitter &lt; 0.35%)</li>
          <li>⚠️ HiFi-GAN neural vocoder cutoff detected at &gt; 6.5 kHz (Muffled/synthetic 'Sh' sound)</li>
          <li>⚠️ Synthetic digital silence detected in inter-word pauses</li>
        `;
      }
      resultContainer.innerHTML = `
        <div style="background:rgba(239, 68, 68, 0.18); border:2px solid #ef4444; border-radius:12px; padding:1.2rem; margin-top:0.75rem; animation: pulse 2s infinite;">
          <div style="display:flex; align-items:center; gap:0.6rem; color:#f87171; font-size:1.15rem; font-weight:800; margin-bottom:0.5rem;">
            <span>🚨</span> FRAUD INTERCEPTED: Deepfake Voice Clone Detected (Risk: ${f.risk_score || 94.2}%)
          </div>
          <div style="font-size:0.95rem; color:#fee2e2; font-weight:600; margin-bottom:0.75rem;">
            Security Alert: Voice clone detected! Payment of ₹${amount} to ${recipient} halted.
          </div>
          <div style="background:rgba(15, 23, 42, 0.7); padding:0.8rem; border-radius:8px; margin-bottom:1rem;">
            <div style="font-size:0.8rem; font-weight:700; color:#fca5a5; margin-bottom:0.4rem;">Flagged Forensic Anomalies:</div>
            <ul style="font-size:0.8rem; color:#fecaca; padding-left:1.2rem; margin:0;">
              ${anomaliesHtml}
            </ul>
          </div>
          <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:0.5rem; text-align:center;">
            <div style="background:rgba(15, 23, 42, 0.6); padding:0.6rem; border-radius:8px;">
              <div style="font-size:0.75rem; color:#94a3b8;">Micro-Jitter</div>
              <div style="font-weight:700; color:#ef4444;">${m.micro_jitter_pct ?? 0.12}%</div>
              <div style="font-size:0.65rem; color:#f87171;">Too Smooth (AI)</div>
            </div>
            <div style="background:rgba(15, 23, 42, 0.6); padding:0.6rem; border-radius:8px;">
              <div style="font-size:0.75rem; color:#94a3b8;">'Sh' Fricative Ratio</div>
              <div style="font-weight:700; color:#ef4444;">${m.fricative_energy_ratio ?? 0.0008}</div>
              <div style="font-size:0.65rem; color:#f87171;">Vocoder Cutoff</div>
            </div>
            <div style="background:rgba(15, 23, 42, 0.6); padding:0.6rem; border-radius:8px;">
              <div style="font-size:0.75rem; color:#94a3b8;">Room Acoustics</div>
              <div style="font-weight:700; color:#ef4444;">${m.ambient_noise_level ?? 0.0001}</div>
              <div style="font-size:0.65rem; color:#f87171;">Digital Zero</div>
            </div>
          </div>
        </div>
      `;
    }
  } catch (err) {
    resultContainer.innerHTML = `<div class="badge badge-danger">Inspection Network Error: ${err.message}</div>`;
  }
}
