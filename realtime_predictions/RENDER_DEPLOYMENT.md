# 🚀 Render.com Deployment Guide

This guide will help you deploy the Real-time Behavior Prediction API to Render.com.

## 📋 Prerequisites

1. **Render.com account** - Sign up at https://render.com
2. **GitHub repository** - Your code should be in a Git repository
3. **Model and data files** - Ensure these are committed:
   - `models/realtime_behavior_model.pkl`
   - `data/firestore_data.csv`

## 🎯 Quick Deploy (Recommended)

### Option 1: Using render.yaml (Blueprint)

1. **Commit your changes**:
   ```bash
   cd realtime_predictions
   git add .
   git commit -m "Add Render deployment configuration"
   git push
   ```

2. **Create New Blueprint on Render**:
   - Go to https://dashboard.render.com
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will auto-detect the `render.yaml` file
   - Click "Apply" to deploy

3. **Monitor deployment**:
   - Watch the build logs in the Render dashboard
   - Wait for the service to become "Live"
   - Your API will be available at: `https://your-service-name.onrender.com`

### Option 2: Manual Web Service Creation

1. **Create New Web Service**:
   - Go to Render Dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository

2. **Configure the service**:
   ```
   Name: behavior-prediction-api
   Region: Oregon (or your preferred region)
   Branch: main
   Root Directory: realtime_predictions
   Environment: Docker
   Plan: Free (or Starter)
   ```

3. **Advanced Settings**:
   - Health Check Path: `/health`
   - Auto-Deploy: Yes (recommended)

4. **Environment Variables** (Optional):
   ```
   PORT=8000
   MODEL_PATH=models/realtime_behavior_model.pkl
   DATA_PATH=data/firestore_data.csv
   ```

5. **Click "Create Web Service"**

## 🔧 Configuration Details

### Dockerfile Features

The Dockerfile is optimized for Render.com with:
- ✅ Curl installed for health checks
- ✅ Dynamic PORT environment variable support
- ✅ Production-ready with `--skip-checks` flag
- ✅ Proper health check configuration
- ✅ Graceful startup without strict model requirements

### Health Checks

Render will automatically check `/health` endpoint:
- **Interval**: Every 30 seconds
- **Timeout**: 30 seconds
- **Start Period**: 40 seconds (allows model loading)
- **Retries**: 3 attempts before marking unhealthy

## 📊 Post-Deployment

### 1. Verify Deployment

```bash
# Check health
curl https://your-service.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

### 2. View API Documentation

Visit these URLs:
- Interactive API Docs: `https://your-service.onrender.com/docs`
- Alternative Docs: `https://your-service.onrender.com/redoc`

### 3. Test the API

```bash
# Get status
curl https://your-service.onrender.com/status

# Get example prediction
curl https://your-service.onrender.com/example/prediction
```

## 🔐 Production Checklist

Before going to production, consider:

- [ ] **Upgrade to Paid Plan** - Free tier spins down after inactivity
- [ ] **Add Authentication** - Protect your API endpoints
- [ ] **Update CORS Settings** - Restrict to your domain in `api_server.py`:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://yourdomain.com"],  # Change from "*"
      allow_credentials=True,
      allow_methods=["POST", "GET"],
      allow_headers=["*"],
  )
  ```
- [ ] **Set up Monitoring** - Use Render's metrics or external monitoring
- [ ] **Configure Secrets** - Use Render's environment variables for sensitive data
- [ ] **Enable Auto-Deploy** - Automatic deployments from GitHub
- [ ] **Set up Alerts** - Get notified of deployment failures

## 📁 Required Files Checklist

Ensure these files are in your repository:

```
realtime_predictions/
├── Dockerfile              ✅ Optimized for Render
├── .dockerignore          ✅ Excludes unnecessary files
├── requirements.txt       ✅ Python dependencies
├── render.yaml           ✅ Render configuration
├── start_server.py       ✅ Entry point with PORT support
├── api_server.py         ✅ FastAPI application
├── services/
│   └── predictor.py      ✅ Prediction service
├── models/
│   └── realtime_behavior_model.pkl  ⚠️ Include if trained
└── data/
    └── firestore_data.csv  ⚠️ Include if needed
```

## 🐛 Troubleshooting

### Issue: Service won't start

**Solution**: Check the logs in Render dashboard
```bash
# Common issues:
# 1. Missing dependencies - check requirements.txt
# 2. Port binding - ensure using PORT env variable
# 3. Model file missing - app should start anyway with warning
```

### Issue: Health check failing

**Solution**: Ensure health endpoint is accessible
```bash
# Test locally first:
docker build -t test-api .
docker run -p 8000:8000 test-api

# Then check:
curl http://localhost:8000/health
```

### Issue: Model not found on startup

**Solution**: This is expected if model file isn't committed
```bash
# Either:
# 1. Train model locally and commit the .pkl file
# 2. Use the API's /retrain endpoint after deployment
# 3. Use online_api_server.py which doesn't require pre-trained model
```

### Issue: Build takes too long

**Solution**: Optimize Docker layers
```bash
# The Dockerfile is already optimized with:
# - requirements.txt copied first for caching
# - Minimal system dependencies
# - Cleaned apt cache
```

### Issue: Service spinning down (Free tier)

**Solution**: 
- Free tier spins down after 15 minutes of inactivity
- Upgrade to Starter plan ($7/month) for always-on service
- Or use a cron job to ping the service every 10 minutes

## 🔄 Updates and Redeployment

### Automatic Deployment (Recommended)

If auto-deploy is enabled:
```bash
git add .
git commit -m "Update API"
git push
# Render will automatically rebuild and redeploy
```

### Manual Deployment

From Render Dashboard:
1. Go to your service
2. Click "Manual Deploy" → "Deploy latest commit"

### Rollback

If something goes wrong:
1. Go to "Events" tab in Render
2. Find the last successful deployment
3. Click "Rollback to this version"

## 💰 Pricing

### Free Tier
- ✅ 750 hours/month (enough for 1 service)
- ✅ Spins down after 15 min inactivity
- ✅ 512 MB RAM
- ⚠️ Slower cold starts

### Starter Tier ($7/month)
- ✅ Always on (no spin down)
- ✅ 512 MB RAM
- ✅ Faster response times
- ✅ Better for production

## 📞 Support & Resources

- **Render Documentation**: https://render.com/docs
- **Render Status**: https://status.render.com
- **API Documentation**: Your deployment URL + `/docs`
- **Health Endpoint**: Your deployment URL + `/health`

## 🎯 Next Steps

1. **Set up CI/CD**: Configure GitHub Actions for automated testing before deployment
2. **Add monitoring**: Integrate with services like Sentry or LogRocket
3. **Scale up**: Use Render's autoscaling when traffic increases
4. **Add database**: Connect to PostgreSQL or MongoDB for persistence
5. **Custom domain**: Add your own domain name in Render settings

## 📝 Example Render.yaml

The included `render.yaml` file configures:
```yaml
services:
  - type: web
    name: behavior-prediction-api
    env: docker
    region: oregon
    plan: starter
    healthCheckPath: /health
    autoDeploy: true
```

Modify this file to customize your deployment settings.

---

**🎉 You're all set!** Your API should now be running on Render.com.

For questions or issues, check the Render dashboard logs or the troubleshooting section above.

