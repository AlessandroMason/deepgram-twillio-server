# 🚀 Integrated Deployment Guide

## Overview

Your Render deployment now includes **TWO services**:
1. **WebSocket Server** (`server.py`) - Twilio/Deepgram voice agent on port `PORT`
2. **Behavior Prediction API** (`realtime_predictions/`) - REST API on port `PORT+1`

Both services run from a single Render web service deployment.

---

## 🎯 Deployment Options

### Option 1: Run Both Services Together (Recommended for Production)

Use the integrated startup script that runs both services:

**On Render:**
1. Set **Start Command** to:
   ```bash
   python start_all_services.py
   ```

2. **Environment Variables:**
   ```
   PORT=5000                      # Render sets this automatically
   PREDICTION_API_PORT=8001       # Optional: Override prediction API port
   DEEPGRAM_API_KEY=your_key
   GMAIL_PASSWORD=your_password
   # ... other existing env vars
   ```

3. **How it works:**
   - Main WebSocket server runs on port `$PORT` (e.g., 5000)
   - Prediction API runs on port `$PORT + 1` (e.g., 5001) or `$PREDICTION_API_PORT`

### Option 2: Run Only WebSocket Server (Current Setup)

Keep your existing deployment as-is:

**Start Command:**
```bash
python server.py
```

The WebSocket server continues to work normally.

### Option 3: Run Only Prediction API

If you want just the prediction service:

**Start Command:**
```bash
cd realtime_predictions && python start_server.py --skip-checks
```

Or:
```bash
python -m uvicorn realtime_predictions.api_server:app --host 0.0.0.0 --port $PORT
```

---

## 📋 Setup Instructions

### 1. Update Dependencies

Already done! Your `requirements.txt` now includes:
- All existing dependencies (WebSocket, Firebase, etc.)
- New: pandas, numpy, scikit-learn, fastapi, uvicorn

### 2. Configure Render

**Go to your Render Dashboard:**

1. Select your web service
2. Go to **Settings**
3. Update **Start Command**:
   ```
   python start_all_services.py
   ```
4. **Save Changes**

### 3. Deploy

```bash
# Commit changes
git add .
git commit -m "Add realtime predictions API to deployment"
git push

# Render will automatically redeploy
```

---

## 🔍 Testing Locally

### Test Both Services Together

```bash
# Install dependencies
pip install -r requirements.txt

# Run both services
python start_all_services.py
```

**In another terminal:**
```bash
# Test WebSocket server
# (Use your existing Twilio test)

# Test Prediction API
curl http://localhost:5001/health
curl http://localhost:5001/status
curl http://localhost:5001/docs  # Open in browser
```

### Test Individual Services

**WebSocket Server Only:**
```bash
python server.py
```

**Prediction API Only:**
```bash
cd realtime_predictions
python start_server.py
```

---

## 🌐 Accessing Your APIs After Deployment

Once deployed on Render (e.g., `https://your-app.onrender.com`):

### WebSocket Server (Existing)
- **Personal Endpoint**: `wss://your-app.onrender.com/twilio`
- **Generic Endpoint**: `wss://your-app.onrender.com/generic`

### Prediction API (New)
Render exposes only the main PORT, so you have two options:

**Option A: Use Render's Internal Port**
The prediction API runs on `PORT+1` but is only accessible internally between services.

**Option B: Create Separate Web Service**
For external access to the Prediction API:
1. Create a new Render Web Service
2. Point to `realtime_predictions/` directory
3. Use start command: `python start_server.py --skip-checks`

**Option C: Add HTTP Router to server.py**
Modify `server.py` to handle both WebSocket and HTTP on the same port (more complex).

---

## 💡 Recommendations

### For Your Use Case:

Since you're on Render, I recommend **Option B** - create a separate web service for the prediction API:

1. **Main Service** (existing):
   - Name: `deepgram-twilio-server`
   - Start Command: `python server.py`
   - Handles: WebSocket connections for Twilio

2. **New Service** (prediction API):
   - Name: `behavior-prediction-api`
   - Root Directory: `realtime_predictions`
   - Start Command: `python start_server.py --skip-checks`
   - Handles: REST API for predictions

This way:
- ✅ Each service is independently scalable
- ✅ Each service has its own public URL
- ✅ Easier to monitor and debug
- ✅ Better separation of concerns

### To Create Second Service on Render:

1. Go to Render Dashboard
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. Configure:
   ```
   Name: behavior-prediction-api
   Root Directory: realtime_predictions
   Build Command: pip install -r requirements.txt
   Start Command: python start_server.py --skip-checks
   ```
5. Deploy!

---

## 🐛 Troubleshooting

### Issue: "Port already in use"

**Solution:** The prediction API tries to use PORT+1. If that's taken:
```bash
export PREDICTION_API_PORT=8001
python start_all_services.py
```

### Issue: "Module not found: realtime_predictions"

**Solution:** Run from the project root:
```bash
cd /Users/alessandromason/Documents/GitHub/340\ ML/deepgram-twillio-server
python start_all_services.py
```

### Issue: "Model file not found"

**Solution:** This is expected and OK! The API will start in degraded mode. To fix:
```bash
cd realtime_predictions
python train_model.py
git add models/realtime_behavior_model.pkl
git commit -m "Add trained model"
git push
```

### Issue: Only want WebSocket server

**Solution:** Just keep using:
```bash
python server.py
```

Nothing breaks if you don't use the prediction API.

---

## 📊 Service Architecture

```
┌─────────────────────────────────────────────┐
│     Render Web Service (Single Deploy)      │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────┐  ┌─────────────────┐ │
│  │  WebSocket       │  │  Prediction     │ │
│  │  Server          │  │  API            │ │
│  │  (server.py)     │  │  (FastAPI)      │ │
│  │                  │  │                 │ │
│  │  Port: $PORT     │  │  Port: $PORT+1  │ │
│  │  (5000)          │  │  (5001)         │ │
│  └──────────────────┘  └─────────────────┘ │
│                                             │
│  Started by: start_all_services.py          │
└─────────────────────────────────────────────┘
```

**OR** (Recommended):

```
┌────────────────────┐    ┌────────────────────┐
│  Service 1:        │    │  Service 2:        │
│  WebSocket Server  │    │  Prediction API    │
│                    │    │                    │
│  python server.py  │    │  start_server.py   │
│  Port: 5000        │    │  Port: 8000        │
│                    │    │                    │
│  Public URL:       │    │  Public URL:       │
│  your-app.         │    │  your-app-api.     │
│  onrender.com      │    │  onrender.com      │
└────────────────────┘    └────────────────────┘
```

---

## ✅ Quick Checklist

### Current Deployment (WebSocket Only)
- [x] requirements.txt updated
- [x] server.py works as before
- [x] No changes needed!

### Add Prediction API (Same Service)
- [ ] Use `python start_all_services.py`
- [ ] Set PREDICTION_API_PORT if needed
- [ ] Note: API only accessible internally

### Separate Prediction API (New Service)
- [ ] Create new Render web service
- [ ] Point to `realtime_predictions/`
- [ ] Set start command: `python start_server.py --skip-checks`
- [ ] Get separate public URL

---

## 🎯 Next Steps

**Choose your path:**

**Path A - Keep Simple (No Changes)**
- Continue using `python server.py`
- Prediction API available for future use

**Path B - Run Both (Same Service)**
- Change start command to `python start_all_services.py`
- Both services run together
- API accessible internally

**Path C - Separate Services (Recommended)**
- Keep main service as-is
- Create new service for prediction API
- Each service independently accessible

---

Need help deciding? I recommend **Path C** for production use!

