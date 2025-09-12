# Testing Guide - Google Calendar Integration

## Overview
This guide shows you how to test all components of your Google Calendar integration to ensure everything works correctly.

## Test Categories

### 1. 🔧 **Environment & Setup Tests**
Test that all environment variables and files are properly configured.

### 2. 📅 **Calendar Service Tests**
Test the Google Calendar service functionality.

### 3. 🤖 **AI Agent Integration Tests**
Test that calendar data is properly included in AI agent prompts.

### 4. 🌐 **Server Integration Tests**
Test the complete server with calendar integration.

### 5. 🚀 **Production Readiness Tests**
Test everything as it would work in production.

## Test Commands

### Quick Health Check
```bash
# Test 1: Environment variables
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('✅ Environment Variables:')
print(f'  GMAIL_PASSWORD: {\"✅ Set\" if os.getenv(\"GMAIL_PASSWORD\") else \"❌ Missing\"}')
print(f'  GOOGLE_CALENDAR_CREDENTIALS_FILE: {\"✅ Set\" if os.getenv(\"GOOGLE_CALENDAR_CREDENTIALS_FILE\") else \"❌ Missing\"}')
print(f'  GOOGLE_TOKEN_FILE: {\"✅ Set\" if os.getenv(\"GOOGLE_TOKEN_FILE\") else \"❌ Missing\"}')
print(f'  OPENAI_API_KEY: {\"✅ Set\" if os.getenv(\"OPENAI_API_KEY\") else \"❌ Missing\"}')
"
```

### Calendar Service Tests
```bash
# Test 2: Calendar service initialization
python services/calendar_service.py

# Test 3: Calendar service with detailed output
python -c "
import sys
sys.path.append('.')
from services.calendar_service import GoogleCalendarService
import json

print('🧪 Testing Calendar Service')
print('=' * 40)

# Initialize service
calendar_service = GoogleCalendarService()

# Get status
status = calendar_service.get_service_status()
print('📊 Service Status:')
print(json.dumps(status, indent=2))

# Test events
events_text = calendar_service.get_events_for_agent()
print(f'📅 Calendar Events: {events_text}')

# Test upcoming events
upcoming = calendar_service.get_upcoming_events()
print(f'�� Upcoming Events Count: {len(upcoming)}')

calendar_service.stop()
print('✅ Calendar service test completed')
"
```

### AI Agent Integration Tests
```bash
# Test 4: AI prompt integration
python -c "
import sys
sys.path.append('.')
from server import get_complete_prompt, get_calendar_service

print('🤖 Testing AI Agent Integration')
print('=' * 40)

# Test calendar service
calendar_svc = get_calendar_service()
if calendar_svc:
    print('✅ Calendar service initialized')
    
    # Test getting events
    events_text = calendar_svc.get_events_for_agent()
    print(f'📅 Events: {events_text[:100]}...')
    
    # Test complete prompt
    prompt = get_complete_prompt(use_personal=True)
    if 'Calendar:' in prompt:
        print('✅ Calendar events included in AI prompt')
        
        # Extract calendar section
        lines = prompt.split('\n')
        for line in lines:
            if 'Calendar:' in line:
                print(f'📅 Calendar line: {line}')
                break
    else:
        print('❌ Calendar events NOT found in AI prompt')
    
    calendar_svc.stop()
else:
    print('❌ Calendar service failed to initialize')
"
```

### Server Integration Tests
```bash
# Test 5: Complete server integration
python -c "
import sys
sys.path.append('.')
from server import main
import asyncio

print('🌐 Testing Server Integration')
print('=' * 40)

# This would normally start the server, but we'll just test imports
try:
    from server import get_calendar_service, get_complete_prompt
    print('✅ Server imports successful')
    
    # Test service initialization
    calendar_svc = get_calendar_service()
    if calendar_svc:
        print('✅ Calendar service available in server')
        calendar_svc.stop()
    else:
        print('❌ Calendar service not available in server')
        
except Exception as e:
    print(f'❌ Server integration error: {e}')
"
```

### Production Readiness Tests
```bash
# Test 6: Production readiness
python -c "
import sys
import os
sys.path.append('.')
from services.calendar_service import GoogleCalendarService
from dotenv import load_dotenv

print('🚀 Testing Production Readiness')
print('=' * 40)

load_dotenv()

# Check all required files exist
required_files = [
    'new_path/client_secret_*.json',
    'new_path/token.json',
    'new_path/ring-database-firebase-adminsdk-*.json'
]

print('📁 Checking required files:')
for pattern in required_files:
    import glob
    files = glob.glob(pattern)
    if files:
        print(f'  ✅ {pattern}: Found {len(files)} file(s)')
    else:
        print(f'  ❌ {pattern}: Missing')

# Test calendar service in production mode
try:
    calendar_service = GoogleCalendarService()
    status = calendar_service.get_service_status()
    
    print('📊 Production Status:')
    print(f'  Initialized: {status[\"initialized\"]}')
    print(f'  Auth Method: {status[\"authentication_method\"]}')
    print(f'  Cached Events: {status[\"cached_events_count\"]}')
    print(f'  Scheduler Running: {status[\"scheduler_running\"]}')
    
    if status['initialized'] and status['cached_events_count'] > 0:
        print('✅ Production ready!')
    else:
        print('⚠️  Production issues detected')
    
    calendar_service.stop()
    
except Exception as e:
    print(f'❌ Production test failed: {e}')
"
```

## Expected Results

### ✅ **Successful Test Results:**
- Environment variables: All set
- Calendar service: Initialized with OAuth2
- Events: Real calendar events fetched
- AI integration: Calendar data in prompts
- Server: All imports successful
- Production: All files present, service working

### ❌ **Common Issues & Solutions:**

#### Issue: "Credentials file not found"
**Solution**: Check file paths in `.env` file

#### Issue: "No refresh token present"
**Solution**: Re-run OAuth2 setup with `access_type=offline&prompt=consent`

#### Issue: "Calendar events not in AI prompt"
**Solution**: Check server integration in `server.py`

#### Issue: "Service not initialized"
**Solution**: Check OAuth2 credentials and token files

## Manual Testing

### Test Calendar Events Manually
1. Add a test event to your Google Calendar
2. Wait a few minutes
3. Run calendar service test
4. Verify the event appears in the output

### Test AI Agent Responses
1. Start your server
2. Send a test message asking about your schedule
3. Verify the AI mentions your calendar events

### Test Background Scheduler
1. Check logs for "Next calendar refresh scheduled for: [time]"
2. Wait until the scheduled time
3. Verify events are refreshed

## Performance Tests

### Test Event Caching
```bash
# Test caching performance
python -c "
import time
import sys
sys.path.append('.')
from services.calendar_service import GoogleCalendarService

calendar_service = GoogleCalendarService()

# First call (should fetch from API)
start = time.time()
events1 = calendar_service.get_events_for_agent()
time1 = time.time() - start

# Second call (should use cache)
start = time.time()
events2 = calendar_service.get_events_for_agent()
time2 = time.time() - start

print(f'First call: {time1:.3f}s')
print(f'Second call: {time2:.3f}s')
print(f'Cache speedup: {time1/time2:.1f}x faster')

calendar_service.stop()
"
```

## Troubleshooting

### Debug Mode
Add this to your code for detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Logs
Look for these key messages:
- `✅ Google Calendar API service initialized`
- `✅ Refreshed X real calendar events`
- `⏰ Next calendar refresh scheduled for: [time]`
- `✅ Calendar events included in prompt`

### Common Error Messages
- `❌ Credentials file not found`: Check file paths
- `❌ No refresh token present`: Re-run OAuth2 setup
- `❌ Error refreshing calendar events`: Check API quota/permissions
- `❌ Calendar service not initialized`: Check OAuth2 setup

## Success Criteria

Your integration is working correctly when:
1. ✅ All environment variables are set
2. ✅ Calendar service initializes with OAuth2
3. ✅ Real calendar events are fetched
4. ✅ Events are formatted correctly
5. ✅ Calendar data is included in AI prompts
6. ✅ Background scheduler is running
7. ✅ All required files are present
8. ✅ No error messages in logs

## Next Steps

After successful testing:
1. Deploy to Render.com
2. Test in production environment
3. Monitor logs for any issues
4. Set up monitoring/alerts if needed

Your Google Calendar integration is ready for production! 🎉
