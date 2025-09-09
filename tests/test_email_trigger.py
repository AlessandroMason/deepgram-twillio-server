#!/usr/bin/env python3
"""
Test script for email trigger functionality
"""
import os
from ..services.email_service import EmailService

def test_email_service():
    """Test the email service with environment variables"""
    print("🧪 Testing Email Service with Environment Variables")
    print("=" * 60)
    
    # Check if required environment variables are set
    openai_key = os.getenv("OPENAI_API_KEY")
    gmail_password = os.getenv("GMAIL_PASSWORD")
    
    print(f"OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Not set'}")
    print(f"GMAIL_PASSWORD: {'✅ Set' if gmail_password else '❌ Not set'}")
    
    if not openai_key:
        print("\n❌ Please set OPENAI_API_KEY environment variable")
        return False
    
    if not gmail_password:
        print("\n❌ Please set GMAIL_PASSWORD environment variable")
        return False
    
    try:
        # Initialize email service
        print("\n🔄 Initializing EmailService...")
        service = EmailService()
        print("✅ EmailService initialized successfully")
        
        # Test the trigger functionality
        print("\n🔄 Testing email trigger functionality...")
        
        # Test case 1: Reply with "email" should trigger
        test_reply_1 = "I can help you with that email request"
        print(f"Test 1 - Reply: '{test_reply_1}'")
        result_1 = service.check_and_trigger_email(test_reply_1)
        print(f"Result: {'✅ Email sent' if result_1 else '❌ No email sent'}")
        
        # Test case 2: Reply without "email" should not trigger
        test_reply_2 = "I can help you with that request"
        print(f"\nTest 2 - Reply: '{test_reply_2}'")
        result_2 = service.check_and_trigger_email(test_reply_2)
        print(f"Result: {'✅ Email sent' if result_2 else '❌ No email sent (expected)'}")
        
        print("\n✅ Email trigger functionality test completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing email service: {e}")
        return False

if __name__ == "__main__":
    test_email_service()
