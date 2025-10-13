"""
Test script for email automation system
Run this locally to test the email automation functionality
"""

import asyncio
import json
import sys
import os
from services.email_automation_service import EmailAutomationService


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.messages = []
    
    async def send(self, message):
        self.messages.append(message)
        print(f"📤 Sent: {message}")
    
    def get_messages(self):
        return self.messages


class MockSTSWebSocket:
    """Mock STS WebSocket for testing"""
    def __init__(self):
        self.messages = []
    
    async def send(self, message):
        self.messages.append(message)
        print(f"📤 STS Sent: {message}")
    
    def get_messages(self):
        return self.messages


async def test_email_automation_flow():
    """Test the complete email automation flow"""
    print("🧪 Testing Email Automation System")
    print("=" * 50)
    
    # Initialize services
    email_service = EmailAutomationService()
    mock_twilio_ws = MockWebSocket()
    mock_sts_ws = MockSTSWebSocket()
    
    # Test cases
    test_cases = [
        {
            "name": "Valid Email Request",
            "response": 'I will send an email for you. {"to": "axm2022@case.edu", "subject": "Test Email", "message": "This is a test message from the automation system."}',
            "expected_valid": True
        },
        {
            "name": "Invalid JSON Format",
            "response": 'I will send an email. {"to": "test@example.com", "subject": "Test", "message": "Hello"',  # Missing closing brace
            "expected_valid": False
        },
        {
            "name": "Missing Required Field",
            "response": 'Here is the email request: {"to": "test@example.com", "subject": "Test"}',  # Missing message
            "expected_valid": False
        },
        {
            "name": "Alternative Field Names",
            "response": 'Email request: {"recipient": "axm2022@case.edu", "title": "Alternative Fields", "body": "Using different field names"}',
            "expected_valid": True
        },
        {
            "name": "No Email Request",
            "response": "Just a regular conversation without any email request.",
            "expected_valid": False
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print(f"Response: {test_case['response']}")
        print("-" * 30)
        
        # Process the response
        has_email, injection_prompt, email_request = await email_service.process_agent_response(test_case['response'])
        
        if has_email:
            if email_request:
                print("✅ Valid email request detected")
                print(f"   To: {email_request.to}")
                print(f"   Subject: {email_request.subject}")
                print(f"   Message: {email_request.message}")
                
                # Simulate sending email
                success, message = await email_service.send_email(email_request)
                print(f"   Email sending: {'✅ Success' if success else '❌ Failed'}")
                print(f"   Message: {message}")
                
                if success:
                    # Create confirmation prompt
                    confirmation = email_service.create_success_confirmation_prompt(email_request)
                    print(f"   Confirmation prompt: {confirmation}")
                    
                    # Simulate injecting confirmation back to agent
                    inject_message = {
                        "type": "InjectUserMessage",
                        "content": confirmation
                    }
                    await mock_sts_ws.send(json.dumps(inject_message))
                
            else:
                print("❌ Invalid email request - needs correction")
                print(f"   Error prompt: {injection_prompt}")
                
                # Simulate injecting correction prompt
                inject_message = {
                    "type": "InjectUserMessage",
                    "content": injection_prompt
                }
                await mock_sts_ws.send(json.dumps(inject_message))
        else:
            print("ℹ️  No email request detected")
        
        print()
    
    print("📊 Test Summary")
    print("=" * 50)
    print(f"Total tests: {len(test_cases)}")
    print(f"STS messages sent: {len(mock_sts_ws.get_messages())}")
    print(f"Twilio messages sent: {len(mock_twilio_ws.get_messages())}")


async def test_manual_email_sending():
    """Test manual email sending"""
    print("\n🔧 Manual Email Sending Test")
    print("=" * 50)
    
    email_service = EmailAutomationService()
    
    # Test with your actual email
    test_email = {
        "to": "axm2022@case.edu",
        "subject": "Test from Automation System",
        "message": "This is a test email sent from the local automation system. If you receive this, the system is working correctly! 🎉"
    }
    
    print(f"Sending test email to: {test_email['to']}")
    print(f"Subject: {test_email['subject']}")
    print(f"Message: {test_email['message']}")
    
    # Validate first
    is_valid, email_request, error = email_service.validate_email_json(json.dumps(test_email))
    
    if is_valid:
        print("✅ Email request is valid")
        success, message = await email_service.send_email(email_request)
        print(f"📧 Email sending result: {'✅ Success' if success else '❌ Failed'}")
        print(f"📝 Message: {message}")
    else:
        print(f"❌ Email request is invalid: {error}")


def print_usage():
    """Print usage instructions"""
    print("""
🚀 Email Automation Test Script

Usage:
    python test_email_automation.py [test_type]

Test Types:
    flow     - Test the complete email automation flow (default)
    manual   - Test manual email sending
    all      - Run all tests

Examples:
    python test_email_automation.py flow
    python test_email_automation.py manual
    python test_email_automation.py all
    """)


async def main():
    """Main test function"""
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
    else:
        test_type = "flow"
    
    if test_type == "flow":
        await test_email_automation_flow()
    elif test_type == "manual":
        await test_manual_email_sending()
    elif test_type == "all":
        await test_email_automation_flow()
        await test_manual_email_sending()
    else:
        print_usage()
        return
    
    print("\n✅ Testing completed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
