"""
Real-Time Agent Tester
Connect to a running server and test the agent in real-time
"""

import asyncio
import json
import websockets
import sys
import os
from typing import Optional


class RealTimeAgentTester:
    """Real-time testing interface that connects to the running server"""
    
    def __init__(self, server_url: str = "ws://localhost:5000/twilio"):
        self.server_url = server_url
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.conversation_history = []
        self.stream_sid = None
    
    async def connect(self):
        """Connect to the server"""
        try:
            print(f"�� Connecting to {self.server_url}...")
            self.websocket = await websockets.connect(self.server_url)
            print("✅ Connected to server successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the server"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 Disconnected from server")
    
    async def send_audio_message(self, text: str):
        """Send a text message as if it were audio (simplified for testing)"""
        if not self.websocket:
            print("❌ Not connected to server")
            return
        
        # For testing, we'll simulate the WebSocket message flow
        # In a real implementation, this would send actual audio data
        
        # Simulate the start message
        start_message = {
            "event": "start",
            "start": {
                "streamSid": "test_stream_123",
                "callSid": "test_call_123",
                "tracks": ["inbound", "outbound"],
                "mediaFormat": {
                    "encoding": "audio/x-mulaw",
                    "sampleRate": 8000,
                    "channels": 1
                }
            }
        }
        
        if not self.stream_sid:
            await self.websocket.send(json.dumps(start_message))
            self.stream_sid = "test_stream_123"
            print(f"📡 Stream started with SID: {self.stream_sid}")
        
        # Simulate media message (in real implementation, this would be audio data)
        # For testing, we'll just send a text representation
        media_message = {
            "event": "media",
            "streamSid": self.stream_sid,
            "media": {
                "track": "inbound",
                "chunk": "1",
                "timestamp": "1234567890",
                "payload": "dGVzdCBhdWRpbyBkYXRh"  # Base64 encoded "test audio data"
            }
        }
        
        await self.websocket.send(json.dumps(media_message))
        print(f"📤 Sent message: {text}")
    
    async def listen_for_responses(self):
        """Listen for responses from the server"""
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.handle_server_message(data)
                except json.JSONDecodeError:
                    print(f"📨 Received non-JSON message: {message}")
                except Exception as e:
                    print(f"❌ Error handling message: {e}")
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection closed by server")
        except Exception as e:
            print(f"❌ Error listening for responses: {e}")
    
    async def handle_server_message(self, data: dict):
        """Handle messages from the server"""
        event_type = data.get("event", "unknown")
        
        if event_type == "media":
            # This would be audio data from the agent
            print("🔊 Received audio response from agent")
        elif event_type == "clear":
            print("🧹 Agent cleared audio (barge-in)")
        else:
            print(f"📨 Server message: {data}")
    
    async def run_interactive_session(self):
        """Run an interactive testing session"""
        print("🚀 Real-Time Agent Tester")
        print("="*50)
        print("This tool connects to your running server to test the agent.")
        print("Make sure your server is running on the specified URL.")
        print("Type 'help' for commands, 'quit' to exit.")
        print()
        
        # Connect to server
        if not await self.connect():
            return
        
        print("✅ Ready to test! Type your messages below.")
        print()
        
        # Start listening for responses in the background
        listen_task = asyncio.create_task(self.listen_for_responses())
        
        try:
            while True:
                # Get user input
                user_input = input("👤 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'help':
                    self.print_help()
                    continue
                elif user_input.lower() == 'status':
                    await self.print_status()
                    continue
                
                # Send message to server
                await self.send_audio_message(user_input)
                
                # Store in conversation history
                self.conversation_history.append({
                    "user_input": user_input,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
        finally:
            # Clean up
            listen_task.cancel()
            await self.disconnect()
    
    def print_help(self):
        """Print help information"""
        print("\n📖 HELP - Available Commands:")
        print("-" * 40)
        print("help          - Show this help message")
        print("status        - Show connection status")
        print("quit/exit/q   - Exit the tester")
        print()
        print("📧 Email Testing Examples:")
        print("-" * 40)
        print("'send email'           - Send a normal email")
        print("'send test email'      - Send a test email")
        print("'hello'                - Test greeting")
        print("'diary' or 'logs'      - Test diary integration")
        print()
    
    async def print_status(self):
        """Print connection status"""
        print(f"\n📊 STATUS:")
        print(f"Server URL: {self.server_url}")
        print(f"Connected: {'✅ Yes' if self.websocket else '❌ No'}")
        print(f"Stream SID: {self.stream_sid or 'Not set'}")
        print(f"Messages sent: {len(self.conversation_history)}")
        print()


class MockAgentTester:
    """Mock agent tester for when server is not available"""
    
    def __init__(self):
        self.conversation_history = []
    
    async def run_interactive_session(self):
        """Run a mock interactive session"""
        print("🚀 Mock Agent Tester (Server Not Available)")
        print("="*50)
        print("This is a mock version for testing when the server is not running.")
        print("It simulates agent responses to test the email automation logic.")
        print()
        
        from services.email_automation_service import EmailAutomationService
        email_automation = EmailAutomationService()
        
        while True:
            try:
                user_input = input("👤 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'help':
                    self.print_help()
                    continue
                
                # Simulate agent response
                agent_response = self.simulate_agent_response(user_input)
                print(f"\n🤖 Agent: {agent_response}")
                
                # Process email automation
                has_email, injection_prompt, email_request = await email_automation.process_agent_response(agent_response)
                
                if has_email:
                    if email_request:
                        print(f"📧 Sending email to: {email_request.to}")
                        success, message = await email_automation.send_email(email_request)
                        if success:
                            print(f"✅ Email sent successfully: {message}")
                        else:
                            print(f"❌ Email sending failed: {message}")
                    else:
                        print(f"❌ Invalid email request: {injection_prompt}")
                
                self.conversation_history.append({
                    "user_input": user_input,
                    "agent_response": agent_response,
                    "has_email": has_email
                })
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def simulate_agent_response(self, user_input: str) -> str:
        """Simulate agent response"""
        user_lower = user_input.lower()
        
        if "send email" in user_lower:
            if "test" in user_lower:
                return 'I will send a test email. {"to": "axm2022@case.edu", "subject": "Test Email", "message": "This is a test email from the mock tester."}'
            else:
                return 'I will send an email for you. {"to": "axm2022@case.edu", "subject": "Email from Mock Agent", "message": "This email was sent through the mock testing interface."}'
        elif "hello" in user_lower:
            return "Hi Alessandro! Kayros here. How can I help you today?"
        else:
            return f"I understand you said: '{user_input}'. How can I assist you?"
    
    def print_help(self):
        """Print help information"""
        print("\n📖 HELP - Mock Agent Tester:")
        print("-" * 40)
        print("This is a mock version that simulates agent responses.")
        print("Type 'send email' to test email automation.")
        print("Type 'quit' to exit.")
        print()


async def main():
    """Main function"""
    print("🔧 Initializing Agent Tester...")
    
    # Try to connect to real server first
    server_url = "ws://localhost:5000/twilio"
    tester = RealTimeAgentTester(server_url)
    
    try:
        if await tester.connect():
            await tester.run_interactive_session()
        else:
            print("\n🔄 Server not available, switching to mock mode...")
            mock_tester = MockAgentTester()
            await mock_tester.run_interactive_session()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
