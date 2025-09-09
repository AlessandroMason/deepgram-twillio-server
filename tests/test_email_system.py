#!/usr/bin/env python3
"""
Test script for the email system with contact list
"""

import os
import sys
sys.path.append('.')

from ..services.email_service import EmailService
from ..agents.constants import CONTACTS

def test_email_system():
    """Test the email system with contact list"""
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize the service
        service = EmailService()
        
        print("🧪 Testing Email System with Contact List")
        print("=" * 50)
        
        # Test 1: Contact lookup
        print("\n📞 Testing Contact Lookup:")
        for name in ["alessandro", "john", "jane", "unknown"]:
            email = service.find_contact_email(name)
            if email:
                print(f"  ✅ {name} -> {email}")
            else:
                print(f"  ❌ {name} -> Not found")
        
        # Test 2: Voice command parsing
        print("\n🎤 Testing Voice Command Parsing:")
        test_commands = [
            "send email to alessandro about the project update",
            "email john regarding the meeting tomorrow",
            "compose email to jane about the budget proposal"
        ]
        
        for command in test_commands:
            recipient, description = service._extract_email_info(command)
            print(f"  Command: '{command}'")
            print(f"    Recipient: {recipient}")
            print(f"    Description: {description}")
            print()
        
        # Test 3: Send a test email
        print("📧 Testing Email Sending:")
        test_message = "send an email to alessandro about testing the new contact system"
        context = "Testing the updated email service with contact list integration"
        
        result = service.process_email_request(test_message, context, send_email=True)
        
        if result["success"]:
            print("✅ Email sent successfully!")
            print(f"📧 Subject: {result['subject']}")
            print(f"📝 Preview: {result['preview']}")
        else:
            print(f"❌ Error: {result['error']}")
            print(f"💬 Message: {result['message']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email_system()
