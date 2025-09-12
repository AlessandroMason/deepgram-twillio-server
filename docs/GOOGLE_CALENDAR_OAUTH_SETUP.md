# Google Calendar OAuth2 Setup Guide

This guide will help you set up real Google Calendar integration using OAuth2.

## Prerequisites

- Google account (axm2022@case.edu)
- Access to Google Cloud Console

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID

## Step 2: Enable Google Calendar API

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Calendar API"
3. Click on it and press "Enable"

## Step 3: Create OAuth2 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in required fields (App name, User support email, Developer contact)
   - Add your email (axm2022@case.edu) to test users
4. For Application type, choose "Desktop application"
5. Give it a name (e.g., "Calendar Service")
6. Click "Create"

## Step 4: Download Credentials

1. After creating the OAuth client ID, click the download button (⬇️)
2. Save the JSON file as `credentials.json`
3. Place it in your project root directory (same level as `server.py`)

## Step 5: Test the Setup

Run the calendar service to complete OAuth2 authentication:

```bash
python services/calendar_service.py
```

This will:
1. Open your browser for OAuth2 authentication
2. Ask you to sign in with your Google account
3. Request permission to access your calendar
4. Save the token for future use

## Step 6: Verify Real Calendar Data

After completing OAuth2, the service will fetch your real calendar events instead of mock data.

## Troubleshooting

### "Credentials file not found"
- Make sure `credentials.json` is in the project root
- Check the file name is exactly `credentials.json`

### "Access blocked" during OAuth2
- Make sure your email is added to test users in OAuth consent screen
- The app might need verification for production use

### "Invalid credentials"
- Delete `token.json` and try again
- Re-download `credentials.json` from Google Cloud Console

## Security Notes

- `credentials.json` and `token.json` are in `.gitignore` and won't be committed
- Keep these files secure and don't share them
- The OAuth2 token will auto-refresh as needed

## Current Status

The calendar service is currently using mock data as a fallback. Once you complete the OAuth2 setup above, it will automatically switch to real calendar data.

Your calendar events will appear in the format:
```
Calendar: Event Name - Time (Duration)
```

For example:
```
Calendar: Team Meeting - 02:00 PM (1h), Doctor Appointment - 10:30 AM (30m)
```
