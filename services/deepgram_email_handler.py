"""
Deepgram Email Handler
Handles voice commands for sending emails via Deepgram
"""

import re
import json
from typing import Dict, Any, Optional
from .email_service import EmailService
from agents.constants import CONTACTS

class DeepgramEmailHandler:
    def __init__(self, email_service: EmailService):
        """
        Initialize the Deepgram email handler
        
        Args:
            email_service: EmailService instance
        """
        self.email_service = email_service
        
    def parse_voice_command(self, voice_text: str) -> Dict[str, Any]:
        """
        Parse voice command to extract email details
        
        Args:
            voice_text: Text from Deepgram voice recognition
            
        Returns:
            Dictionary with parsed email information
        """
        # Common patterns for email commands
        patterns = [
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
        
        voice_text_lower = voice_text.lower().strip()
        
        for pattern in patterns:
            match = re.search(pattern, voice_text_lower, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                description = match.group(2).strip()
                
                # Find email for the contact
                email = self.email_service.find_contact_email(name)
                
                if email:
                    return {
                        "success": True,
                        "recipient": email,
                        "name": name,
                        "description": description,
                        "original_text": voice_text
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Contact '{name}' not found",
                        "available_contacts": list(CONTACTS.keys()),
                        "original_text": voice_text
                    }
        
        return {
            "success": False,
            "error": "Could not parse email command",
            "suggestions": [
                "Try: 'send email to [name] about [topic]'",
                "Try: 'email [name] regarding [topic]'",
                "Try: 'compose email to [name] about [topic]'"
            ],
            "original_text": voice_text
        }
    
    def handle_voice_email_request(self, voice_text: str, context: str = "", send_email: bool = False) -> Dict[str, Any]:
        """
        Handle voice-triggered email request
        
        Args:
            voice_text: Voice command text
            context: Additional context (e.g., diary entries)
            send_email: Whether to send email or save as draft
            
        Returns:
            Dictionary with processing results
        """
        # Parse the voice command
        parsed = self.parse_voice_command(voice_text)
        
        if not parsed["success"]:
            return parsed
        
        # Create the email message for the service
        email_message = f"send an email to {parsed['recipient']} {parsed['description']}"
        
        # Process the email request
        result = self.email_service.process_email_request(
            user_message=email_message,
            context=context,
            send_email=send_email
        )
        
        # Add voice-specific information
        result["voice_parsed"] = parsed
        result["voice_command"] = voice_text
        
        return result
    
    def get_available_contacts(self) -> Dict[str, str]:
        """
        Get list of available contacts
        
        Returns:
            Dictionary of contact names and emails
        """
        return CONTACTS.copy()
    
    def add_contact(self, name: str, email: str) -> bool:
        """
        Add a new contact (this would need to update agents/constants.py)
        
        Args:
            name: Contact name
            email: Contact email
            
        Returns:
            True if successful
        """
        # Note: This would need to update the agents/constants.py file
        # For now, just return success
        print(f"Contact '{name}' with email '{email}' would be added")
        return True

def create_standard_response(success: bool, message: str, **kwargs) -> str:
    """
    Create a standard response format for Deepgram
    
    Args:
        success: Whether the operation was successful
        message: Response message
        **kwargs: Additional data
        
    Returns:
        Standardized response string
    """
    response = {
        "action": "email",
        "success": success,
        "message": message,
        **kwargs
    }
    
    return json.dumps(response, indent=2)

def main():
    """
    Test the Deepgram email handler
    """
    try:
        # Initialize services
        email_service = EmailService()
        handler = DeepgramEmailHandler(email_service)
        
        # Test voice commands
        test_commands = [
            "send email to alessandro about the project update",
            "email john regarding the meeting tomorrow",
            "compose email to jane about the budget proposal",
            "send to bob about the client feedback"
        ]
        
        print("🧪 Testing Deepgram Email Handler")
        print("=" * 50)
        
        for command in test_commands:
            print(f"\n🎤 Voice Command: '{command}'")
            result = handler.handle_voice_email_request(command, send_email=False)
            
            if result["success"]:
                print(f"✅ Parsed successfully!")
                print(f"📧 Recipient: {result['voice_parsed']['recipient']}")
                print(f"📝 Description: {result['voice_parsed']['description']}")
                print(f"📋 Subject: {result['subject']}")
            else:
                print(f"❌ Error: {result['error']}")
        
        # Show available contacts
        print(f"\n📞 Available Contacts:")
        contacts = handler.get_available_contacts()
        for name, email in contacts.items():
            print(f"  {name}: {email}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
