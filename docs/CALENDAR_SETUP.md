# Google Calendar Service Setup Guide

This guide will help you set up the Google Calendar service that caches upcoming events and refreshes them at midnight.

## 📋 Overview

The Google Calendar service provides:
- **Event Caching**: Stores upcoming calendar events in memory for fast access
- **Midnight Refresh**: Automatically refreshes events at midnight every day
- **Agent Integration**: Provides formatted calendar data to the AI agent
- **Background Scheduler**: Runs continuously to maintain fresh data

## 🔧 Setup Steps

### 1. Environment Variables

The calendar service uses the same Gmail credentials as the email service:

```bash
# Gmail App Password (same as email service)
export GMAIL_PASSWORD="your_gmail_app_password"
```

### 2. Dependencies

The required dependencies are already included in `requirements.txt`:
- `google-auth==2.23.4`
- `google-auth-oauthlib==1.1.0`
- `google-auth-httplib2==0.1.1`
- `google-api-python-client==2.108.0`
- `pytz==2024.1`

### 3. Gmail App Password Setup

1. Enable 2-factor authentication on your Gmail account
2. Go to Google Account settings > Security > 2-Step Verification > App passwords
3. Generate an app password for "Mail"
4. Use this 16-character password (without spaces) as `GMAIL_PASSWORD`

## 🚀 Usage

### Basic Usage

```python
from services.calendar_service import GoogleCalendarService

# Initialize service (uses GMAIL_PASSWORD env var)
calendar_service = GoogleCalendarService()

# Get upcoming events
events = calendar_service.get_upcoming_events(days_ahead=7)

# Get formatted events for AI agent
agent_events = calendar_service.get_events_for_agent()

# Get service status
status = calendar_service.get_service_status()
```

### Integration with Voice Agent

The calendar service is automatically integrated into the main server:

1. **Server Startup**: Calendar service initializes when server starts
2. **Event Caching**: Events are cached in memory for fast access
3. **Midnight Refresh**: Events automatically refresh at midnight
4. **Agent Prompt**: Calendar events are included in the AI agent's prompt

## 📅 Features

### Event Caching
- Events are cached in memory for instant access
- No API calls needed during conversations
- Reduces latency and API quota usage

### Midnight Refresh
- Background thread refreshes events at midnight
- Automatic scheduling without manual intervention
- Graceful error handling and recovery

### Agent Integration
- Events formatted specifically for AI agent consumption
- Includes event details, times, and locations
- Automatically included in personal endpoint prompts

## 🧪 Testing

Run the test script to verify the setup:

```bash
python tests/test_calendar_service.py
```

The test will:
- Check environment variables
- Initialize the calendar service
- Test event retrieval
- Verify scheduler functionality
- Test agent formatting

## 🔧 Configuration

### Service Configuration

```python
# Initialize with custom settings
calendar_service = GoogleCalendarService(
    gmail_email="your-email@gmail.com",
    gmail_password="your_app_password"
)
```

### Event Retrieval

```python
# Get events for different time periods
events_3_days = calendar_service.get_upcoming_events(days_ahead=3)
events_week = calendar_service.get_upcoming_events(days_ahead=7)
events_month = calendar_service.get_upcoming_events(days_ahead=30)
```

## 📊 Service Status

Check the service status:

```python
status = calendar_service.get_service_status()
print(json.dumps(status, indent=2))
```

Returns:
```json
{
  "initialized": true,
  "cached_events_count": 5,
  "last_refresh": "2024-01-15T00:00:00",
  "scheduler_running": true,
  "gmail_email": "axm2022@case.edu"
}
```

## 🔄 Midnight Refresh

The service automatically refreshes events at midnight:

1. **Background Thread**: Runs continuously
2. **Smart Scheduling**: Calculates time until next midnight
3. **Event Refresh**: Fetches latest events from Google Calendar
4. **Error Handling**: Continues running even if refresh fails

## 🛠️ Troubleshooting

### Common Issues

**Calendar service not available**
- Check that `GMAIL_PASSWORD` environment variable is set
- Verify Gmail app password is correct

**No events found**
- Ensure calendar has upcoming events
- Check date range (default is 7 days ahead)

**Scheduler not running**
- Check service initialization
- Verify background thread is active

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔐 Security Notes

- Uses Gmail app password (not main password)
- Credentials stored in environment variables
- No sensitive data logged
- Secure API communication

## 📈 Performance

- **Memory Usage**: Minimal (events cached in memory)
- **API Calls**: Only at midnight refresh
- **Response Time**: Instant (cached data)
- **Reliability**: Background thread with error recovery

## 🔮 Future Enhancements

Planned improvements:
- OAuth2 authentication for full Google Calendar access
- Multiple calendar support
- Event creation and modification
- Real-time event updates
- Custom refresh intervals
