# Kayros AI Reminder Integration

## Overview

Reminder calls now connect to **Kayros AI** for full conversational capability! Instead of just playing a message and hanging up, reminder calls:

1. **Announce the upcoming event** ("Hey Alessandro, this is Kayros. You have Team Meeting at 2PM in 10 minutes")
2. **Ask if you need anything** ("I'm here if you need anything. What's on your mind?")
3. **Connect to Kayros AI** - Full conversation with the same configuration as your personal assistant

## What Changed

### Before (Simple Voice Message)
```
☎️  Phone rings
🔊 "Hello! This is your calendar reminder. You have Team Meeting at 2PM in 10 minutes. Have a great day!"
📴 Call ends
```

### After (Kayros AI Integration)
```
☎️  Phone rings
🔊 "Hey Alessandro, this is Kayros. Quick reminder: you have Team Meeting at 2PM in 10 minutes."
🔊 "I'm here if you need anything. What's on your mind?"
🤖 Kayros AI activates - you can now talk!
💬 Ask questions, get help preparing for the event, or just chat
📴 You hang up when ready
```

## Features

✅ **Full AI conversation** - Same Kayros AI as your personal phone line  
✅ **Event context awareness** - Kayros knows why he called you  
✅ **Helpful assistance** - Can help you prepare for the event  
✅ **Natural interaction** - Ask questions, get advice, or just acknowledge  
✅ **Diary & calendar access** - Kayros has all your context  

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────┐
│            Reminder Service Detects Event            │
│         (10 minutes before event starts)             │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│              Twilio Outbound Call API                │
│                                                       │
│  TwiML Instructions:                                 │
│   1. <Say> Announce event                            │
│   2. <Say> Offer help                                │
│   3. <Connect><Stream> to websocket                  │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│           Your Server: /reminder Endpoint            │
│                                                       │
│  • Receives event info via URL parameters            │
│  • Adds event context to Kayros prompt               │
│  • Uses same config as /twilio endpoint              │
│  • Connects to Deepgram Agent API                    │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│              Deepgram Agent API                      │
│                                                       │
│  • Speech-to-Text (Nova-3)                           │
│  • LLM Processing (GPT-4.1)                          │
│  • Text-to-Speech (Aura-2 Odysseus)                 │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
              🗣️  Conversation!
```

### Technical Implementation

#### 1. TwiML with Stream Connection

The reminder service generates TwiML that connects to your websocket:

```xml
<Response>
    <Say voice="Polly.Joanna">
        Hey Alessandro, this is Kayros. Quick reminder: 
        you have Team Meeting starting at 02:00 PM in 10 minutes.
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Joanna">
        I'm here if you need anything. What's on your mind?
    </Say>
    <Connect>
        <Stream url="wss://your-server.com/reminder?event_name=Team%20Meeting&event_time=02:00%20PM&event_id=abc123" />
    </Connect>
</Response>
```

#### 2. Event Context in AI Prompt

When Kayros connects, he receives additional context:

```
IMPORTANT: This is a REMINDER CALL. Alessandro has "Team Meeting" starting at 02:00 PM.
You already announced this at the start of the call. Now he's talking to you.
Be helpful - ask if he needs anything, if he's prepared, or if he wants to discuss the event.
Keep the conversation focused and concise unless he wants to chat more.
```

#### 3. Intelligent Behavior

Kayros knows:
- This is a reminder call (not a random call from you)
- What event is coming up
- When the event starts
- He already announced it
- You're probably in a hurry

So he'll be concise and helpful, not chatty unless you want to talk more.

## Example Conversations

### Example 1: Quick Acknowledgment

```
📞 [Phone rings]

🤖 Kayros: "Hey Alessandro, this is Kayros. Quick reminder: you have 
            Team Meeting starting at 02:00 PM in 10 minutes."
            [pause]
            "I'm here if you need anything. What's on your mind?"

👤 You: "Thanks, I'm ready."

🤖 Kayros: "Perfect! Crush it."

👤 You: [hangs up]
```

### Example 2: Need Help

```
📞 [Phone rings]

🤖 Kayros: "Hey Alessandro, this is Kayros. Quick reminder: you have 
            Client Presentation starting at 03:00 PM in 10 minutes."
            [pause]
            "I'm here if you need anything. What's on your mind?"

👤 You: "Wait, what client? I don't remember the details."

🤖 Kayros: "Let me check your calendar... It's the quarterly review 
            with BlueJay. You have the deck ready from yesterday's prep."

👤 You: "Oh right, thanks! Anything I should remember?"

🤖 Kayros: "Yeah - they're focused on the Q4 metrics. Lead with the 
            wins, address concerns directly. You got this."

👤 You: "Perfect, thanks!"

🤖 Kayros: "Go get 'em."

👤 You: [hangs up]
```

### Example 3: Running Late

```
📞 [Phone rings]

🤖 Kayros: "Hey Alessandro, this is Kayros. Quick reminder: you have 
            Doctor Appointment starting at 10:00 AM in 10 minutes."
            [pause]
            "I'm here if you need anything. What's on your mind?"

👤 You: "Shit, I'm still 15 minutes away. Can you call them and let them know?"

🤖 Kayros: "I would, but I can't make calls yet. Text them or call directly. 
            Want me to look up the number?"

👤 You: "Yeah, what's the number?"

🤖 Kayros: "Based on your calendar notes, it's 216-555-0123."

👤 You: "Thanks!"

🤖 Kayros: "Drive safe, bro."

👤 You: [hangs up]
```

## Configuration

### Environment Variables

```bash
# Reminder Service Configuration
REMINDER_PHONE_NUMBER=+12162589844  # Your phone number
REMINDER_ADVANCE_MINUTES=10  # How many minutes before event
REMINDER_CHECK_INTERVAL_SECONDS=30  # How often to check

# Websocket URL (for production deployment)
REMINDER_WEBSOCKET_URL=wss://deepgram-twillio-server.onrender.com/reminder

# Calendar Refresh (for real-time updates)
CALENDAR_REFRESH_MINUTES=5  # Keep events up-to-date
```

### For Local Testing

When testing locally, you need a public URL for Twilio to connect to your websocket:

1. **Install ngrok**: `brew install ngrok` (or download from ngrok.com)
2. **Run your server**: `python server.py`
3. **Expose via ngrok**: `ngrok http 5000`
4. **Set the URL**: `export REMINDER_WEBSOCKET_URL=wss://your-ngrok-url.ngrok.io/reminder`
5. **Run test**: `python test_reminder_calls.py`

## Server Endpoints

Your server now has three websocket endpoints:

| Endpoint | Purpose | Used By |
|----------|---------|---------|
| `/twilio` | Personal assistant calls | Manual calls to your Twilio number |
| `/generic` | Public assistant calls | Anyone calling your public number |
| `/reminder` | Reminder calls | Automated reminder service |

All endpoints use the same infrastructure but with different configurations:
- `/twilio` and `/reminder` use personal prompt with diary + calendar
- `/reminder` adds event context and has no greeting (already spoken in TwiML)
- `/generic` uses public prompt (no personal data)

## Testing Locally

### Step 1: Start Your Server

```bash
cd /path/to/deepgram-twillio-server
python server.py
```

You should see:
```
✅ Calendar service initialized - events refreshed every 5 minutes
✅ Reminder service initialized - automated calls enabled
📞 Reminder status: calling +12162589844 10 minutes before events
```

### Step 2: Expose with ngrok

In a new terminal:
```bash
ngrok http 5000
```

Copy the `https://` URL (e.g., `https://abc123.ngrok.io`)

### Step 3: Set Websocket URL

```bash
export REMINDER_WEBSOCKET_URL=wss://abc123.ngrok.io/reminder
```

Or for full URLs:
```bash
# If ngrok gives you: https://abc123.ngrok.io
export REMINDER_WEBSOCKET_URL=wss://abc123.ngrok.io/reminder
```

### Step 4: Run Test Script

```bash
python test_reminder_calls.py
```

Choose option 1 to send a test call. You should:
1. Receive a call on your phone
2. Hear Kayros announce a test event
3. Be able to talk to Kayros normally
4. See the websocket connection in your server logs

## Troubleshooting

### "Connection failed" errors

**Problem**: Twilio can't connect to your websocket

**Solutions**:
1. Verify ngrok is running and showing traffic
2. Check `REMINDER_WEBSOCKET_URL` is correct (wss://, not https://)
3. Ensure your server is actually running on port 5000
4. Check ngrok console: `http://localhost:4040` for connection attempts

### Call connects but no AI response

**Problem**: Kayros doesn't respond after the initial announcement

**Solutions**:
1. Check server logs for websocket connection
2. Verify `DEEPGRAM_API_KEY` is set correctly
3. Check Deepgram console for API errors
4. Ensure you have Deepgram credits remaining

### AI doesn't know about the event

**Problem**: Kayros acts like a normal call, doesn't mention the event

**Solutions**:
1. Check server logs show event info: `Starting reminder Twilio handler for event: Team Meeting`
2. Verify URL parameters are being parsed correctly
3. Look for the reminder context being added to the prompt

### Voice quality issues

**Problem**: Choppy audio or delays

**Solutions**:
1. Check your internet connection
2. Use wired connection instead of WiFi for local testing
3. ngrok can add latency - this is normal for local testing
4. Production deployment will have better latency

## Production Deployment

When deployed to Render (or another platform):

1. ✅ No ngrok needed - your server has a public URL
2. ✅ Set `REMINDER_WEBSOCKET_URL` to your production URL:
   ```
   wss://deepgram-twillio-server.onrender.com/reminder
   ```
3. ✅ The reminder service automatically uses this URL
4. ✅ Everything works out of the box

### Render Environment Variables

Make sure these are set in Render:
```
DEEPGRAM_API_KEY=your_key_here
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
TWILIO_PHONE_NUMBER=+1234567890
REMINDER_PHONE_NUMBER=+12162589844
GMAIL_PASSWORD=your_gmail_app_password
GOOGLE_CALENDAR_CREDENTIALS_FILE=new_path/client_secret_*.json
GOOGLE_TOKEN_FILE=new_path/token.json
CALENDAR_REFRESH_MINUTES=5
REMINDER_WEBSOCKET_URL=wss://deepgram-twillio-server.onrender.com/reminder
```

## What Kayros Can Do During Reminder Calls

Because he's connected to the full AI system, Kayros can:

✅ **Answer questions** about the event details  
✅ **Look up information** from your calendar and diary  
✅ **Provide advice** on how to prepare  
✅ **Coach you** if you're anxious about the event  
✅ **Make jokes** to lighten the mood  
✅ **Be brief** if you just want to acknowledge and go  
✅ **Keep you accountable** based on your diary entries  

He **cannot** (yet):
❌ Reschedule events  
❌ Send emails during the call  
❌ Make outbound calls to others  
❌ Add calendar events  

## Cost Considerations

### With Kayros AI Connection

**Twilio Costs** (same as before):
- Outbound call: ~$0.013/min
- Call duration: ~30 seconds to 3 minutes depending on conversation
- Average: ~$0.01 per reminder

**Deepgram Costs** (new):
- Speech-to-Text: $0.0043/min
- Text-to-Speech: $0.015/min  
- Combined: ~$0.02/min of conversation
- Short call (1 min): ~$0.02
- Longer call (3 min): ~$0.06

**OpenAI Costs** (new):
- GPT-4.1 API calls during conversation
- ~$0.01-0.05 per call depending on length
- Very reasonable for the value

**Total Per Reminder**:
- Quick acknowledgment (30 sec): ~$0.02
- Normal conversation (1-2 min): ~$0.05
- Longer discussion (3-5 min): ~$0.10

**Monthly Estimate**:
- 5 events/day × 30 days = 150 reminders
- Average $0.05 per reminder = **$7.50/month**
- Well worth it for never missing important events! 💪

## Advanced Customization

### Custom Announcement Voice

Edit `services/reminder_service.py`, line 142-148:

```python
<Say voice="Polly.Matthew">  <!-- Male voice -->
    Hey bro, Kayros here. You got {event_name} at {formatted_time} in {self.advance_minutes} minutes.
</Say>
```

### Different Behavior for Different Events

You could add logic to customize based on event name:

```python
if "workout" in event_name.lower():
    announcement = "Time to hit the gym, beast mode activated!"
elif "meeting" in event_name.lower():
    announcement = "Business time. Let's crush this meeting."
else:
    announcement = f"You have {event_name} coming up."
```

### Skip AI for Quick Events

For very short events, you might want just the announcement:

```python
# Don't connect to AI for events under 15 minutes
if event_duration_minutes < 15:
    # Just play announcement and hang up
    return simple_twiml
else:
    # Connect to Kayros for longer events
    return connect_twiml
```

## Summary

Your reminder system is now a **full-featured AI assistant** that:
1. Proactively calls you before events
2. Gives you the context you need
3. Stays on the line to help if needed
4. Has all your personal data for intelligent responses
5. Maintains the same personality and coaching style as your main assistant

This is like having a personal executive assistant who:
- Never forgets your schedule
- Always calls on time
- Knows everything about your life
- Gives great advice
- Is available 24/7

**Never miss an important event again!** 📅🤖📞✅

