# 🚀 Quick Deployment Guide

## Changes Made for Render.com Deployment

### ✅ Fixed Issues:

1. **Dockerfile**
   - ✅ Added `curl` for health checks
   - ✅ Added support for `PORT` environment variable
   - ✅ Changed CMD to use `--skip-checks` flag for production
   - ✅ Extended health check start period to 40s

2. **start_server.py**
   - ✅ Added support for `PORT` environment variable
   - ✅ Falls back to PORT env var if --port not specified
   - ✅ Allows graceful startup without strict pre-flight checks

3. **api_server.py**
   - ✅ Improved startup messages
   - ✅ Graceful degradation if model not found
   - ✅ Better error handling

4. **New Files**
   - ✅ `.dockerignore` - Excludes unnecessary files from Docker build
   - ✅ `render.yaml` - Render.com blueprint configuration
   - ✅ `RENDER_DEPLOYMENT.md` - Detailed deployment guide

5. **requirements.txt**
   - ✅ Added `uvicorn[standard]` for better production support
   - ✅ Added `python-multipart` for form handling

## 🎯 What You Need to Do

### Option A: Deploy with Pre-trained Model (Recommended for Production)

1. **Ensure model files are in git:**
   ```bash
   cd /Users/alessandromason/Documents/GitHub/340\ ML/deepgram-twillio-server
   git add realtime_predictions/
   git commit -m "Add realtime predictions service for deployment"
   git push
   ```

2. **Deploy to Render:**
   - Go to https://dashboard.render.com
   - New + → Blueprint
   - Connect your repository
   - Point to `realtime_predictions/render.yaml`
   - Click "Apply"

3. **Monitor deployment:**
   - Watch logs in Render dashboard
   - Wait for "Live" status
   - Visit: `https://your-service.onrender.com/health`

### Option B: Use Online Learning Server (No Pre-trained Model Required)

If you want to use the online learning version that doesn't require a pre-trained model:

1. **Modify Dockerfile CMD:**
   Change line 32 to:
   ```dockerfile
   CMD python -m uvicorn online_api_server:app --host 0.0.0.0 --port ${PORT:-8000}
   ```

2. **Deploy as above**

3. **Initialize with data:**
   ```bash
   curl -X POST https://your-service.onrender.com/learn/bulk \
     -H "Content-Type: application/json" \
     -d @historical_data.json
   ```

## 📋 Pre-Deployment Checklist

- [ ] All files in `realtime_predictions/` are committed to git
- [ ] Model file exists: `realtime_predictions/models/realtime_behavior_model.pkl`
- [ ] Data file exists: `realtime_predictions/data/firestore_data.csv`
- [ ] `Dockerfile` has correct CMD line
- [ ] `render.yaml` region is set to your preference
- [ ] Requirements.txt is updated
- [ ] `.dockerignore` is present

## 🔍 Testing Locally Before Deploy

```bash
cd realtime_predictions

# Build Docker image
docker build -t behavior-api .

# Run container
docker run -p 8000:8000 -e PORT=8000 behavior-api

# Test in another terminal
curl http://localhost:8000/health
curl http://localhost:8000/status
curl http://localhost:8000/docs  # Open in browser
```

## 🐛 Common Issues

### Issue: "Model not found" error
**Solution**: 
- Either commit the model file, or
- Use `online_api_server.py` instead, or
- Train after deployment via `/retrain` endpoint

### Issue: Health check failing
**Solution**: Check that curl is installed in Dockerfile (✅ already fixed)

### Issue: Port binding error
**Solution**: Ensure using PORT env variable (✅ already fixed)

### Issue: Service spinning down
**Solution**: 
- Free tier spins down after 15 min inactivity
- Upgrade to Starter plan ($7/mo) for always-on
- Or ping every 10 min with cron job

## 🎬 Next Steps After Deployment

1. **Test the API:**
   ```bash
   export API_URL="https://your-service.onrender.com"
   
   # Health check
   curl $API_URL/health
   
   # Get status
   curl $API_URL/status
   
   # View docs
   open $API_URL/docs
   ```

2. **Monitor logs:**
   - Check Render dashboard for real-time logs
   - Look for any startup errors

3. **Set up alerts:**
   - Configure Render notifications
   - Set up uptime monitoring (e.g., UptimeRobot)

4. **Secure the API:**
   - Update CORS in `api_server.py`
   - Add API key authentication
   - Use HTTPS only

## 📝 Files Modified Summary

```
realtime_predictions/
├── Dockerfile                    (MODIFIED - added curl, PORT support)
├── .dockerignore                 (NEW - exclude dev files)
├── requirements.txt              (MODIFIED - added uvicorn[standard])
├── render.yaml                   (NEW - Render config)
├── start_server.py              (MODIFIED - PORT env var support)
├── api_server.py                (MODIFIED - better error handling)
├── RENDER_DEPLOYMENT.md         (NEW - detailed guide)
└── README_DEPLOYMENT.md         (NEW - this file)
```

## 💡 Tips

- **Free Tier**: Good for testing, spins down after inactivity
- **Starter Tier**: $7/mo, always on, recommended for production
- **Logs**: Always check Render logs if something goes wrong
- **Health Checks**: Render uses `/health` to know if service is up
- **Auto-deploy**: Push to git and Render auto-deploys (if enabled)

---

**Ready to deploy!** Follow Option A or B above to get started. 🚀

