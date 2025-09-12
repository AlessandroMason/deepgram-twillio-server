# Render.com Deployment Guide

## Overview
This guide helps you deploy your Deepgram Twilio server with Google Calendar integration to Render.com.

## Prerequisites
- Render.com account
- GitHub repository with your code
- Google Calendar OAuth2 setup completed
- All required files in `new_path/` directory

## Step 1: Prepare Your Repository

### Required Files Structure
```
your-repo/
├── server.py
├── services/
│   └── calendar_service.py
├── new_path/
│   ├── client_secret_*.json (OAuth2 credentials)
│   ├── token.json (refresh token)
│   └── firebase_*.json (Firebase credentials)
├── .env (for local development only)
├── requirements.txt
└── docs/
```

### Files to Keep Secret
- `new_path/client_secret_*.json`
- `new_path/token.json` 
- `new_path/firebase_*.json`
- `.env` (don't commit this)

## Step 2: Render.com Setup

### Create New Web Service
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Choose your repository

### Service Configuration
- **Name**: `deepgram-twilio-server` (or your preferred name)
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python server.py`
- **Plan**: Free tier works for testing

## Step 3: Environment Variables

Set these in Render Dashboard → Your Service → Environment:

### Required Variables
```bash
# Google Calendar OAuth2
GOOGLE_CALENDAR_CREDENTIALS_FILE=/opt/render/project/src/new_path/client_secret_1026226421787-u4gs6bh6ora2q8a77ro3c1ov35ab2lcc.apps.googleusercontent.com.json
GOOGLE_TOKEN_FILE=/opt/render/project/src/new_path/token.json

# Gmail (for fallback)
GMAIL_PASSWORD=bhrv noda retb rnuj

# OpenAI


# Firebase
FIREBASE_SERVICE_ACCOUNT_PATH=/opt/render/project/src/new_path/ring-database-firebase-adminsdk-essjy-0cfe7d82d0.json
```

## Step 4: Secret File Management

### Option A: Environment Variables (Recommended)
Convert your JSON files to environment variables:

1. **For credentials.json**:
```bash
GOOGLE_CALENDAR_CREDENTIALS='{"installed":{"client_id":"...","project_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_secret":"...","redirect_uris":["..."]}}'
```

2. **For token.json**:
```bash
GOOGLE_CALENDAR_TOKEN='{"token":"...","refresh_token":"...","token_uri":"...","client_id":"...","client_secret":"...","scopes":["https://www.googleapis.com/auth/calendar.readonly"],"expiry":"..."}'
```

3. **For firebase.json**:
```bash
FIREBASE_CREDENTIALS='{"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}'
```

### Option B: Render Disk (Alternative)
1. Upload files to Render's persistent disk
2. Update file paths in environment variables
3. Files persist across deployments

## Step 5: Update Code for Environment Variables

Modify `services/calendar_service.py` to handle environment variable credentials:

```python
def _build_calendar_from_token(self):
    # Check for environment variable first
    creds_json = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
    token_json = os.getenv("GOOGLE_CALENDAR_TOKEN")
    
    if creds_json and token_json:
        # Use environment variables
        creds_data = json.loads(creds_json)
        token_data = json.loads(token_json)
        # ... rest of OAuth2 logic
    else:
        # Fall back to file-based approach
        # ... existing file logic
```

## Step 6: Deploy and Test

### Deploy
1. Save all environment variables in Render
2. Click "Deploy" in Render dashboard
3. Monitor build logs for errors

### Test Calendar Integration
1. Check Render logs for calendar service initialization
2. Look for: "✅ Google Calendar API service initialized"
3. Verify: "✅ Refreshed X real calendar events"

### Test Webhook
1. Use your Render URL: `https://your-app.onrender.com`
2. Test with Deepgram webhook
3. Verify AI agent includes calendar data

## Step 7: Monitoring

### Render Dashboard
- Monitor service health
- Check logs for errors
- View resource usage

### Calendar Service Status
Look for these log messages:
- `✅ Google Calendar API service initialized`
- `✅ Refreshed X real calendar events`
- `⏰ Next calendar refresh scheduled for: [time]`

## Troubleshooting

### Common Issues

#### 1. OAuth2 Token Expired
**Error**: "No refresh token present"
**Solution**: Re-run OAuth2 setup locally, update token in Render

#### 2. File Not Found
**Error**: "Credentials file not found"
**Solution**: Check file paths in environment variables

#### 3. Calendar API Quota
**Error**: "Quota exceeded"
**Solution**: Google Calendar API has generous limits, check for API errors

#### 4. Background Thread Issues
**Error**: Scheduler not running
**Solution**: Render supports background threads, check logs

### Debug Commands
Add to your code for debugging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Best Practices

### Environment Variables
- Never commit secrets to git
- Use Render's environment variable system
- Rotate tokens periodically

### OAuth2 Security
- Refresh tokens are long-lived but can be revoked
- Monitor for unauthorized access
- Use HTTPS only (Render provides this)

### File Permissions
- Render runs with appropriate permissions
- Secret files are not publicly accessible
- Environment variables are encrypted

## Cost Considerations

### Render Free Tier
- 750 hours/month
- Sleeps after 15 minutes of inactivity
- Good for development/testing

### Render Paid Plans
- Always-on service
- Better performance
- More resources

## Next Steps

1. **Deploy to Render**: Follow steps above
2. **Test Integration**: Verify calendar data in AI responses
3. **Monitor Performance**: Check logs and resource usage
4. **Scale as Needed**: Upgrade Render plan if required

Your AI agent will now have access to your real Google Calendar events in production! 🎉
