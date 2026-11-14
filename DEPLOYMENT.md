# AirInsight Production Deployment Guide

AirInsight is container-ready and pre-configured for free cloud hosting (Render, Railway, Fly.io, Heroku, Docker).

---

## 🌐 Option 1: Free 1-Click Cloud Deployment on Render.com (Recommended)

Render provides free hosting for Python FastAPI web services.

### Steps:
1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "AirInsight production release"
   git branch -M main
   git remote add origin https://github.com/<your-username>/airinsight.git
   git push -u origin main
   ```

2. **Deploy on Render:**
   * Go to [https://dashboard.render.com](https://dashboard.render.com) and log in.
   * Click **New +** $\rightarrow$ **Web Service**.
   * Connect your GitHub repository (`airinsight`).
   * Configure the settings:
     * **Name:** `airinsight`
     * **Runtime:** `Python 3`
     * **Build Command:** `pip install -r requirements.txt`
     * **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
     * **Instance Type:** `Free`
   * Click **Deploy Web Service**!
   * Within 2 minutes, your website is live with a free HTTPS URL (e.g. `https://airinsight.onrender.com`).

---

## 🚂 Option 2: Deploy on Railway.app

1. Go to [https://railway.app](https://railway.app).
2. Click **New Project** $\rightarrow$ **Deploy from GitHub repo**.
3. Select your `airinsight` repository.
4. Railway automatically reads the bundled `Procfile` and deploys your FastAPI server and frontend web client.
5. In Settings $\rightarrow$ Domains, click **Generate Domain** to get your public live URL.

---

## 🐳 Option 3: Deploy with Docker

AirInsight includes a multi-stage production `Dockerfile` and `docker-compose.yml`.

### Build & Run locally or on any VPS (AWS / DigitalOcean / Linode / GCP):

```bash
docker compose up --build -d
```
Access the application at `http://localhost:8000`.

### To stop:
```bash
docker compose down
```

---

## 💻 Option 4: Local Production Server

To run the application continuously on your machine:

```powershell
python server.py
```
* **Web Dashboard:** [http://localhost:8000](http://localhost:8000)
* **REST API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
