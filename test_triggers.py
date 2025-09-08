#!/usr/bin/env python3
"""
Test script to show all email triggers and patterns
"""

import re
from services.email_service import EmailService
from constants import CONTACTS

def test_all_triggers():
    """Test all possible email trigger patterns"""
    
    print("🎤 EMAIL TRIGGER PATTERNS")
    print("=" * 60)
    
    # Initialize service
    service = EmailService()
    
    # Test patterns from deepgram_email_handler.py
    deepgram_patterns = [
        r'send.*email.*to\s+(\w+).*about\s+(.+)',
        r'email\s+(\w+).*regarding\s+(.+)',
        r'send.*to\s+(\w+).*about\s+(.+)',
        r'write.*email.*to\s+(\w+).*concerning\s+(.+)',
        r'draft.*email.*to\s+(\w+).*regarding\s+(.+)',
        r'send.*(\w+).*an\s+email.*about\s+(.+)',
        r'email\s+(\w+).*about\s+(.+)',
        r'send.*email.*to\s+(\w+).*regarding\s+(.+)',
        r'compose.*email.*to\s+(\w+).*about\s+(.+)'
    ]
    
    # Test patterns from email_service.py
    email_service_patterns = [
        r'send.*email.*to\s+(\w+)',
        r'email.*to\s+(\w+)',
        r'send.*to\s+(\w+)',
        r'email\s+(\w+)'
    ]
    
    # Test voice commands
    test_commands = [
        # Deepgram patterns
        "send email to alessandro about the project update",
        "email john regarding the meeting tomorrow", 
        "send to jane about the budget proposal",
        "write email to bob concerning the client feedback",
        "draft email to sarah regarding the presentation",
        "send mike an email about the deadline",
        "email alessandro about the code review",
        "send email to john regarding the status update",
        "compose email to jane about the new feature",
        
        # Email service patterns
        "send an email to alessandro",
        "email to john",
        "send to jane",
        "email bob",
        
        # With direct email addresses
        "send email to axm2022@case.edu about testing",
        "email john.doe@example.com regarding the meeting",
        
        # Edge cases
        "hey send an email to alessandro about the project",
        "can you email john about the meeting",
        "please send to jane regarding the budget",
        "I need to email bob about the client"
    ]
    
    print("\n📋 TESTING VOICE COMMANDS:")
    print("-" * 40)
    
    for i, command in enumerate(test_commands, 1):
        print(f"\n{i:2d}. Command: '{command}'")
        
        # Test with email service
        recipient, description = service._extract_email_info(command)
        
        if recipient:
            print(f"    ✅ Recipient: {recipient}")
            print(f"    📝 Description: {description}")
            
            # Check if it's a contact name or direct email
            if '@' in recipient:
                print(f"    📧 Direct email address")
            else:
                contact_email = service.find_contact_email(recipient)
                if contact_email:
                    print(f"    👤 Contact: {recipient} -> {contact_email}")
                else:
                    print(f"    ❌ Contact not found: {recipient}")
        else:
            print(f"    ❌ No recipient found")
    
    print(f"\n📞 AVAILABLE CONTACTS:")
    print("-" * 30)
    for name, email in CONTACTS.items():
        print(f"  {name:12} -> {email}")
    
    print(f"\n🔍 REGEX PATTERNS USED:")
    print("-" * 30)
    print("Deepgram Handler Patterns:")
    for i, pattern in enumerate(deepgram_patterns, 1):
        print(f"  {i:2d}. {pattern}")
    
    print("\nEmail Service Patterns:")
    for i, pattern in enumerate(email_service_patterns, 1):
        print(f"  {i:2d}. {pattern}")
    
    print(f"\n💡 TRIGGER KEYWORDS:")
    print("-" * 20)
    trigger_words = [
        "send", "email", "to", "about", "regarding", "concerning",
        "write", "draft", "compose", "an", "the"
    ]
    print("  " + ", ".join(trigger_words))

if __name__ == "__main__":
    test_all_triggers()
