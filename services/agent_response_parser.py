"""
Agent Response Parser
Parses agent responses to detect email triggers and prevent duplicates
"""

import re
import json
import hashlib
from typing import Dict, Any, Optional, Set
from email_service import EmailService
from constants import CONTACTS

class AgentResponseParser:
    def __init__(self, email_service: EmailService):
        """
        Initialize the agent response parser
        
        Args:
            email_service: EmailService instance
        """
        self.email_service = email_service
        self.processed_responses: Set[str] = set()  # Track processed responses to prevent duplicates
        
    def parse_agent_response(self, response: str) -> Dict[str, Any]:
        """
        Parse agent response to detect email triggers
        
        Args:
            response: Agent's response text
            
        Returns:
            Dictionary with parsing results
        """
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
    
    def process_email_trigger(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the email trigger and send the email
        
        Args:
            trigger_data: Parsed email trigger data
            
        Returns:
            Dictionary with email processing results
        """
        try:
            recipient = trigger_data["recipient"]
            subject = trigger_data["subject"]
            body = trigger_data["body"]
            context = trigger_data.get("context", "")
            
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
    
    def handle_agent_response(self, response: str) -> Dict[str, Any]:
        """
        Handle a complete agent response (parse + process if needed)
        
        Args:
            response: Complete agent response
            
        Returns:
            Dictionary with handling results
        """
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
    
    def clear_processed_responses(self):
        """Clear the processed responses cache (useful for testing)"""
        self.processed_responses.clear()
    
    def get_processed_count(self) -> int:
        """Get the number of processed responses"""
        return len(self.processed_responses)

def main():
    """
    Test the agent response parser
    """
    try:
        # Initialize services
        email_service = EmailService()
        parser = AgentResponseParser(email_service)
        
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
        
        print("🧪 Testing Agent Response Parser")
        print("=" * 50)
        
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
        
        print(f"\n📊 Processed {parser.get_processed_count()} unique responses")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
