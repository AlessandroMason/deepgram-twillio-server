# ⚡ Quick Start Guide

## Your Current Situation

You have:
- ✅ Existing Render deployment running `python server.py`
- ✅ New `realtime_predictions/` folder added
- ✅ Both in the same git repository

## 🎯 What Do You Want?

### Option A: Keep It Simple (Recommended)
**Deploy prediction API as a separate Render service**

This is the cleanest approach for Render:

1. **Your main service stays the same:**
   - Keep using `python server.py`
   - No changes needed!

2. **Create a new Render web service:**
   - Dashboard → "New +" → "Web Service"
   - Connect same GitHub repo
   - **Root Directory**: `realtime_predictions`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python start_server.py --skip-checks`
   - **Health Check Path**: `/health`

3. **Done!** You now have two services:
   - `https://your-app.onrender.com` - WebSocket server
   - `https://your-app-api.onrender.com` - Prediction API

**Pros:**
- ✅ Independently scalable
- ✅ Separate URLs for each service
- ✅ Easy to monitor
- ✅ No code changes needed

---

### Option B: Run Both Together
**Run both services from one Render deployment**

1. **Update Render start command:**
   ```
   python start_all_services.py
   ```

2. **That's it!**

**Pros:**
- ✅ Single deployment
- ✅ Both services running

**Cons:**
- ⚠️  Prediction API only accessible internally (same port limitation)
- ⚠️  Harder to scale independently

---

### Option C: Just WebSocket (Current)
**Don't use prediction API yet**

Keep everything as-is:
```bash
python server.py
```

The prediction API code is there when you need it later.

---

## 🚀 Deployment Steps (Option A - Recommended)

### Step 1: Commit & Push

```bash
cd /Users/alessandromason/Documents/GitHub/340\ ML/deepgram-twillio-server

# Test locally (optional)
./test_integrated_setup.sh

# Commit everything
git add .
git commit -m "Add realtime predictions API"
git push
```

### Step 2: Keep Main Service As-Is

Your existing Render service continues to work:
- **Start Command**: `python server.py`
- No changes needed!

### Step 3: Create New Service for Prediction API

**In Render Dashboard:**

1. Click **"New +"** → **"Web Service"**

2. **Connect Repository:**
   - Select your GitHub repo
   - Branch: `main`

3. **Configure Service:**
   ```
   Name: behavior-prediction-api
   Region: Oregon (or same as main service)
   Branch: main
   Root Directory: realtime_predictions
   
   Build Command: pip install -r requirements.txt
   Start Command: python start_server.py --skip-checks
   
   Plan: Free (or Starter)
   ```

4. **Advanced Settings:**
   ```
   Health Check Path: /health
   Auto-Deploy: Yes
   ```

5. **Click "Create Web Service"**

6. **Wait for deployment** (2-3 minutes)

7. **Test it:**
   ```bash
   curl https://your-service.onrender.com/health
   curl https://your-service.onrender.com/docs
   ```

### Done! 🎉

You now have:
- Main service: WebSocket server (unchanged)
- New service: Prediction API (separate URL)

---

## 🧪 Local Testing

### Test Everything First

```bash
# Quick validation
./test_integrated_setup.sh

# Install dependencies
pip install -r requirements.txt

# Test WebSocket server only
python server.py

# OR test both services together
python start_all_services.py

# OR test prediction API only
cd realtime_predictions
python start_server.py
```

---

## 📊 What's Different Now?

### Before
```
requirements.txt           (WebSocket dependencies only)
server.py                  (Your WebSocket server)
```

### After
```
requirements.txt           (All dependencies - WebSocket + Prediction API)
server.py                  (Unchanged - WebSocket server)
start_all_services.py      (NEW - runs both services)
realtime_predictions/      (NEW - Prediction API)
  ├── api_server.py
  ├── start_server.py
  ├── requirements.txt
  └── ...
```

---

## 🐛 Common Issues

### "Module not found: pandas/sklearn/fastapi"

**Solution:**
```bash
pip install -r requirements.txt
```

### "Port already in use"

**Solution:** Kill existing processes:
```bash
# Find process
lsof -ti:5000 | xargs kill -9
lsof -ti:5001 | xargs kill -9
```

### "Model file not found"

**This is OK!** The API starts anyway. To train the model:
```bash
cd realtime_predictions
python train_model.py
```

### Still using old requirements.txt on Render

**Solution:** Trigger a new deploy:
- Render Dashboard → Your service → "Manual Deploy"
- Or push a new commit

---

## 📖 Full Documentation

- **INTEGRATED_DEPLOYMENT.md** - Complete deployment guide
- **realtime_predictions/RENDER_DEPLOYMENT.md** - Prediction API details
- **realtime_predictions/README.md** - API usage

---

## 💡 My Recommendation

**Use Option A (Separate Services):**

1. Keep your main deployment unchanged
2. Create a new Render service for the prediction API
3. Each service has its own URL and can scale independently

**Why?**
- ✅ Simpler architecture
- ✅ Better for production
- ✅ Easier to debug
- ✅ Render's recommended approach for multi-service apps

---

## 🎯 Ready?

1. ✅ Run: `./test_integrated_setup.sh`
2. ✅ Commit and push your changes
3. ✅ Create new Render service (Option A) or update start command (Option B)
4. ✅ Test your deployment

That's it! 🚀

---

## ❓ Questions?

**Q: Do I need to change my existing deployment?**
A: No! Keep using `python server.py` and create a separate service for the API.

**Q: Will this break my current setup?**
A: No! Your existing server.py works exactly as before.

**Q: Can I test locally first?**
A: Yes! Run `./test_integrated_setup.sh` then `python start_all_services.py`

**Q: What if I only want the WebSocket server?**
A: Just keep using `python server.py` - nothing changes!

**Q: Do I need the model file committed?**
A: No, the API starts without it. Train later if needed.

