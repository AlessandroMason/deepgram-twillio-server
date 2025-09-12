# Google Calendar Integration - Code Explanation

## Overview
The calendar service fetches real Google Calendar events and provides them to your AI agent in a simplified format. It uses OAuth2 refresh tokens for secure, long-term access without requiring user interaction.

## Key Files

### 1. `services/calendar_service.py` - Main Calendar Service
**Purpose**: Fetches and caches Google Calendar events

**Key Components**:

#### OAuth2 Authentication
```python
def _build_calendar_from_token(self):
    # Loads refresh token from token.json
    # Automatically refreshes access tokens when needed
    # Returns Google Calendar API service
```

#### Event Fetching
```python
def refresh_events(self):
    # Calls Google Calendar API
    # Fetches upcoming events (max 10)
    # Processes and formats events
    # Caches results in memory
```

#### Event Formatting
```python
def get_events_for_agent(self) -> str:
    # Converts events to simple format: "Event Name - Time (Duration)"
    # Example: "CSDS 310 - 11:40 AM (50m)"
    # Returns: "Calendar: Event1, Event2, Event3"
```

#### Background Scheduler
```python
def _midnight_refresh_loop(self):
    # Runs in background thread
    # Refreshes events at midnight daily
    # Handles errors gracefully
```

### 2. `server.py` - Server Integration
**Purpose**: Integrates calendar service with your main server

**Key Integration**:
```python
def get_calendar_service():
    # Creates/returns global calendar service instance
    # Handles initialization errors gracefully

def get_complete_prompt(use_personal=True):
    # Includes calendar events in AI agent prompt
    # Combines with diary data
    # Returns complete context for AI
```

### 3. Environment Variables (`.env`)
```bash
GOOGLE_CALENDAR_CREDENTIALS_FILE=new_path/client_secret_*.json
GOOGLE_TOKEN_FILE=new_path/token.json
GMAIL_PASSWORD="your_app_password"
```

## How It Works

### 1. Initialization
1. Load environment variables from `.env`
2. Initialize OAuth2 service with refresh token
3. Start background scheduler for midnight refresh
4. Cache initial events

### 2. Event Processing
1. Fetch events from Google Calendar API
2. Parse start/end times and durations
3. Format as "Name - Time (Duration)"
4. Cache in memory for fast access

### 3. AI Agent Integration
1. Server calls `get_events_for_agent()`
2. Returns formatted string: "Calendar: Event1, Event2, Event3"
3. Included in AI agent's context prompt
4. AI can reference your schedule when responding

### 4. Background Refresh
1. Scheduler runs in separate thread
2. Calculates time until next midnight
3. Refreshes events automatically
4. Updates cache with new events

## Security Features

### OAuth2 Refresh Tokens
- **Long-lived**: Works indefinitely (unless revoked)
- **Auto-refresh**: Automatically gets new access tokens
- **Secure**: No passwords stored, uses Google's OAuth2
- **Server-friendly**: No browser interaction needed

### File Security
- `token.json`: Contains refresh token (keep secret!)
- `credentials.json`: OAuth2 client credentials (keep secret!)
- Both files in `.gitignore` (not committed to git)

## Error Handling

### Graceful Degradation
- If OAuth2 fails → Falls back to Gmail IMAP test
- If API fails → Uses mock events
- If scheduler fails → Continues with cached events
- Always provides some calendar data to AI

### Logging
- Clear status messages for debugging
- Error details for troubleshooting
- Service status reporting

## Performance

### Caching
- Events cached in memory
- Refreshed only at midnight
- Fast access for AI agent
- Reduces API calls

### Efficiency
- Fetches only upcoming events (max 10)
- Simple string format for AI
- Background processing
- Minimal server impact

## Deployment Considerations

### For Render.com
1. **Environment Variables**: Set in Render dashboard
2. **Secret Files**: Upload as environment variables or use secret management
3. **Token Refresh**: Works automatically in production
4. **Background Threads**: Render supports long-running processes

### Required Files for Deployment
- `token.json` (with refresh token)
- `credentials.json` (OAuth2 client credentials)
- Environment variables set in Render

### Render Environment Variables
```bash
GOOGLE_CALENDAR_CREDENTIALS_FILE=/opt/render/project/src/new_path/client_secret_*.json
GOOGLE_TOKEN_FILE=/opt/render/project/src/new_path/token.json
GMAIL_PASSWORD=your_app_password
OPENAI_API_KEY=your_openai_key
FIREBASE_SERVICE_ACCOUNT_PATH=/opt/render/project/src/new_path/firebase_*.json
```

## Usage Example

When you ask your AI agent: "What do I have today?"
The agent receives context like:
```
Calendar: CSDS 310 - 11:40 AM (50m), ThinkEnergy Week 3 - 01:00 PM (1h), CSDS 393 - 03:15 PM (1h 30m)
```

And can respond: "You have CSDS 310 at 11:40 AM (50 minutes), ThinkEnergy Week 3 at 1:00 PM (1 hour), and CSDS 393 at 3:15 PM (1.5 hours)."
