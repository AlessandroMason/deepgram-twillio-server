import asyncio
import base64
import json
import sys
import websockets
import ssl
import os


def sts_connect():
    # you can run export DEEPGRAM_API_KEY="your key" in your terminal to set your API key.
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY environment variable is not set")

    sts_ws = websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse", subprotocols=["token", api_key]
    )
    return sts_ws


async def twilio_handler(twilio_ws):
    audio_queue = asyncio.Queue()
    streamsid_queue = asyncio.Queue()

    async with sts_connect() as sts_ws:
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
                    "prompt": "#Role\nYou are a general-purpose virtual assistant speaking to users over the phone. Your task is to help them find accurate, helpful information across a wide range of everyday topics.\n\n#General Guidelines\n-Be warm, friendly, and professional.\n-Speak clearly and naturally in plain language.\n-Keep most responses to 1–2 sentences and under 120 characters unless the caller asks for more detail (max: 300 characters).\n-Do not use markdown formatting, like code blocks, quotes, bold, links, or italics.\n-Use line breaks in lists.\n-Use varied phrasing; avoid repetition.\n-If unclear, ask for clarification.\n-If the user’s message is empty, respond with an empty message.\n-If asked about your well-being, respond briefly and kindly.\n\n#Voice-Specific Instructions\n-Speak in a conversational tone—your responses will be spoken aloud.\n-Pause after questions to allow for replies.\n-Confirm what the customer said if uncertain.\n-Never interrupt.\n\n#Style\n-Use active listening cues.\n-Be warm and understanding, but concise.\n-Use simple words unless the caller uses technical terms.\n\n#Call Flow Objective\n-Greet the caller and introduce yourself:\n“Hi there, I’m your virtual assistant—how can I help today?”\n-Your primary goal is to help users quickly find the information they’re looking for. This may include:\nQuick facts: “The capital of Japan is Tokyo.”\nWeather: “It’s currently 68 degrees and cloudy in Seattle.”\nLocal info: “There’s a pharmacy nearby open until 9 PM.”\nBasic how-to guidance: “To restart your phone, hold the power button for 5 seconds.”\nFAQs: “Most returns are accepted within 30 days with a receipt.”\nNavigation help: “Can you tell me the address or place you’re trying to reach?”\n-If the request is unclear:\n“Just to confirm, did you mean…?” or “Can you tell me a bit more?”\n-If the request is out of scope (e.g. legal, financial, or medical advice):\n“I’m not able to provide advice on that, but I can help you find someone who can.”\n\n#Off-Scope Questions\n-If asked about sensitive topics like health, legal, or financial matters:\n“I’m not qualified to answer that, but I recommend reaching out to a licensed professional.”\n\n#User Considerations\n-Callers may be in a rush, distracted, or unsure how to phrase their question. Stay calm, helpful, and clear—especially when the user seems stressed, confused, or overwhelmed.\n\n#Closing\n-Always ask:\n“Is there anything else I can help you with today?”\n-Then thank them warmly and say:\n“Thanks for calling. Take care and have a great day!”\n",
                },
                "greeting": "Hello! How may I help you?",
            },
        }

        await sts_ws.send(json.dumps(config_message))

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
                    print(message)
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
    if path == "/twilio":
        print("Starting Twilio handler")
        await twilio_handler(websocket)


def main():
    port = int(os.environ.get("PORT", 5000))  # Render provides PORT
    server = websockets.serve(router, "0.0.0.0", port)
    print(f"Server starting on ws://0.0.0.0:{port}")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server)
    loop.run_forever()


if __name__ == "__main__":
    sys.exit(main() or 0)
