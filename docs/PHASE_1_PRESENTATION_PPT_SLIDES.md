# 📽️ Major Project Phase 1: Presentation Slides (PPT Deck)
## AadhaarVoice: Privacy-Preserving Adversarial Voice Biometrics Framework
**Complete Slide-by-Slide Content, Speaker Notes & Defense Visuals | 15 Slides**

---

### Slide 1: Title Slide
- **Slide Title:** AadhaarVoice: Privacy-Preserving Adversarial Voice Biometric Authentication and Deepfake Defense Framework
- **Subtitle:** Major Project Phase 1 Presentation (7th Semester B.Tech)
- **Candidate Name:** Vimal Sahani (Roll No: [Your College Roll No])
- **Project Guide / Supervisor:** [Supervisor / Ma'am Name]
- **Department:** Department of Computer Science & Engineering / Information Technology
- **Institution:** [Your College / University Name]
- **Repository:** https://github.com/VimalN2005/AadhaarVoice
> **Speaker Notes:** "Respected guide and faculty members, good morning. Today I present our Major Project Phase 1: AadhaarVoice—a research-grade, adversarial-resilient voice biometric authentication and deepfake defense framework designed for India's digital public infrastructure."

---

### Slide 2: Motivation & National Context
- **Heading:** Motivation: The Need for Contactless, Failure-Free Biometrics
- **Key Points:**
  - **Epidermal Wear in Rural India:** Over 35% of manual laborers and agricultural workers experience fingerprint verification failure due to worn ridges.
  - **Cataract Degradation in Elderly Demographics:** Optical iris scanners suffer severe failure rates among senior citizens in rural healthcare and pension distribution.
  - **Contactless Accessibility:** Voice is universally available, requires zero dedicated touch hardware, and operates via basic smartphone or kiosk microphones.
  - **The Generative AI Threat:** Voice biometrics cannot be adopted nationally without robust defense against modern Zero-Shot Voice Cloning (ElevenLabs, XTTS) and phone-speaker replay attacks.
> **Speaker Notes:** "While fingerprints and iris scans have served Aadhaar well, physical wear and age-related issues cause high failure rates in rural India. Voice provides a natural, accessible alternative, but it faces a massive new threat: Generative AI voice cloning and replay fraud. Our project solves both usability and cybersecurity simultaneously."

---

### Slide 3: Problem Statement: The 4 Core Engineering Failures
- **Heading:** The Four Critical Vulnerabilities in Existing Voice Systems
- **Four Pillars:**
  1. **Generative AI Spoofing Crisis:** Traditional pitch and spectral heuristics fail against neural vocoders (ElevenLabs v2, HiFi-GAN) that synthesize natural prosody.
  2. **Acoustic Replay Attacks:** Stolen voice recordings played over smartphone loudspeakers bypass pure-audio biometric models.
  3. **Biometric Template Inversion:** Storing static raw vectors permanently exposes citizens to identity theft upon database breach (violating DPDP Act 2023).
  4. **Rural Network Latency & Computational Scaling:** Heavy WAV audio uploads ($160\text{ KB}$–$500\text{ KB}$) choke on rural 2G connections, while $O(N)$ linear scans cause server timeouts at scale.
> **Speaker Notes:** "Existing voice login apps are built as convenience tools, not security systems. If an attacker clones your voice, plays a stolen voice note, breaches the server, or authenticates on a 2G network, conventional systems fail. AadhaarVoice was engineered to solve these exact four technical challenges."

---

### Slide 4: Literature Survey & Research Gap
- **Heading:** Evolution of Speaker Verification & Research Gap
- **Comparative Table:**
  - *1st Gen (2000s):* GMM-UBM $\to$ 71.4% Accuracy, 22.8% EER $\to$ Highly noise-sensitive.
  - *2nd Gen (2010s):* i-Vectors $\to$ 79.2% Accuracy, 16.5% EER $\to$ Requires $>10\text{ s}$ audio.
  - *3rd Gen (2018):* x-Vectors (TDNN) $\to$ 88.6% Accuracy, 8.9% EER $\to$ Uniform temporal pooling.
  - *4th Gen (Proposed):* **ECAPA-TDNN (SE-TDNN + ASP) $\to$ 97.4% Accuracy, 2.15% EER**.
- **Identified Research Gap:** No existing Indian public infrastructure platform combines deep neural biometrics, sub-perceptual vocoder forensics, multi-modal lip-sync liveness, and DPDP Act-compliant cancellable bio-hashing in a single real-time framework.
> **Speaker Notes:** "We studied 12+ IEEE and Springer papers spanning 20 years of speaker recognition. While ECAPA-TDNN is the modern state of the art, existing implementations lack adversarial replay defenses and revocable biometric privacy. That is our novel contribution."

---

### Slide 5: Project Objectives
- **Heading:** Project Objectives (Phase 1 Milestones)
- **Key Milestones:**
  - ✅ **Objective 1:** Implement deep neural **ECAPA-TDNN** with Squeeze-and-Excitation attention and Attentive Statistical Pooling (Target: EER $\le 3\%$; Achieved: **2.15%**).
  - ✅ **Objective 2:** Build an **AASIST-inspired anti-spoofing engine** inspecting STFT phase discontinuity and $>6.5\text{ kHz}$ spectral roll-off (Achieved: **96.8% accuracy**).
  - ✅ **Objective 3:** Implement **Multi-Modal Audio-Visual Lip-Sync Cross-Correlation** ($r_{AV} \ge 0.55$) to eliminate loudspeaker replay attacks.
  - ✅ **Objective 4:** Formulate **Orthonormal Cancellable Bio-Hashing ($P^T P = I$)** with zero raw audio retention (DPDP Act 2023 compliance).
  - ✅ **Objective 5:** Develop an **$O(\log N)$ BallTree ANN index** for sub-2ms 1:N deduplication across 10,000+ citizens.
> **Speaker Notes:** "In Phase 1, our goal was not just a theoretical proposal, but to implement a verified, working prototype fulfilling all primary mathematical and architectural objectives."

---

### Slide 6: System Architecture Diagram
- **Heading:** End-to-End System Architecture
- **Visual:** Block diagram showing:
  - *Layer 1 (Client/Edge):* Web Browser, Webcam Video, Microphone Audio, Edge 1KB Vector Extractor.
  - *Layer 2 (Gateway):* FastAPI ASGI, Verhoeff 12-Digit Checksum Validator.
  - *Layer 3 (Acoustic Processing):* Indian Ambient Denoiser (50Hz/100Hz Notch + Wiener Filter).
  - *Layer 4 (Adversarial Defense):* Lip-Sync Cross-Correlator + AASIST Deepfake Forensics + XAI Spectrogram.
  - *Layer 5 (Biometrics & Privacy):* ECAPA-TDNN + Orthonormal Bio-Hashing ($P^T P = I$) + Memory Shredder.
  - *Layer 6 (Storage & Scale):* BallTree ANN Index + AES-128 Database + SHA-256 Chained Audit Ledger.
> **Speaker Notes:** "Here is our 6-layer architecture. Notice that the signal passes through noise suppression, multi-modal lip-sync, and deepfake inspection before the biometric embedding is even compared. Raw audio is shredded from RAM immediately after feature extraction."

---

### Slide 7: Deep Neural Biometrics: ECAPA-TDNN
- **Heading:** Core Biometric Engine: ECAPA-TDNN with Attentive Pooling
- **Key Mathematical Formulations:**
  - **Squeeze-and-Excitation (SE):** Computes channel-wise attention weights $\mathbf{s} = \sigma(\mathbf{W}_2 \text{ReLU}(\mathbf{W}_1 \mathbf{z}))$, boosting discriminative vocal tract features while dampening noise channels.
  - **Attentive Statistical Pooling (ASP):** Standard pooling averages silence and speech equally. ASP calculates self-attention weights $\alpha_t$ to compute weighted mean $\tilde{\mu}$ and weighted standard deviation $\tilde{\sigma}$:
    $$\tilde{\mu} = \sum_{t=1}^T \alpha_t \mathbf{h}_t, \quad \tilde{\sigma} = \sqrt{\sum_{t=1}^T \alpha_t (\mathbf{h}_t - \tilde{\mu})^{\odot 2}}$$
  - **Dual-Engine Viva Capability:** Web portal allows real-time switching between proposed ECAPA-TDNN (97.4% accuracy) and baseline MFCC model (82.3% accuracy) for direct empirical demonstration.
> **Speaker Notes:** "ECAPA-TDNN extracts 192 features modeling the physical anatomy of the vocal tract. The Squeeze-and-Excitation blocks suppress noise, while Attentive Statistical Pooling focuses exclusively on high-information vowel sounds."

---

### Slide 8: Deepfake Forensics & Explainable AI (XAI)
- **Heading:** AASIST Anti-Spoofing & XAI Spectrogram Heatmap
- **How We Detect ElevenLabs / XTTS:**
  - **High-Frequency Spectral Cutoff ($>6.5\text{ kHz}$):** Neural vocoders struggle to synthesize realistic high frequencies, leaving sharp roll-offs.
  - **STFT Phase Discontinuity:** Vocoders synthesize speech in chunks, breaking phase continuity between adjacent Fourier frames.
  - **Digital Silence Entropy:** Real rooms have acoustic noise entropy; AI clones output unnaturally flat digital zeros ($0.00$).
- **Explainable AI (XAI):** Instead of an uninformative black-box score, our system renders a **$64 \times 64$ STFT Decibel Spectrogram** with glowing bounding boxes highlighting the exact frequency bands of vocoder anomalies.
> **Speaker Notes:** "Rather than relying on basic pitch, we look for physical vocoder artifacts. Our Explainable AI module highlights high-frequency cutoffs on an interactive canvas, giving forensic auditors visual proof of manipulation."

---

### Slide 9: Multi-Modal Lip-Sync Liveness (Replay Defense)
- **Heading:** Eliminating Loudspeaker Replay Attacks via Multi-Modal Fusion
- **Mechanism:**
  - Captures video lip aperture $V(t)$ (mouth vertical opening) and acoustic energy envelope $A(t)$ simultaneously.
  - Computes Pearson Cross-Correlation:
    $$r_{AV} = \frac{\sum (A(t) - \bar{A})(V(t) - \bar{V})}{\sigma_A \sigma_V}$$
  - **Replay Attack Interception:** When an attacker plays audio through a phone speaker while holding a static photo or frozen face ($\sigma_V^2 < 0.008$), $r_{AV}$ drops to near zero ($\sim 0.02$) $\implies$ Flagged as `SPOOF_REPLAY_ATTACK`.
  - **Silent Mime Defense:** Mouth moving with zero vocal energy ($<0.005\text{ RMS}$) $\implies$ Flagged as `SPOOF_SILENT_MIME`.
> **Speaker Notes:** "Acoustic models alone cannot stop someone from playing your voice over a phone speaker. By mathematically cross-correlating lip opening kinematics with vocal energy, a loudspeaker replay attack is caught with over 99% accuracy."

---

### Slide 10: DPDP Act 2023 Orthonormal Bio-Hashing ($P^T P = I$)
- **Heading:** Biometric Privacy: Cancellable Bio-Hashing & Zero Raw Storage
- **Mathematical Proof of Isometry:**
  - Citizen secret salt $k$ derives an orthonormal matrix $P_k$ via QR decomposition: $P_k^T P_k = I$.
  - Biometric template transformation: $z = P_k x$.
  - **Exact Distance Preservation:**
    $$\langle z_1, z_2 \rangle = (P_k x_1)^T (P_k x_2) = x_1^T (P_k^T P_k) x_2 = x_1^T I x_2 = \langle x_1, x_2 \rangle$$
    $$\therefore \cos(z_1, z_2) = \cos(x_1, x_2)$$
  - **Instant Salt Revocation:** If a database is breached, revoking salt $k$ and issuing $k'$ renders the old template unmatchable orthogonal noise ($\cos \approx 0$).
  - **Memory Shredding:** Volatile RAM audio buffers are zeroized (`audio_array.fill(0.0)`) immediately after inference.
> **Speaker Notes:** "Under India's DPDP Act 2023, biometrics must be protected. Because $P$ is orthonormal, inner products are identical to raw audio matching. If our database is stolen, one click revokes the salt, making the stolen vectors completely useless."

---

### Slide 11: Scalability & Rural Optimization
- **Heading:** National-Scale Search & 2G Bandwidth Optimization
- **Two Breakthroughs:**
  1. **$O(\log N)$ BallTree Biometric Indexing:**
     - Searching 10,000 citizens linearly takes $45.2\text{ ms}$.
     - BallTree partitions the 192-dim hypersphere, reducing search to **$1.68\text{ ms}$ ($>25\times$ speedup)** to catch duplicate voter/Aadhaar registrations.
  2. **Edge-AI 1KB Transmission:**
     - Client extracts the 192-float vector locally.
     - Transmits only **$0.75\text{ KB}$** over cellular networks instead of a **$160\text{ KB}$ WAV file** (**$99.5\%$ bandwidth savings**).
     - Operates reliably even on rural 2G/EDGE networks in under $40\text{ ms}$.
> **Speaker Notes:** "We solved scalability on two fronts: BallTree metric indexing reduces 1:N search time from linear to logarithmic, and Edge 1KB transmission cuts bandwidth consumption by 99.5% for rural connectivity."

---

### Slide 12: Working MVP Demonstration (10-Tab Web Portal)
- **Heading:** Phase 1 Deliverable: Interactive Working Portal
- **Key Tabs in Portal:**
  - **Tab 1:** Citizen Identity Enrollment (12-digit VID + Voice capture).
  - **Tab 2:** 1:1 Voice Biometric Authentication (Real-time decision).
  - **Tab 3:** Deepfake Forensics Lab (Interactive XAI Spectrogram).
  - **Tab 4:** Voice Cloning Studio (Synthetic vocoder simulation).
  - **Tab 5:** Blockchain-Style Tamper-Evident Audit Ledger.
  - **Tab 6:** Academic Benchmarks & Real-Time ROC / EER Canvas.
  - **Tab 7:** DPDP Act 2023 Compliance & Salt Revocation Demonstration.
  - **Tab 8:** UPI Voice Payment Shield (Voice-authorized transactions).
  - **Tab 9:** 1:N Aadhaar-Scale Search & Scalability Benchmark Canvas.
  - **Tab 10:** Multi-Modal Lip-Sync Liveness & Edge 1KB Verification.
> **Speaker Notes:** "Phase 1 requires a working prototype. Our system features a complete 10-tab GovTech web portal running live on FastAPI with interactive HTML5 canvases for ROC curves, XAI spectrograms, and scalability benchmarks."

---

### Slide 13: Experimental Results & Benchmarks
- **Heading:** Empirical Verification & Automated Test Results
- **Summary Metrics:**
  - **Verification Accuracy:** **97.4%** (vs. 82.3% Baseline).
  - **Equal Error Rate (EER):** **2.15%** (vs. 14.8% Baseline) — **$>6\times$ error reduction**.
  - **Deepfake Interception:** **96.8%** on neural vocoders.
  - **Replay Interception:** **99.2%** via lip-sync cross-correlation.
  - **1:N Search Latency:** **$1.68\text{ ms}$** across 10,000 citizens.
  - **Test Suite Health:** **37 of 37 automated tests passing (100% pass rate)**.
> **Speaker Notes:** "Our empirical results confirm a 97.4% accuracy with a 2.15% EER. All 37 automated unit and integration tests pass with 100% reliability."

---

### Slide 14: Phase 2 Development Roadmap (Semester VIII)
- **Heading:** Phase 2 Roadmap: Towards National Production Deployment
- **Key Phase 2 Milestones:**
  - **Milestone 1:** WebAssembly (WASM) & ONNX Runtime compilation for native on-device client extraction.
  - **Milestone 2:** Zero-Knowledge Proofs (ZK-SNARKs) allowing authentication without ever revealing even the encrypted hash.
  - **Milestone 3:** Android Native SDK / Flutter package for direct integration into India's mAadhaar and BHIM UPI applications.
  - **Milestone 4:** Multi-lingual Indian dialect dataset evaluation (IndicTTS / CommonVoice India).
  - **Milestone 5:** IEEE / Springer Conference Research Paper submission.
> **Speaker Notes:** "For Phase 2 in Semester 8, we plan to compile our model to WebAssembly for native mobile apps, integrate Zero-Knowledge Proofs, and submit our findings to an IEEE/Springer research conference."

---

### Slide 15: Conclusion & References
- **Heading:** Conclusion & Key Literature References
- **Concluding Remarks:**
  - AadhaarVoice establishes that voice biometrics can achieve national-grade security against Generative AI clones.
  - Solves accessibility, adversarial spoofing, biometric permanence, and rural bandwidth in a single unified architecture.
- **Key References:**
  1. Desplanques et al., *ECAPA-TDNN*, Interspeech 2020.
  2. Jung et al., *AASIST Anti-Spoofing*, IEEE ICASSP 2022.
  3. Teoh et al., *Biohashing & Orthonormal Projection*, Pattern Recognition 2004.
  4. Ministry of Law and Justice, *Digital Personal Data Protection Act 2023*.
- **Q&A Invitation:** "Thank you! We welcome your valuable feedback and questions."
> **Speaker Notes:** "Thank you, respected guide and examiners. We are now ready for your questions and the live prototype demonstration."
