# 🚀 AadhaarVoice: Production & Cloud Deployment Guide

A step-by-step deployment guide for deploying **AadhaarVoice** to **Hugging Face Spaces (Free Cloud with HTTPS)**, **Render.com**, and **Local Offline Environments**.

> 💡 **Why HTTPS (SSL) is Mandatory for Voice AI:** Web browsers (Chrome, Edge, Safari) strictly block microphone access (`navigator.mediaDevices.getUserMedia`) on non-localhost HTTP connections. To test live microphone input on mobile phones or external laptops, you must deploy on an HTTPS host (like Hugging Face Spaces or Render).

---

## 🥇 Option 1: Hugging Face Spaces (⭐ Recommended & Free for AI)

Hugging Face Spaces provides **free 2 vCPU + 16GB RAM** with automatic SSL/HTTPS. It is the premier platform to showcase AI projects to professors, examiners, and hackathon judges.

### Step-by-Step Setup:

1. **Create an Account / Log In:**
   - Go to [huggingface.co](https://huggingface.co) and log in.

2. **Create a New Space:**
   - Navigate to [huggingface.co/new-space](https://huggingface.co/new-space).
   - **Space Name:** `AadhaarVoice`
   - **License:** `MIT`
   - **Space SDK:** Select **Docker** (Blank).
   - **Space Hardware:** Select **Free 2 vCPU · 16 GB RAM**.
   - **Visibility:** Public.

3. **Link Your GitHub Repository or Push to Hugging Face:**
   In your terminal inside `AadhaarVoice`:
   ```bash
   # Add Hugging Face git remote (replace <YOUR_HF_USERNAME> with your HF username)
   git remote add hf https://huggingface.co/spaces/<YOUR_HF_USERNAME>/AadhaarVoice

   # Push code to Hugging Face Space
   git push hf main
   ```

4. **Live Verification:**
   - In 2–3 minutes, the Docker container will build automatically.
   - Access your live portal at: `https://huggingface.co/spaces/<YOUR_HF_USERNAME>/AadhaarVoice`
   - Open this link on your smartphone, allow microphone permissions, and test live voice authentication!

---

## 🥈 Option 2: Render.com (Web Service)

1. Sign up at [render.com](https://render.com) using your GitHub account.
2. Click **New +** -> **Web Service**.
3. Select your repository: `VimalN2005/AadhaarVoice`.
4. Choose **Environment: Docker**.
5. Set Health Check Path: `/api/health`.
6. Click **Deploy Web Service**.
7. Render will provide a free HTTPS URL (e.g. `https://aadhaarvoice.onrender.com`).

---

## 💻 Option 3: Local Offline Setup (Mandatory for College Viva / Presentation Day)

> ⚠️ **Viva Pro Tip:** Never rely on campus Wi-Fi or mobile hotspots during an in-person defense. Keep the project running locally on your laptop beforehand.

### 1. Docker Compose (1-Command Startup)
```bash
# Build and run containers in background
docker compose up --build -d

# Check running status
docker compose ps
```

### 2. Direct Python Startup
```bash
# Activate virtual environment and install dependencies
pip install -r requirements.txt

# Start FastAPI Uvicorn server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Dashboard:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **API Specs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- *Note:* Chrome allows microphone access on `http://127.0.0.1` and `http://localhost` without SSL.
