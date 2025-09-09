import asyncio
import base64
import json
import sys
import websockets
import ssl
import os
from services.optimized_diary_service import OptimizedDiaryService
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
email_service = None

def get_diary_service():
    """
    Get or create the global diary service instance
    """
    global diary_service
    if diary_service is None:
        diary_service = OptimizedDiaryService()
    return diary_service

""" def get_email_service():
   
    global email_service
    if email_service is None:
        try:
            email_service = EmailService()
        except ValueError as e:
            print(f"⚠️  Email service not available: {e}")
            email_service = None
    return email_service """

def sts_connect():
    # you can run export DEEPGRAM_API_KEY="your key" in your terminal to set your API key.
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY environment variable is not set")

    sts_ws = websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse", subprotocols=["token", api_key]
    )
    return sts_ws


def get_complete_prompt(use_personal=True):
    """
    Get the complete prompt with diary data included immediately
    
    Args:
        use_personal: If True, use personal prompt with diary data. If False, use generic prompt.
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
            
            # Combine initial prompt with diary data
            complete_prompt = f"""{INITIAL_PROMPT}

{diary_section}"""
            
            return complete_prompt
            
        except Exception as e:
            print(f"Error fetching diary entries: {e}")
            # Fallback to static diary content if Firebase fails
            return f"""{INITIAL_PROMPT}

{FALLBACK_DIARY}"""
    else:
        # Use generic prompt without personal data
        return INITIAL_PROMPT_GENERIC


async def twilio_handler(twilio_ws, use_personal=True):
    audio_queue = asyncio.Queue()
    streamsid_queue = asyncio.Queue()

    async with sts_connect() as sts_ws:
        # Get complete prompt based on endpoint type
        complete_prompt = get_complete_prompt(use_personal)
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
                    "provider": {"type": "open_ai", "model": "gpt-4.1"},
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
                    
                    # Check for agent responses and trigger email if needed (only for personal endpoint)
                    if use_personal and decoded.get("type") == "AgentResponse":
                        agent_text = decoded.get("text", "")
                        if agent_text:
                            print(f"🤖 Agent response: {agent_text}")
                            # Check if email service is available and trigger email
                            """ email_svc = get_email_service()
                            if email_svc:
                                email_svc.check_and_trigger_email(agent_text) """
                    
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
    if path == "/twilio":
        print("Starting personal Twilio handler")
        await twilio_handler(websocket, use_personal=True)
    elif path == "/generic":
        print("Starting generic Twilio handler")
        await twilio_handler(websocket, use_personal=False)
    else:
        print(f"Unknown path: {path}")
        await websocket.close()


def main():
    port = int(os.environ.get("PORT", 5000))  # Render provides PORT
    server = websockets.serve(router, "0.0.0.0", port)
    print(f"Server starting on ws://0.0.0.0:{port}")
    print("Available endpoints:")
    print("  /twilio  - Personal assistant with diary data")
    print("  /generic - Public assistant promoting Alessandro")
    print("Using optimized diary service with aggressive caching")
    print("Diary data pre-loaded for instant access")
    print("Complete prompt sent immediately - no updates needed")
    print(f"Personal limits: {DIARY_DAYS} days, {DIARY_MAX_ENTRIES} entries max, {DIARY_MAX_CHARS} characters max")
    
    # Check if email service is available
    """ email_svc = get_email_service()
    if email_svc:
        print("✅ Email service initialized - will trigger emails when agent replies contain 'email' (personal endpoint only)")
    else:
        print("⚠️  Email service not available - set GMAIL_PASSWORD environment variable to enable")
     """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server)
    loop.run_forever()


if __name__ == "__main__":
    sys.exit(main() or 0)
