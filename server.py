import asyncio
import base64
import json
import sys
import websockets
import ssl
import os
from services.optimized_diary_service import OptimizedDiaryService

# Global service instance for caching across requests
diary_service = None

def get_diary_service():
    """
    Get or create the global diary service instance
    """
    global diary_service
    if diary_service is None:
        diary_service = OptimizedDiaryService()
    return diary_service

def sts_connect():
    # you can run export DEEPGRAM_API_KEY="your key" in your terminal to set your API key.
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY environment variable is not set")

    sts_ws = websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse", subprotocols=["token", api_key]
    )
    return sts_ws


def get_diary_prompt_section():
    """
    Get diary entries from Firebase and format them for the prompt
    """
    try:
        # User ID from the path provided
        user_id = "qkr7puLMnfOvZP5T967rJNyqOsv1"
        
        # Get the optimized service
        service = get_diary_service()
        
        # Get formatted diary entries (with caching and decryption)
        diary_section = service.get_diary_prompt_section(user_id, days=7)
        
        return diary_section
        
    except Exception as e:
        print(f"Error fetching diary entries: {e}")
        # Fallback to static diary content if Firebase fails
        return """12:45 - Reflecting [15 min]
writing a lit of the diary. Still debating if keeping it private or making it public, while i
write there is a difference vibe absed on if its going to get shown or not whatever i
should sleep a little now.
Also since this morning (at the start of the run) my right ball hurts, but i think it might
have to do with me practicing my kicking skills on the tree and having fucked up some
muscle or tendon in that area, not sure but since there is a clear trauma ill not worry
about it.
also looking at what i have done one year ago and send screens to BJ and Jasper about
the night. its cool to stay in touch that way.
13:00 - Sleep [15 min]
good nap, i found a place where i can actually nap on a table, its outside the view form
the door so they dont see me, but still see my laptop and stuff so will not come in.
great place to nap and recharge before the next leetcode streak. (that i start now i
guess)
14:00 - leetcode [1 h]
leetcoding session, finally solved a couple of medium problmes withouth help form
chat in a straightforeward manner, were both matrix problems and the ML practice i
have done this morning really helped, found a window problem and losing focus. ill
nap for 15 min and be back on the grind for a final 45 min then do my resume for
Saab, apply to interships, idk other work that feels lighter"""


async def twilio_handler(twilio_ws):
    audio_queue = asyncio.Queue()
    streamsid_queue = asyncio.Queue()
    prompt_updated = False

    async with sts_connect() as sts_ws:
        # Initial configuration without diary data
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
                    "prompt": """you are a friend and mentor in a phonecall with Alessandro, be masculine. direct. use coaching techniques to guide him but also bring up topics if you want and if you retain necessary. I will provide you with his diary entries shortly.""",
                },
                "greeting": "Hello! How may I help you?",
            },
        }

        await sts_ws.send(json.dumps(config_message))
        print("✅ Initial configuration sent")

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
                    
                    # Handle PromptUpdated response
                    if decoded["type"] == "PromptUpdated":
                        print("✅ Prompt updated successfully!")
                        prompt_updated = True

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
                        
                        # Start loading diary data in background
                        print("🔄 Starting background diary data loading...")
                        asyncio.create_task(load_and_update_prompt(sts_ws))
                        
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

        async def load_and_update_prompt(sts_ws):
            """
            Load diary data and update prompt in background
            """
            try:
                print("🔄 Loading diary data...")
                diary_content = get_diary_prompt_section()
                
                # Create the updated prompt
                updated_prompt = f"""you are a friend and mentor in a phonecall with Alessandro, be masculine. direct. use coaching techniques to guide him but also bring up topics if you want and if you retain necessary. I attach some of his diary so you know him better

{diary_content}"""
                
                # Send UpdatePrompt message
                update_message = {
                    "type": "UpdatePrompt",
                    "prompt": updated_prompt
                }
                
                print("📤 Sending UpdatePrompt message...")
                await sts_ws.send(json.dumps(update_message))
                print("✅ UpdatePrompt message sent")
                
            except Exception as e:
                print(f"❌ Error loading diary data: {e}")

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
        print("Starting Twilio handler")
        await twilio_handler(websocket)


def main():
    port = int(os.environ.get("PORT", 5000))  # Render provides PORT
    server = websockets.serve(router, "0.0.0.0", port)
    print(f"Server starting on ws://0.0.0.0:{port}")
    print("Using optimized diary service with caching and decryption")
    print("Diary data will be loaded in background and injected via UpdatePrompt")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server)
    loop.run_forever()


if __name__ == "__main__":
    sys.exit(main() or 0)
