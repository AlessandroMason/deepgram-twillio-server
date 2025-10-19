# Calendar Reminder Setup Guide

This guide explains how to set up and test the automated calendar reminder calling feature.

## Overview

The reminder service automatically monitors your Google Calendar and makes phone calls 10 minutes before each event starts. It uses:
- **Google Calendar API** - To fetch upcoming events
- **Twilio** - To make outbound phone calls
- **Background monitoring** - Checks for upcoming events every 30 seconds

## Features

✅ **Real-time calendar updates** - Refreshes every 5 minutes (configurable)  
✅ **Automated reminder calls** - Calls you 10 minutes before events (configurable)  
✅ **Smart tracking** - Won't call twice for the same event  
✅ **Local testing** - Test everything before deploying  
✅ **Customizable** - Configure phone number, timing, and intervals

## Environment Variables

Add these to your `.env` file:

```bash
# Twilio Configuration (Required for reminders)
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890  # Your Twilio phone number

# Reminder Configuration
REMINDER_PHONE_NUMBER=+12162589844  # Phone number to receive reminders (default)
REMINDER_ADVANCE_MINUTES=10  # How many minutes before event to call (default: 10)
REMINDER_CHECK_INTERVAL_SECONDS=30  # How often to check for events (default: 30)

# Calendar Refresh Configuration
CALENDAR_REFRESH_MINUTES=5  # How often to refresh calendar (default: 5, 0 = midnight only)

# Google Calendar (Already configured)
GMAIL_PASSWORD=your_app_password_here
GOOGLE_CALENDAR_CREDENTIALS_FILE=new_path/client_secret_*.json
GOOGLE_TOKEN_FILE=new_path/token.json
```

## Getting Twilio Credentials

1. **Sign up for Twilio** (if you haven't already)
   - Go to https://www.twilio.com/try-twilio
   - Sign up for a free account
   - You get a free trial with $15 credit

2. **Get your credentials**
   - Go to https://console.twilio.com/
   - Find your **Account SID** and **Auth Token** on the dashboard
   - Add them to your `.env` file

3. **Get a phone number**
   - In the Twilio console, go to "Phone Numbers" > "Manage" > "Buy a number"
   - Choose a number (free with trial)
   - Add it to your `.env` as `TWILIO_PHONE_NUMBER`

## Local Testing

### Step 1: Install Dependencies

```bash
# Install the new Twilio package
pip install -r requirements.txt
```

### Step 2: Run the Test Script

```bash
python test_reminder_calls.py
```

The test script will:
1. ✅ Check all environment variables are set
2. ✅ Initialize calendar service with 5-minute refresh
3. ✅ Initialize reminder service
4. ✅ Show interactive menu with options:
   - Send a test reminder call now
   - Monitor for upcoming events (60 seconds)
   - Check service status
   - Exit

### Step 3: Test a Live Call

From the test menu:
1. Choose option **1** to send a test call
2. Confirm when prompted
3. Your phone should ring within seconds
4. You'll hear: *"This is a test reminder call from your calendar assistant..."*

### Step 4: Test Event Monitoring

From the test menu:
1. Choose option **2** to monitor for upcoming events
2. The script will check for events in the next 10 minutes
3. If any events are found, you'll receive a call
4. The call will say: *"You have [Event Name] starting at [Time] in 10 minutes"*

## How It Works

### Architecture

```
┌─────────────────────┐
│  Google Calendar    │
│                     │
│  Your Events        │
└──────────┬──────────┘
           │
           │ Refreshes every 5 min
           ▼
┌─────────────────────┐
│  Calendar Service   │
│                     │
│  Cached Events      │
└──────────┬──────────┘
           │
           │ Monitors every 30 sec
           ▼
┌─────────────────────┐
│  Reminder Service   │
│                     │
│  Checks if event    │
│  is 10 min away     │
└──────────┬──────────┘
           │
           │ When triggered
           ▼
┌─────────────────────┐
│  Twilio API         │
│                     │
│  Makes phone call   │
└──────────┬──────────┘
           │
           ▼
    📞 Your Phone Rings!
```

### Call Flow

1. **Monitoring**: Every 30 seconds, the reminder service checks cached calendar events
2. **Detection**: If an event starts in 10 minutes (within the check window), trigger a call
3. **Deduplication**: Event ID is tracked to prevent duplicate calls
4. **Calling**: Twilio makes an outbound call to your configured phone number
5. **Voice Message**: TwiML plays a voice message with event details
6. **Cleanup**: After the event passes, the event ID is removed from tracking

### Sample Call Script (TwiML)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">
        Hello! This is your calendar reminder.
        You have Team Meeting starting at 02:00 PM in 10 minutes.
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Joanna">
        Have a great day!
    </Say>
</Response>
```

## Configuration Options

### Reminder Phone Number
```bash
REMINDER_PHONE_NUMBER=+12162589844
```
- The phone number to receive reminder calls
- Must include country code (e.g., +1 for US)
- Default: `+12162589844`

### Advance Time
```bash
REMINDER_ADVANCE_MINUTES=10
```
- How many minutes before the event to call
- Recommended: 5-15 minutes
- Default: `10`

### Check Interval
```bash
REMINDER_CHECK_INTERVAL_SECONDS=30
```
- How often to check for upcoming events
- Recommended: 30-60 seconds (lower = more responsive, higher = less resource usage)
- Default: `30`

### Calendar Refresh Interval
```bash
CALENDAR_REFRESH_MINUTES=5
```
- How often to refresh calendar from Google
- Set to `0` for midnight-only refresh
- Recommended: 5-10 minutes for reminders to work well
- Default: `5`

## Production Deployment

### Running in Production

When you deploy to Render or another platform:

1. **Set all environment variables** in the platform's settings
2. **The reminder service starts automatically** when the server starts
3. **No additional setup needed** - it runs in the background

### Monitoring

Check the server logs for:
- ✅ `Calendar service initialized - events refreshed every 5 minutes`
- ✅ `Reminder service initialized - automated calls enabled`
- ✅ `Reminder status: calling +12162589844 10 minutes before events`

When a reminder is sent:
- 🔔 `Event 'Team Meeting' is 10 minutes away - sending reminder!`
- ✅ `Reminder call initiated: SID=CA1234567890abcdef`

## Troubleshooting

### "Reminder service not available"

**Problem**: Server logs show reminder service failed to initialize

**Solutions**:
1. Check that all Twilio environment variables are set correctly
2. Verify `GMAIL_PASSWORD` is set (calendar service required)
3. Check server logs for specific error messages

### No calls received

**Problem**: Service is running but no calls come through

**Solutions**:
1. Verify you have events in your calendar within the next 10 minutes
2. Check that `REMINDER_PHONE_NUMBER` is correct (include country code)
3. Run the test script locally to verify Twilio credentials work
4. Check Twilio console for call logs: https://console.twilio.com/logs/calls
5. Ensure your phone can receive calls from the Twilio number

### Calls are delayed

**Problem**: Calls arrive late or not at the right time

**Solutions**:
1. Decrease `CALENDAR_REFRESH_MINUTES` to 3-5 minutes
2. Decrease `REMINDER_CHECK_INTERVAL_SECONDS` to 20-30 seconds
3. Check server timezone matches your timezone expectations

### Too many duplicate calls

**Problem**: Receiving multiple calls for the same event

**Solutions**:
1. This shouldn't happen due to event tracking
2. Check server logs for errors in the monitoring loop
3. Restart the server to clear the notified events cache

## Cost Considerations

### Twilio Pricing (as of 2024)

- **Trial Account**: $15 credit free
- **Outbound calls**: ~$0.013/min (US)
- **Phone number**: $1.15/month

### Example Usage

If you have:
- 5 events per day
- Each call is ~30 seconds long
- 30 days in a month

**Monthly cost**: ~$1.15 (phone) + $0.10 (calls) = **$1.25/month**

### Free Trial Limitations

- Can only call verified phone numbers
- Calls include a trial message: "You have a trial account..."
- To remove, upgrade to a paid account ($20 minimum)

## Advanced Customization

### Custom Call Messages

Edit `services/reminder_service.py`, method `_send_reminder_call()`:

```python
twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">
        Your custom message here!
        Event: {event_name} at {formatted_time}
    </Say>
</Response>"""
```

Available voices:
- `Polly.Joanna` (Female, US)
- `Polly.Matthew` (Male, US)
- `Polly.Amy` (Female, British)
- `Polly.Brian` (Male, British)
- See more: https://www.twilio.com/docs/voice/twiml/say/text-speech#amazon-polly

### Multiple Phone Numbers

To call multiple numbers, modify `_send_reminder_call()` to loop:

```python
phone_numbers = ["+12162589844", "+19876543210"]
for number in phone_numbers:
    call = self.twilio_client.calls.create(
        twiml=twiml,
        to=number,
        from_=self.twilio_phone_number
    )
```

### Different Advance Times for Different Events

You could add logic to check event title and adjust timing:

```python
event_name = event.get("summary", "")
if "urgent" in event_name.lower():
    advance_minutes = 15  # More time for urgent events
else:
    advance_minutes = 10  # Standard time
```

## Testing Tips

### Create Test Events

To test thoroughly:
1. Create a Google Calendar event 15 minutes from now
2. Run the test script: `python test_reminder_calls.py`
3. Choose option 2 (monitor for 60 seconds)
4. Wait for the monitoring to detect the event
5. You should receive a call when the event is 10 minutes away

### Check Logs

When running locally, watch for:
```
🔔 Event 'Test Event' is 10 minutes away - sending reminder!
✅ Reminder call initiated: SID=CA1234567890abcdef
   Event: Test Event
   Time: 02:00 PM
   To: +12162589844
```

### Verify Twilio

Check calls in Twilio console:
1. Go to https://console.twilio.com/logs/calls
2. Find your call by SID or time
3. Check status (should be "completed")
4. Listen to recording (if enabled)

## FAQ

**Q: Can I use this with a free Twilio account?**  
A: Yes, but you can only call verified phone numbers and calls include a trial message.

**Q: Does this work with all calendar services?**  
A: Currently only Google Calendar is supported.

**Q: Can I get SMS reminders instead of calls?**  
A: Yes! Modify `_send_reminder_call()` to use `messages.create()` instead of `calls.create()`.

**Q: Will this drain my Twilio credit?**  
A: Very slowly. Each ~30-second call costs ~$0.01. 100 reminders = ~$1.

**Q: What happens if I miss the reminder call?**  
A: The call will go to voicemail if you don't answer. Twilio doesn't retry automatically.

**Q: Can I test without making real calls?**  
A: Not really - Twilio doesn't have a full sandbox mode for voice calls. The test script lets you confirm before making calls.

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review server logs for error messages
3. Test locally with `test_reminder_calls.py`
4. Verify Twilio credentials in the Twilio console
5. Check Google Calendar API is working with `test_calendar_integration.py`

## Next Steps

Once testing is complete:
1. ✅ Commit the changes to git
2. ✅ Set environment variables in Render dashboard
3. ✅ Deploy to production
4. ✅ Check logs to confirm services started
5. ✅ Create a test event to verify end-to-end

Happy scheduling! 📅📞

