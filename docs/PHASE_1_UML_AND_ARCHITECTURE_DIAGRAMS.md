# 📐 System Architecture & UML Design Document
## AadhaarVoice: Comprehensive Diagrams & Database Specifications
**Major Project Phase 1 (Semester VII) | B.Tech Capstone Project**

---

## 📑 Diagram Index
1. **System Architecture Diagram** (Layered Deep-Tech Architecture)
2. **Use Case Diagram** (Actors & System Interactions)
3. **Data Flow Diagram (DFD) Level 0** (Context Level Diagram)
4. **Data Flow Diagram (DFD) Level 1** (Subsystem Decomposition)
5. **Data Flow Diagram (DFD) Level 2** (Detailed Verification Pipeline)
6. **Entity-Relationship (ER) Diagram** (Database Entities & Relationships)
7. **Class Diagram** (Core Classes, Attributes, and Methods)
8. **Sequence Diagram** (End-to-End Authentication Sequence)
9. **Activity Diagram** (Decision Workflow & Multi-Modal Liveness)
10. **Physical Database Schema** (Table Specifications & Constraints)

---

## 1. System Architecture Diagram

```mermaid
graph TD
    subgraph ClientLayer["🖥️ Presentation & Edge Layer"]
        UI["Web Portal / Mobile UI<br>(Vanilla JS, Web Audio API, Canvas)"]
        CamMic["Client Peripherals<br>(Webcam Video + Microphone Audio)"]
        EdgeExtract["Edge 1KB Feature Extractor<br>(Optional On-Device Extraction)"]
    end

    subgraph SecurityGateway["🛡️ Security & API Gateway"]
        FastAPI["FastAPI ASGI Server (Uvicorn)"]
        CORS["CORS & Rate Limiting"]
        VerhoeffCheck["Verhoeff Checksum Validator<br>(12-Digit VID Verification)"]
    end

    subgraph AudioProcessing["🌪️ Acoustic Signal Engineering"]
        IndianDenoiser["Indian Ambient Denoiser<br>(50Hz/100Hz IIR Notch + Wiener Filter)"]
        AudioPreprocessor["Audio Processor<br>(16kHz Resampling, Silence Trimmer)"]
    end

    subgraph MultiModal["🎥 Multi-Modal & Deepfake Defense"]
        LipSync["Lip-Sync Cross-Correlator<br>(r_AV >= 0.55, Replay Defense)"]
        AASIST["AASIST Anti-Spoofing Engine<br>(STFT Phase + >6.5kHz Cutoff)"]
        XAI["XAI Spectrogram Heatmap<br>(Time-Frequency Bounding Boxes)"]
    end

    subgraph BiometricCore["🧠 Biometric Intelligence Core"]
        ECAPA["ECAPA-TDNN Deep Neural Engine<br>(1D Dilated Conv, SE Attention, ASP)"]
        Baseline["Heuristic Baseline Engine<br>(40 MFCCs + Jitter/Shimmer)"]
        Cancellable["Orthonormal Bio-Hashing<br>(z = P_k * x, P_k^T * P_k = I)"]
        BallTree["1:N BallTree ANN Engine<br>(O(log N) Deduplication Index)"]
    end

    subgraph DataStorage["💾 Cryptographic Storage & Ledger"]
        UserDB[("Voice Profiles DB<br>(AES-128 Encrypted Demographics)")]
        AuditLedger[("Tamper-Evident Audit Ledger<br>(SHA-256 Blockchain Hash Chaining)")]
        MemoryShred["RAM Zeroization<br>(0x00 Buffer Shredding - DPDP Act)"]
    end

    CamMic --> UI
    UI --> EdgeExtract
    UI -->|HTTPS / REST| FastAPI
    EdgeExtract -->|0.75 KB Vector| FastAPI
    FastAPI --> CORS --> VerhoeffCheck
    VerhoeffCheck --> IndianDenoiser --> AudioPreprocessor
    AudioPreprocessor --> LipSync
    AudioPreprocessor --> AASIST --> XAI
    AudioPreprocessor --> ECAPA
    AudioPreprocessor --> Baseline
    ECAPA --> Cancellable
    Cancellable --> BallTree
    Cancellable --> MemoryShred
    Cancellable --> UserDB
    FastAPI --> AuditLedger
```

---

## 2. Use Case Diagram

```mermaid
flowchart LR
    Citizen((Citizen / End User))
    Operator((Kiosk Operator))
    Auditor((Forensic Auditor))
    Admin((System Administrator))

    subgraph AadhaarVoiceSystem["🇮🇳 AadhaarVoice System Boundary"]
        UC1(["UC-01: Enroll Voice Biometric Profile"])
        UC2(["UC-02: Authenticate via Voice & Lip-Sync"])
        UC3(["UC-03: Execute UPI Voice Payment"])
        UC4(["UC-04: Deepfake Forensics & XAI Inspection"])
        UC5(["UC-05: 1:N Fraud Duplicate Search"])
        UC6(["UC-06: Revoke Biometric Salt (DPDP Act)"])
        UC7(["UC-07: Verify Audit Ledger Integrity"])
        UC8(["UC-08: View Academic ROC Curves & EER"])
    end

    Citizen --> UC1
    Citizen --> UC2
    Citizen --> UC3
    Citizen --> UC6

    Operator --> UC1
    Operator --> UC2
    Operator --> UC5

    Auditor --> UC4
    Auditor --> UC7
    Auditor --> UC8

    Admin --> UC5
    Admin --> UC6
    Admin --> UC7
```

---

## 3. Data Flow Diagram (DFD) Level 0 — Context Level

```mermaid
flowchart TD
    Citizen["👤 Citizen / User Device"]
    AadhaarSystem["[0.0] AadhaarVoice Biometric System"]
    AuditorAdmin["👨‍💼 Auditor / Banking Administrator"]

    Citizen -->|12-digit VID, Voice Audio, Webcam Video| AadhaarSystem
    AadhaarSystem -->|Authentication Decision, Matching Score, UPI Token| Citizen

    AuditorAdmin -->|Audit Verification Request, Revocation Signal| AadhaarSystem
    AadhaarSystem -->|Tamper-evident Audit Logs, Deepfake XAI Heatmaps, EER Curves| AuditorAdmin
```

---

## 4. Data Flow Diagram (DFD) Level 1 — Subsystem Decomposition

```mermaid
flowchart TD
    User["Citizen / Client Device"]

    subgraph ProcessFlow["AadhaarVoice Processes"]
        P1["[1.0] Input Validation & Noise Suppression"]
        P2["[2.0] Multi-Modal Lip-Sync & Liveness"]
        P3["[3.0] AASIST Deepfake Forensics"]
        P4["[4.0] ECAPA-TDNN Feature Extraction"]
        P5["[5.0] Orthonormal Cancellable Bio-Hashing"]
        P6["[6.0] 1:1 Cosine Matching & 1:N BallTree Search"]
        P7["[7.0] Cryptographic Audit Ledger Chaining"]
    end

    subgraph DataStores["Persistent Storage"]
        D1[("D1: Voice Profiles Store")]
        D2[("D2: Audit Ledger Blocks")]
    end

    User -->|VID + Audio + Video| P1
    P1 -->|Denoised 16kHz PCM| P2
    P2 -->|Lip Aperture + Audio Envelope| P3
    P3 -->|Clean Speech Signal| P4
    P4 -->|192-dim Raw Vector x| P5
    P5 -->|Encrypted Template z = P_k * x| P6
    D1 <-->|Fetch Enrolled Template| P6
    P6 -->|Verification Result| P7
    P7 -->|Append Hash Chained Record| D2
    P7 -->|Final Verification Response| User
```

---

## 5. Data Flow Diagram (DFD) Level 2 — Detailed Biometric Pipeline

```mermaid
flowchart TD
    subgraph DFD_Level_2["[4.0 - 6.0] Detailed Biometric & Security Pipeline"]
        Sub1["4.1 Temporal Dilated Convolutions"]
        Sub2["4.2 Squeeze-and-Excitation Channel Attention"]
        Sub3["4.3 Attentive Statistical Pooling (ASP)"]
        Sub4["5.1 QR Orthonormalization (P_k^T * P_k = I)"]
        Sub5["5.2 Isometric Vector Projection (z = P_k * x)"]
        Sub6["5.3 Memory Shredding (0x00 RAM Fill)"]
        Sub7["6.1 BallTree Metric Partitioning"]
        Sub8["6.2 Triangle Inequality Pruning (O(log N))"]
    end

    Speech["Speech Samples (16 kHz)"] --> Sub1
    Sub1 --> Sub2 --> Sub3 -->|192-dim Vector x| Sub5
    Salt["Citizen Salt k"] --> Sub4 -->|Orthonormal Matrix P_k| Sub5
    Sub5 -->|Transformed Template z| Sub7
    Sub5 --> Sub6
    Sub7 --> Sub8 --> Result["1:1 Match Score & 1:N Duplicate Verdict"]
```

---

## 6. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    USERS ||--o{ VERIFICATION_LOGS : audits
    VOICE_PROFILES ||--o{ VERIFICATION_LOGS : logs
    VOICE_PROFILES ||--o{ LIVENESS_CHALLENGES : validates

    USERS {
        int id PK
        string username UK
        string hashed_password
        string role
        datetime created_at
    }

    VOICE_PROFILES {
        int id PK
        string demo_vid UK "12-digit Aadhaar VID"
        text full_name_encrypted "AES-128 Encrypted"
        text phone_encrypted "AES-128 Encrypted"
        string gender
        string embedding_hash "HMAC-SHA256"
        text embedding_json "192-dim Vector JSON"
        float pitch_hz
        float sample_duration_seconds
        string enrollment_status "ACTIVE / REVOKED"
        datetime created_at
        datetime updated_at
    }

    VERIFICATION_LOGS {
        int id PK
        int profile_id FK
        string demo_vid
        boolean verified
        float similarity_score
        boolean is_synthetic
        float deepfake_score
        string risk_level "LOW / MEDIUM / HIGH"
        boolean challenge_passed
        string status "AUTHENTICATED / REJECTED / SPOOF"
        string failure_reason
        string ip_address
        string client_user_agent
        string previous_hash "SHA-256 Blockchain Link"
        string current_hash "SHA-256 Current Block"
        datetime timestamp
    }

    LIVENESS_CHALLENGES {
        int id PK
        string challenge_id UK
        string demo_vid
        string challenge_type
        string expected_text
        boolean is_used
        datetime expires_at
        datetime created_at
    }
```

---

## 7. Class Diagram

```mermaid
classDiagram
    class VoiceProfile {
        +int id
        +string demo_vid
        +string full_name_encrypted
        +string embedding_hash
        +string embedding_json
        +string enrollment_status
        +datetime created_at
    }

    class VerificationLog {
        +int id
        +string demo_vid
        +boolean verified
        +float similarity_score
        +boolean is_synthetic
        +string status
        +string previous_hash
        +string current_hash
    }

    class ECAPATDNN {
        +int embedding_dim = 192
        +extract_embedding(signal, sr) dict
        -squeeze_and_excitation(features) ndarray
        -attentive_statistical_pooling(features) ndarray
    }

    class AASISTAntiSpoof {
        +float high_freq_threshold = 6500.0
        +analyze_neural_deepfake(signal, sr) dict
        -compute_phase_discontinuity(signal) float
        -compute_fricative_ratio(signal) float
    }

    class MultiModalLipSyncDetector {
        +float min_correlation = 0.55
        +float max_lag_ms = 120.0
        +analyze_audiovisual_sync(audio, sr, lip_apertures, fps) dict
        -compute_audio_energy_envelope(audio, sr) ndarray
    }

    class CancellableBiometrics {
        +derive_orthonormal_projection(salt, dim) ndarray
        +transform_to_cancellable_embedding(raw_emb, salt) ndarray
        +shred_audio_buffer(audio_array) void
    }

    class BiometricVectorIndex {
        +int embedding_dim = 192
        +BallTree tree
        +search_1_to_n(probe_vector, top_k) dict
        +benchmark_scalability(sizes) list
    }

    VoiceProfile "1" --> "*" VerificationLog : tracks
    ECAPATDNN ..> CancellableBiometrics : feeds
    CancellableBiometrics ..> BiometricVectorIndex : indexes
    AASISTAntiSpoof ..> VerificationLog : validates
    MultiModalLipSyncDetector ..> VerificationLog : validates
```

---

## 8. Sequence Diagram (1:1 Verification Sequence)

```mermaid
sequenceDiagram
    autonumber
    actor Citizen as Citizen / User
    participant WebUI as Web Browser / Kiosk UI
    participant API as FastAPI Gateway
    participant AudioModule as Audio Preprocessor & Denoiser
    participant MultiModal as LipSync Detector
    participant DeepfakeEngine as AASIST Detector
    participant BiometricEngine as ECAPA-TDNN & Bio-Hash
    participant DB as SQLite / Ledger DB

    Citizen->>WebUI: Clicks "Authenticate" & speaks challenge phrase
    WebUI->>API: POST /api/voice/verify (VID, Audio WAV, Video Lip Array)
    API->>API: Validate 12-digit VID via Verhoeff Checksum
    API->>AudioModule: Suppress Indian 50Hz/100Hz fan drone & normalize
    AudioModule-->>API: Clean 16kHz audio array

    par Multi-Modal & Deepfake Verification
        API->>MultiModal: analyze_audiovisual_sync(audio, lip_apertures)
        MultiModal-->>API: r_AV=0.78, lag=15ms (LIVENESS_VERIFIED)
    and
        API->>DeepfakeEngine: analyze_neural_deepfake(audio)
        DeepfakeEngine-->>API: deepfake_score=0.02 (CLEAN_HUMAN)
    end

    API->>BiometricEngine: Extract 192-dim ECAPA embedding & project (z = P_k * x)
    BiometricEngine-->>API: Candidate Cancellable Vector
    API->>DB: Fetch enrolled template for VID
    DB-->>API: Enrolled Vector

    API->>API: Compute Cosine Similarity (Cosine = 0.94 >= 0.75)
    API->>DB: Append SHA-256 Hash Chained Audit Log Block
    DB-->>API: Audit Record Confirmed
    API->>BiometricEngine: shred_audio_buffer(signal) -> 0x00 RAM Fill
    API-->>WebUI: 200 OK: {"verified": true, "status": "AUTHENTICATED", "similarity": 94.2%}
    WebUI-->>Citizen: Green Banner: "Identity Verified via Voice"
```

---

## 9. Activity Diagram (Decision Flowchart)

```mermaid
flowchart TD
    Start([User Initiates Authentication]) --> InputVID[Enter 12-Digit Demo Aadhaar VID]
    InputVID --> CheckVerhoeff{Passes Verhoeff<br>Dihedral Checksum?}

    CheckVerhoeff -- No --> ErrVID[Return Error 400: Invalid Aadhaar Checksum] --> End([Process Terminated])
    CheckVerhoeff -- Yes --> RecAudio[Capture 3s Audio Speech + Camera Lip Frames]

    RecAudio --> Denoise[Apply 50Hz/100Hz Notch + Wiener Denoising]
    Denoise --> CheckLipSync{Lip-Sync Cross-Corr<br>r >= 0.55 & Lag <= 120ms?}

    CheckLipSync -- No (Frozen Lips) --> ReplaySpoof[Flag SPOOF_REPLAY_ATTACK: Loudspeaker Detected] --> LogAudit
    CheckLipSync -- Yes --> CheckDeepfake{AASIST Score <= 0.65<br>& High-Band Energy OK?}

    CheckDeepfake -- No (Vocoder Cutoff) --> FakeSpoof[Flag SPOOF_DETECTED: Synthetic AI Clone Detected] --> LogAudit
    CheckDeepfake -- Yes --> ExtractECAPA[Extract 192-dim ECAPA-TDNN Embedding]

    ExtractECAPA --> ProjectBioHash[Transform Vector: z = P_k * x]
    ProjectBioHash --> ShredRAM[RAM Buffer Zeroization: 0x00 Shred]
    ShredRAM --> MatchCosine{Cosine Similarity >= 0.75?}

    MatchCosine -- No --> RejectMatch[Status: REJECTED: Voice Mismatch] --> LogAudit
    MatchCosine -- Yes --> AuthMatch[Status: AUTHENTICATED: Identity Confirmed] --> LogAudit

    LogAudit[Append SHA-256 Chained Record to Audit Ledger] --> RetResult[Return JSON Outcome to Client] --> End
```

---

## 10. Physical Database Schema

### Table 1: `users`
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Internal user ID |
| `username` | `VARCHAR(64)` | `UNIQUE, NOT NULL` | Operator / Auditor login username |
| `hashed_password` | `VARCHAR(255)` | `NOT NULL` | PBKDF2-HMAC-SHA256 salted password |
| `role` | `VARCHAR(32)` | `DEFAULT 'operator'` | RBAC role (`admin`, `operator`, `auditor`) |
| `created_at` | `DATETIME` | `DEFAULT UTC NOW` | Record creation timestamp |

### Table 2: `voice_profiles`
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Internal profile identifier |
| `demo_vid` | `VARCHAR(12)` | `UNIQUE, NOT NULL, INDEX` | 12-digit demo Aadhaar number passing Verhoeff |
| `full_name_encrypted` | `TEXT` | `NOT NULL` | AES-128 (Fernet) encrypted citizen legal name |
| `phone_encrypted` | `TEXT` | `NULLABLE` | AES-128 (Fernet) encrypted mobile number |
| `gender` | `VARCHAR(16)` | `DEFAULT 'unspecified'` | Demographic gender flag |
| `embedding_hash` | `VARCHAR(64)` | `NOT NULL` | HMAC-SHA256 cryptographic template digest |
| `embedding_json` | `TEXT` | `NOT NULL` | Serialized 192-float JSON vector |
| `pitch_hz` | `FLOAT` | `DEFAULT 150.0` | Fundamental frequency estimate ($F_0$) |
| `sample_duration_seconds` | `FLOAT` | `DEFAULT 0.0` | Duration of enrolled vocal sample |
| `enrollment_status` | `VARCHAR(32)` | `DEFAULT 'ACTIVE'` | Status (`ACTIVE`, `REVOKED`, `SUSPENDED`) |
| `created_at` | `DATETIME` | `DEFAULT UTC NOW` | Enrollment timestamp |
| `updated_at` | `DATETIME` | `DEFAULT UTC NOW` | Last update / salt reissuance timestamp |

### Table 3: `verification_logs`
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Internal log ID |
| `profile_id` | `INTEGER` | `FOREIGN KEY (voice_profiles.id)` | Enrolled profile reference |
| `demo_vid` | `VARCHAR(12)` | `INDEX, NOT NULL` | Aadhaar VID attempted |
| `verified` | `BOOLEAN` | `NOT NULL, DEFAULT FALSE` | Final authentication decision boolean |
| `similarity_score` | `FLOAT` | `NOT NULL` | Cosine similarity value $[-1.0, 1.0]$ |
| `is_synthetic` | `BOOLEAN` | `DEFAULT FALSE` | True if AASIST detected deepfake |
| `deepfake_score` | `FLOAT` | `NOT NULL` | Synthetic spoof probability $[0.0, 1.0]$ |
| `risk_level` | `VARCHAR(16)` | `DEFAULT 'LOW'` | Spoof risk classification (`LOW`, `HIGH`, `CRITICAL`) |
| `challenge_passed`| `BOOLEAN` | `DEFAULT TRUE` | Challenge-response verification boolean |
| `status` | `VARCHAR(32)` | `NOT NULL` | Verdict (`AUTHENTICATED`, `REJECTED`, `SPOOF_DETECTED`) |
| `failure_reason` | `VARCHAR(255)`| `NULLABLE` | Human-readable explanation of failure |
| `ip_address` | `VARCHAR(64)` | `DEFAULT '127.0.0.1'` | Client endpoint IP address |
| `client_user_agent`| `VARCHAR(255)`| `DEFAULT 'unknown'` | Client device / browser fingerprint |
| `previous_hash` | `VARCHAR(64)` | `NOT NULL` | SHA-256 hash of previous log block |
| `current_hash` | `VARCHAR(64)` | `NOT NULL` | SHA-256 hash of current log block |
| `timestamp` | `DATETIME` | `DEFAULT UTC NOW` | Exact UTC execution timestamp |

### Table 4: `liveness_challenges`
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Internal challenge ID |
| `challenge_id` | `VARCHAR(64)` | `UNIQUE, NOT NULL, INDEX` | Cryptographically generated UUID token |
| `demo_vid` | `VARCHAR(12)` | `NOT NULL` | Targeted citizen VID |
| `challenge_type` | `VARCHAR(32)` | `DEFAULT 'DIGIT_SEQUENCE'` | Dynamic challenge type (`DIGIT_SEQUENCE`, `PHRASE`) |
| `expected_text` | `VARCHAR(64)` | `NOT NULL` | Random digits/words to articulate |
| `is_used` | `BOOLEAN` | `DEFAULT FALSE` | Replay protection flag (one-time use) |
| `expires_at` | `DATETIME` | `NOT NULL` | Challenge expiration timestamp (TTL = 120s) |
| `created_at` | `DATETIME` | `DEFAULT UTC NOW` | Generation timestamp |
