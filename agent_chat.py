"""
Agent Chat Interface
Simple command-line interface to chat with your agent and test email automation
"""

import asyncio
import json
import sys
import os
from services.email_automation_service import EmailAutomationService
from services.optimized_diary_service import OptimizedDiaryService
from services.calendar_service import GoogleCalendarService
from agents.constants import (
    INITIAL_PROMPT, 
    GREETING, 
    USER_ID, 
    DIARY_DAYS, 
    DIARY_MAX_ENTRIES, 
    DIARY_MAX_CHARS,
    FALLBACK_DIARY
)


class AgentChat:
    """Simple chat interface for testing the agent"""
    
    def __init__(self):
        self.email_automation = EmailAutomationService()
        self.diary_service = OptimizedDiaryService()
        self.calendar_service = None
        self.chat_history = []
        
        # Initialize calendar service if available
        try:
            self.calendar_service = GoogleCalendarService()
            print("✅ Calendar service initialized")
        except Exception as e:
            print(f"⚠️  Calendar service not available: {e}")
    
    def get_agent_context(self):
        """Get agent context information"""
        try:
            # Get diary data
            diary_section = self.diary_service.get_diary_prompt_section(
                USER_ID, 
                days=DIARY_DAYS, 
                max_entries=DIARY_MAX_ENTRIES, 
                max_chars=DIARY_MAX_CHARS
            )
            
            # Get calendar events
            calendar_section = ""
            if self.calendar_service:
                calendar_section = self.calendar_service.get_events_for_agent()
            else:
                calendar_section = "Calendar service not available."
            
            return {
                "diary": diary_section,
                "calendar": calendar_section,
                "greeting": GREETING
            }
        except Exception as e:
            print(f"Error getting agent context: {e}")
            return {
                "diary": FALLBACK_DIARY,
                "calendar": "Calendar service not available.",
                "greeting": GREETING
            }
    
    def simulate_agent_response(self, user_input: str) -> str:
        """Simulate agent response based on user input and context"""
        user_lower = user_input.lower()
        context = self.get_agent_context()
        
        # Email automation responses
        if "send email" in user_lower or "email" in user_lower:
            if "test" in user_lower:
                return 'I will send a test email for you. {"to": "axm2022@case.edu", "subject": "Test Email from Chat Interface", "message": "This is a test email sent from the agent chat interface. The system is working correctly!"}'
            elif "invalid" in user_lower:
                return 'I will send an email. {"to": "test@example.com", "subject": "Test", "message": "Hello"'  # Missing closing brace
            elif "missing" in user_lower:
                return 'Here is the email request: {"to": "test@example.com", "subject": "Test"}'  # Missing message
            elif "alternative" in user_lower:
                return 'Email request: {"recipient": "axm2022@case.edu", "title": "Alternative Fields Test", "body": "Testing alternative field names in the email automation system."}'
            else:
                return 'I will send an email for you. {"to": "axm2022@case.edu", "subject": "Email from Agent Chat", "message": "This email was sent through the agent chat interface."}'
        
        # Greeting responses
        elif "hello" in user_lower or "hi" in user_lower:
            return f"{context['greeting']} How can I help you today?"
        
        # Diary/logs responses
        elif "diary" in user_lower or "logs" in user_lower:
            return "I can see your recent diary entries. You've been working on your projects and maintaining your routine. Is there anything specific you'd like to discuss about your recent activities?"
        
        # Calendar responses
        elif "calendar" in user_lower:
            return "I can see your upcoming calendar events. You have some meetings and classes scheduled. Would you like me to help you prepare for any of them?"
        
        # Help responses
        elif "help" in user_lower:
            return """I can help you with:
- Sending emails (just say 'send email')
- Discussing your diary entries (say 'diary' or 'logs')
- Checking your calendar (say 'calendar')
- General conversation

Try saying 'send test email' to test the email automation!"""
        
        # Default response
        else:
            return f"I understand you said: '{user_input}'. How can I assist you further? You can ask me to send emails, discuss your diary, or check your calendar."
    
    async def process_agent_response(self, agent_text: str) -> dict:
        """Process agent response and handle email automation"""
        print(f"\n🤖 Agent: {agent_text}")
        
        # Process email automation
        has_email, injection_prompt, email_request = await self.email_automation.process_agent_response(agent_text)
        
        result = {
            "has_email": has_email,
            "agent_text": agent_text,
            "injection_prompt": injection_prompt,
            "email_request": email_request,
            "email_sent": False,
            "email_success": False,
            "email_message": ""
        }
        
        if has_email:
            if email_request:
                # Valid email request - send the email
                print(f"\n📧 Sending email to: {email_request.to}")
                print(f"   Subject: {email_request.subject}")
                print(f"   Message: {email_request.message}")
                
                success, message = await self.email_automation.send_email(email_request)
                result["email_sent"] = True
                result["email_success"] = success
                result["email_message"] = message
                
                if success:
                    print(f"✅ Email sent successfully: {message}")
                    # Show what agent would receive
                    confirmation = self.email_automation.create_success_confirmation_prompt(email_request)
                    print(f"\n📤 Agent would receive confirmation:")
                    print(f"   {confirmation}")
                else:
                    print(f"❌ Email sending failed: {message}")
                    error_message = f"Email sending failed: {message}. Please try again."
                    print(f"\n📤 Agent would receive error:")
                    print(f"   {error_message}")
            else:
                # Invalid email request - show correction prompt
                print(f"\n❌ Invalid email request detected")
                print(f"📤 Agent would receive correction prompt:")
                print(f"   {injection_prompt}")
                result["injection_prompt"] = injection_prompt
        
        return result
    
    def print_welcome(self):
        """Print welcome message"""
        print("🚀 Agent Chat Interface")
        print("=" * 50)
        print("Chat with your agent and test email automation!")
        print("Type 'help' for commands, 'quit' to exit.")
        print()
        
        # Show system status
        context = self.get_agent_context()
        print("📊 System Status:")
        print(f"   📧 Email automation: ✅ Ready")
        print(f"   📅 Calendar service: {'✅ Available' if self.calendar_service else '❌ Not available'}")
        print(f"   📝 Diary data: ✅ Loaded")
        print(f"   👋 Greeting: {context['greeting']}")
        print()
    
    def print_help(self):
        """Print help information"""
        print("\n📖 HELP - Available Commands:")
        print("-" * 40)
        print("help                    - Show this help message")
        print("quit/exit/q            - Exit the chat")
        print("status                 - Show system status")
        print("history                - Show chat history")
        print("clear                  - Clear chat history")
        print()
        print("📧 Email Testing Examples:")
        print("-" * 40)
        print("'send email'           - Send a normal email")
        print("'send test email'      - Send a test email")
        print("'send invalid email'   - Test invalid JSON handling")
        print("'send missing email'   - Test missing field handling")
        print("'send alternative email' - Test alternative field names")
        print()
        print("💬 General Testing:")
        print("-" * 40)
        print("'hello'                - Test greeting")
        print("'diary' or 'logs'      - Test diary integration")
        print("'calendar'             - Test calendar integration")
        print("'help'                 - Test help response")
        print()
    
    def print_status(self):
        """Print system status"""
        context = self.get_agent_context()
        print(f"\n📊 SYSTEM STATUS:")
        print(f"Email automation: ✅ Ready")
        print(f"Calendar service: {'✅ Available' if self.calendar_service else '❌ Not available'}")
        print(f"Diary entries: ✅ Loaded ({len(context['diary'])} chars)")
        print(f"Chat history: {len(self.chat_history)} messages")
        print(f"Greeting: {context['greeting']}")
        print()
    
    def print_history(self):
        """Print chat history"""
        if not self.chat_history:
            print("\n📝 No chat history yet.")
            return
        
        print(f"\n📝 CHAT HISTORY ({len(self.chat_history)} messages):")
        print("-" * 50)
        for i, entry in enumerate(self.chat_history, 1):
            status = "✅" if entry.get("email_success") else "❌" if entry.get("has_email") else "💬"
            print(f"{i}. {status} You: {entry['user_input']}")
            if entry.get("has_email"):
                print(f"   📧 Email: {'Sent' if entry.get('email_success') else 'Failed'}")
        print()
    
    async def run_chat(self):
        """Run the chat interface"""
        self.print_welcome()
        
        while True:
            try:
                # Get user input
                user_input = input("👤 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    self.print_help()
                    continue
                elif user_input.lower() == 'status':
                    self.print_status()
                    continue
                elif user_input.lower() == 'history':
                    self.print_history()
                    continue
                elif user_input.lower() == 'clear':
                    self.chat_history.clear()
                    print("🗑️  Chat history cleared")
                    continue
                
                # Simulate agent response
                agent_response = self.simulate_agent_response(user_input)
                
                # Process the response
                result = await self.process_agent_response(agent_response)
                result["user_input"] = user_input
                
                # Store in chat history
                self.chat_history.append(result)
                
                # Show summary
                if result['has_email']:
                    status = "✅ Sent" if result['email_success'] else "❌ Failed"
                    print(f"\n📊 Email automation: {status}")
                else:
                    print(f"\n💬 Regular conversation")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue


async def main():
    """Main function"""
    print("🔧 Initializing Agent Chat...")
    
    try:
        chat = AgentChat()
        await chat.run_chat()
    except Exception as e:
        print(f"❌ Failed to initialize chat: {e}")
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
