#!/usr/bin/env python3
"""
Test script for the agent email trigger system
"""

import os
import sys
import json
import re
import hashlib
sys.path.append('.')

from services.email_service import EmailService
from constants import CONTACTS

class AgentResponseParser:
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
        self.processed_responses: set = set()
        
    def parse_agent_response(self, response: str):
        # Create a hash of the response to detect duplicates
        response_hash = hashlib.md5(response.encode()).hexdigest()
        
        # Check if we've already processed this response
        if response_hash in self.processed_responses:
            return {
                "success": False,
                "is_duplicate": True,
                "message": "Response already processed, skipping to prevent duplicate emails"
            }
        
        # Look for EMAIL_TRIGGER pattern
        email_trigger_pattern = r'EMAIL_TRIGGER:\s*(\{.*?\})'
        match = re.search(email_trigger_pattern, response, re.DOTALL)
        
        if not match:
            return {
                "success": False,
                "is_duplicate": False,
                "message": "No email trigger found in response"
            }
        
        try:
            # Parse the JSON trigger
            trigger_json = match.group(1)
            trigger_data = json.loads(trigger_json)
            
            # Validate required fields
            if not all(key in trigger_data for key in ["action", "recipient", "subject", "body"]):
                return {
                    "success": False,
                    "is_duplicate": False,
                    "error": "Invalid email trigger format - missing required fields"
                }
            
            # Mark this response as processed
            self.processed_responses.add(response_hash)
            
            return {
                "success": True,
                "is_duplicate": False,
                "trigger_data": trigger_data,
                "response_hash": response_hash
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "is_duplicate": False,
                "error": f"Invalid JSON in email trigger: {str(e)}"
            }
    
    def process_email_trigger(self, trigger_data):
        try:
            recipient = trigger_data["recipient"]
            subject = trigger_data["subject"]
            body = trigger_data["body"]
            
            # Check if recipient is a contact name or direct email
            if "@" not in recipient:
                # Look up contact email
                contact_email = self.email_service.find_contact_email(recipient)
                if not contact_email:
                    return {
                        "success": False,
                        "error": f"Contact '{recipient}' not found",
                        "available_contacts": list(CONTACTS.keys())
                    }
                recipient = contact_email
            
            # Send the email
            success = self.email_service.create_draft_email(
                to_email=recipient,
                subject=subject,
                body=body
            )
            
            if success:
                return {
                    "success": True,
                    "message": f"Email sent successfully to {recipient}",
                    "subject": subject,
                    "recipient": recipient
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to send email"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing email trigger: {str(e)}"
            }
    
    def handle_agent_response(self, response: str):
        # Parse the response
        parse_result = self.parse_agent_response(response)
        
        if not parse_result["success"]:
            return parse_result
        
        # Process the email trigger
        email_result = self.process_email_trigger(parse_result["trigger_data"])
        
        return {
            "success": email_result["success"],
            "message": email_result.get("message", ""),
            "error": email_result.get("error", ""),
            "email_sent": email_result["success"],
            "recipient": email_result.get("recipient", ""),
            "subject": email_result.get("subject", ""),
            "is_duplicate": parse_result["is_duplicate"]
        }

def test_agent_email_system():
    """Test the agent email trigger system"""
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize services
        email_service = EmailService()
        parser = AgentResponseParser(email_service)
        
        print("🧪 Testing Agent Email Trigger System")
        print("=" * 60)
        
        # Test responses
        test_responses = [
            # Normal response without email trigger
            "That's a great question! I think you should focus on your health first.",
            
            # Response with email trigger
            "I'll send that email to John about the meeting tomorrow.\n\nEMAIL_TRIGGER: {\"action\": \"send_email\", \"recipient\": \"john\", \"subject\": \"Meeting Tomorrow\", \"body\": \"Hi John, just wanted to confirm our meeting tomorrow. Looking forward to discussing the project updates.\", \"context\": \"Meeting confirmation\"}",
            
            # Duplicate response (should be skipped)
            "I'll send that email to John about the meeting tomorrow.\n\nEMAIL_TRIGGER: {\"action\": \"send_email\", \"recipient\": \"john\", \"subject\": \"Meeting Tomorrow\", \"body\": \"Hi John, just wanted to confirm our meeting tomorrow. Looking forward to discussing the project updates.\", \"context\": \"Meeting confirmation\"}",
            
            # Response with direct email
            "I'll send that email to Alessandro about the project.\n\nEMAIL_TRIGGER: {\"action\": \"send_email\", \"recipient\": \"axm2022@case.edu\", \"subject\": \"Project Update\", \"body\": \"Hi Alessandro, here's the project update you requested.\", \"context\": \"Project status\"}"
        ]
        
        for i, response in enumerate(test_responses, 1):
            print(f"\n{i}. Testing Response:")
            print(f"   '{response[:100]}{'...' if len(response) > 100 else ''}'")
            
            result = parser.handle_agent_response(response)
            
            if result["success"]:
                print(f"   ✅ Email sent successfully!")
                print(f"   📧 Recipient: {result['recipient']}")
                print(f"   📝 Subject: {result['subject']}")
            elif result.get("is_duplicate"):
                print(f"   ⏭️  Duplicate response, skipped")
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        
        print(f"\n📊 Processed {len(parser.processed_responses)} unique responses")
        
        # Test the updated prompt
        print(f"\n🤖 Updated Agent Prompt Preview:")
        print("-" * 40)
        from constants import UPDATED_INITIAL_PROMPT
        print(UPDATED_INITIAL_PROMPT[:500] + "...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent_email_system()
