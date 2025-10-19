import asyncio
import base64
import json
import sys
import websockets
import ssl
import os
from services.optimized_diary_service import OptimizedDiaryService

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not available, using system environment variables")
from services.calendar_service import GoogleCalendarService
from services.reminder_service import ReminderService
#from services.email_service import EmailService
from agents.constants import (
    INITIAL_PROMPT, 
    GREETING, 
    USER_ID, 
    DIARY_DAYS, 
    DIARY_MAX_ENTRIES, 
    DIARY_MAX_CHARS,
    FALLBACK_DIARY
)
from agents.constants_generic import (
    INITIAL_PROMPT_GENERIC,
    GREETING_GENERIC,
    DIARY_DAYS_GENERIC,
    DIARY_MAX_ENTRIES_GENERIC,
    DIARY_MAX_CHARS_GENERIC,
    FALLBACK_DIARY_GENERIC
)

# Global service instances for caching across requests
diary_service = None
calendar_service = None
reminder_service = None

def get_diary_service():
    """
    Get or create the global diary service instance
    """
    global diary_service
    if diary_service is None:
        diary_service = OptimizedDiaryService()
    return diary_service

def get_calendar_service():
    """
    Get or create the global calendar service instance
    """
    global calendar_service
    if calendar_service is None:
        try:
            # Get refresh interval from environment (default: 5 minutes for reminders to work well)
            refresh_minutes = int(os.getenv("CALENDAR_REFRESH_MINUTES", "5"))
            calendar_service = GoogleCalendarService(refresh_interval_minutes=refresh_minutes)
        except ValueError as e:
            print(f"⚠️  Calendar service not available: {e}")
            calendar_service = None
    return calendar_service

def get_reminder_service():
    """
    Get or create the global reminder service instance
    """
    global reminder_service
    if reminder_service is None:
        calendar_svc = get_calendar_service()
        if calendar_svc is None:
            print("⚠️  Reminder service not available: calendar service required")
            return None
        
        try:
            # Get configuration from environment
            phone_number = os.getenv("REMINDER_PHONE_NUMBER", "+12162589844")
            advance_minutes = int(os.getenv("REMINDER_ADVANCE_MINUTES", "10"))
            check_interval = int(os.getenv("REMINDER_CHECK_INTERVAL_SECONDS", "30"))
            
            reminder_service = ReminderService(
                calendar_service=calendar_svc,
                phone_number=phone_number,
                advance_minutes=advance_minutes,
                check_interval_seconds=check_interval
            )
        except ValueError as e:
            print(f"⚠️  Reminder service not available: {e}")
            reminder_service = None
        except Exception as e:
            print(f"⚠️  Reminder service initialization failed: {e}")
            reminder_service = None
    return reminder_service


def sts_connect():
    # you can run export DEEPGRAM_API_KEY="your key" in your terminal to set your API key.
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY environment variable is not set")

    sts_ws = websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse", subprotocols=["token", api_key]
    )
    return sts_ws


def get_complete_prompt(use_personal=True, reminder_event=None):
    """
    Get the complete prompt with diary data and calendar events included immediately
    
    Args:
        use_personal: If True, use personal prompt with diary data and calendar. If False, use generic prompt.
        reminder_event: If provided, adds context about the upcoming event (for reminder calls)
    """
    if use_personal:
        try:
            # Get the optimized service
            service = get_diary_service()
            
            # Get formatted diary entries with limits
            diary_section = service.get_diary_prompt_section(
                USER_ID, 
                days=DIARY_DAYS, 
                max_entries=DIARY_MAX_ENTRIES, 
                max_chars=DIARY_MAX_CHARS
            )
            
            # Get calendar events
            calendar_section = ""
            calendar_svc = get_calendar_service()
            if calendar_svc:
                calendar_section = calendar_svc.get_events_for_agent()
            else:
                calendar_section = "Calendar service not available."
            
            # Add reminder event context if this is a reminder call
            reminder_context = ""
            if reminder_event:
                event_name = reminder_event.get("name", "Unknown event")
                event_time = reminder_event.get("time", "Unknown time")
                advance_min = reminder_event.get("advance_minutes", "10")
                
                # Get all upcoming events for additional context
                all_events = calendar_section if calendar_section != "Calendar service not available." else "No other events available."
                
                reminder_context = f"""
IMPORTANT CONTEXT - THIS IS A REMINDER CALL:
- You are calling Alessandro to remind him about: "{event_name}" starting at {event_time} (in {advance_min} minutes)
- You already announced this in your greeting
- Be helpful - ask if he needs anything, if he's prepared, or wants to discuss the event
- Here are his other upcoming events for context: {all_events}
- Keep responses focused and concise unless he wants to chat more"""
            
            # Combine initial prompt with diary data, calendar events, and optional reminder context
            complete_prompt = f"""{INITIAL_PROMPT}

{diary_section}

{calendar_section}

{reminder_context}"""
            
            return complete_prompt
            
        except Exception as e:
            print(f"Error fetching diary entries or calendar events: {e}")
            # Fallback to static diary content if Firebase fails
            return f"""{INITIAL_PROMPT}

{FALLBACK_DIARY}

Calendar service not available."""
    else:
        # Use generic prompt without personal data
        return INITIAL_PROMPT_GENERIC


async def twilio_handler(twilio_ws, use_personal=True, reminder_event=None):
    audio_queue = asyncio.Queue()
    streamsid_queue = asyncio.Queue()

    async with sts_connect() as sts_ws:
        # Get complete prompt based on endpoint type
        complete_prompt = get_complete_prompt(use_personal, reminder_event=reminder_event)
        
        # For reminder calls, Kayros announces the event in his greeting
        if reminder_event:
            event_name = reminder_event.get("name", "Unknown event")
            event_time = reminder_event.get("time", "Unknown time")
            advance_min = reminder_event.get("advance_minutes", "10")
            greeting = f"Hey Alessandro, Kayros here. Quick reminder: you have {event_name} starting at {event_time} in {advance_min} minutes."
        else:
            greeting = GREETING if use_personal else GREETING_GENERIC
        
        # Configuration with complete prompt from the start
        config_message = {
            "type": "Settings",
            "audio": {
                "input": {
                    "encoding": "mulaw",
                    "sample_rate": 8000,
                },
                "output": {
                    "encoding": "mulaw",
                    "sample_rate": 8000,
                    "container": "none",
                },
            },
            "agent": {
                "speak": {
                    "provider": {"type": "deepgram", "model": "aura-2-odysseus-en"}
                },
                "listen": {"provider": {"type": "deepgram", "model": "nova-3"}},
                "think": {
                    "provider": {"type": "open_ai", "model": "gpt-4o"},
                    "prompt": complete_prompt,
                },
                "greeting": greeting,
            },
        }

        await sts_ws.send(json.dumps(config_message))
        endpoint_type = "personal" if use_personal else "generic"
        print(f"✅ Complete configuration sent for {endpoint_type} endpoint")

        async def sts_sender(sts_ws):
            print("sts_sender started")
            while True:
                chunk = await audio_queue.get()
                await sts_ws.send(chunk)

        async def sts_receiver(sts_ws):
            print("sts_receiver started")
            # we will wait until the twilio ws connection figures out the streamsid
            streamsid = await streamsid_queue.get()
            # for each sts result received, forward it on to the call
            async for message in sts_ws:
                if type(message) is str:
                    print(f"📨 Received message: {message}")
                    # handle barge-in
                    decoded = json.loads(message)
                    if decoded["type"] == "UserStartedSpeaking":
                        clear_message = {"event": "clear", "streamSid": streamsid}
                        await twilio_ws.send(json.dumps(clear_message))
                    
                    continue
 
                print(type(message))
                raw_mulaw = message

                # construct a Twilio media message with the raw mulaw (see https://www.twilio.com/docs/voice/twiml/stream#websocket-messages---to-twilio)
                media_message = {
                    "event": "media",
                    "streamSid": streamsid,
                    "media": {"payload": base64.b64encode(raw_mulaw).decode("ascii")},
                }

                # send the TTS audio to the attached phonecall
                await twilio_ws.send(json.dumps(media_message))

        async def twilio_receiver(twilio_ws):
            print("twilio_receiver started")
            # twilio sends audio data as 160 byte messages containing 20ms of audio each
            # we will buffer 20 twilio messages corresponding to 0.4 seconds of audio to improve throughput performance
            BUFFER_SIZE = 20 * 160

            inbuffer = bytearray(b"")
            async for message in twilio_ws:
                try:
                    data = json.loads(message)
                    if data["event"] == "start":
                        print("got our streamsid")
                        start = data["start"]
                        streamsid = start["streamSid"]
                        streamsid_queue.put_nowait(streamsid)
                        
                    if data["event"] == "connected":
                        continue
                    if data["event"] == "media":
                        media = data["media"]
                        chunk = base64.b64decode(media["payload"])
                        if media["track"] == "inbound":
                            inbuffer.extend(chunk)
                    if data["event"] == "stop":
                        break

                    # check if our buffer is ready to send to our audio_queue (and, thus, then to sts)
                    while len(inbuffer) >= BUFFER_SIZE:
                        chunk = inbuffer[:BUFFER_SIZE]
                        audio_queue.put_nowait(chunk)
                        inbuffer = inbuffer[BUFFER_SIZE:]
                except:
                    break

        # the async for loop will end if the ws connection from twilio dies
        # and if this happens, we should forward an some kind of message to sts
        # to signal sts to send back remaining messages before closing(?)
        # audio_queue.put_nowait(b'')

        await asyncio.wait(
            [
                asyncio.ensure_future(sts_sender(sts_ws)),
                asyncio.ensure_future(sts_receiver(sts_ws)),
                asyncio.ensure_future(twilio_receiver(twilio_ws)),
            ]
        )

        await twilio_ws.close()


async def router(websocket, path):
    print(f"Incoming connection on path: {path}")
    
    # Parse path and query parameters
    if "?" in path:
        base_path, query_string = path.split("?", 1)
    else:
        base_path = path
        query_string = ""
    
    if base_path == "/twilio":
        print("Starting personal Twilio handler")
        await twilio_handler(websocket, use_personal=True)
    elif base_path == "/generic":
        print("Starting generic Twilio handler")
        await twilio_handler(websocket, use_personal=False)
    elif base_path == "/reminder":
        # Parse event information from query parameters
        event_info = {}
        if query_string:
            from urllib.parse import parse_qs
            params = parse_qs(query_string)
            event_info = {
                "name": params.get("event_name", ["Unknown event"])[0],
                "time": params.get("event_time", ["Unknown time"])[0],
                "id": params.get("event_id", [""])[0],
                "advance_minutes": params.get("advance_minutes", ["10"])[0]
            }
        
        print(f"Starting reminder call for event: {event_info.get('name', 'Unknown')} at {event_info.get('time', 'Unknown')}")
        await twilio_handler(websocket, use_personal=True, reminder_event=event_info)
    else:
        print(f"Unknown path: {path}")
        await websocket.close()


def main():
    port = int(os.environ.get("PORT", 5000))  # Render provides PORT
    server = websockets.serve(router, "0.0.0.0", port)
    print(f"Server starting on ws://0.0.0.0:{port}")
    print("Available endpoints:")
    print("  /twilio  - Personal assistant with diary data, calendar events, and email automation")
    print("  /generic - Public assistant promoting Alessandro")
    print("  /reminder - Reminder calls that connect to Kayros AI (used by reminder service)")
    print("Using optimized diary service with aggressive caching")
    print("Diary data pre-loaded for instant access")
    print("Complete prompt sent immediately - no updates needed")
    print(f"Personal limits: {DIARY_DAYS} days, {DIARY_MAX_ENTRIES} entries max, {DIARY_MAX_CHARS} characters max")
    
    # Check if calendar service is available
    calendar_svc = get_calendar_service()
    if calendar_svc:
        status = calendar_svc.get_service_status()
        refresh_info = f"every {status['refresh_interval_minutes']} minutes" if status['refresh_mode'] == 'periodic' else "at midnight"
        print(f"✅ Calendar service initialized - events refreshed {refresh_info}")
        print(f"📅 Calendar status: {status['cached_events_count']} events cached, scheduler running: {status['scheduler_running']}")
    else:
        print("⚠️  Calendar service not available - set GMAIL_PASSWORD environment variable to enable")
    
    # Check if reminder service is available
    reminder_svc = get_reminder_service()
    if reminder_svc:
        status = reminder_svc.get_service_status()
        print("✅ Reminder service initialized - automated calls enabled")
        print(f"📞 Reminder status: calling {status['phone_number']} {status['advance_minutes']} minutes before events")
    else:
        print("⚠️  Reminder service not available - requires calendar service and Twilio credentials")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server)
    loop.run_forever()


if __name__ == "__main__":
    sys.exit(main() or 0)
