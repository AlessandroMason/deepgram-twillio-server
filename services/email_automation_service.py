"""
Email Automation Service
Handles JSON validation, email sending, and agent injection for email automation
"""

import json
import re
import asyncio
import aiohttp
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, ValidationError
from guardrails import Guard


class EmailRequest(BaseModel):
    """Pydantic model for email request validation"""
    to: str
    subject: str
    message: str


class EmailAutomationService:
    """Service for handling email automation with JSON validation"""
    
    def __init__(self, webhook_url: str = "https://kayros.app.n8n.cloud/webhook/send-email"):
        """
        Initialize the email automation service
        
        Args:
            webhook_url: URL for the n8n webhook to send emails
        """
        self.webhook_url = webhook_url
        self.guard = self._setup_guardrails()
        
    def _setup_guardrails(self) -> Guard:
        """Setup Guardrails for JSON validation"""
        return Guard()
    
    def detect_json_in_response(self, response: str) -> Optional[str]:
        """
        Detect if the response contains JSON that looks like an email request
        
        Args:
            response: Agent response text
            
        Returns:
            JSON string if found, None otherwise
        """
        # Look for JSON-like patterns in the response with various field names
        json_patterns = [
            # Standard field names
            r'\{[^{}]*"to"[^{}]*"subject"[^{}]*"message"[^{}]*\}',
            r'\{[^{}]*"subject"[^{}]*"to"[^{}]*"message"[^{}]*\}',
            r'\{[^{}]*"message"[^{}]*"to"[^{}]*"subject"[^{}]*\}',
            # Alternative field names
            r'\{[^{}]*"recipient"[^{}]*"title"[^{}]*"body"[^{}]*\}',
            r'\{[^{}]*"title"[^{}]*"recipient"[^{}]*"body"[^{}]*\}',
            r'\{[^{}]*"body"[^{}]*"recipient"[^{}]*"title"[^{}]*\}',
            # Mixed field names
            r'\{[^{}]*"(?:to|recipient)"[^{}]*"(?:subject|title)"[^{}]*"(?:message|body)"[^{}]*\}',
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(0)
        
        # Also look for any JSON object that might be an email request
        json_objects = re.findall(r'\{[^{}]*(?:"to"|"subject"|"message"|"recipient"|"title"|"body"|"email"|"address")[^{}]*\}', response, re.DOTALL | re.IGNORECASE)
        for json_obj in json_objects:
            if self._looks_like_email_json(json_obj):
                return json_obj
                
        return None
    
    def _looks_like_email_json(self, json_str: str) -> bool:
        """
        Check if a JSON string looks like an email request
        
        Args:
            json_str: JSON string to check
            
        Returns:
            True if it looks like an email request
        """
        try:
            data = json.loads(json_str)
            # Check if it has email-related fields
            email_fields = ['to', 'subject', 'message', 'recipient', 'body', 'content', 'title', 'email', 'address']
            return any(field in str(data).lower() for field in email_fields)
        except:
            return False
    
    def validate_email_json(self, json_str: str) -> Tuple[bool, Optional[EmailRequest], Optional[str]]:
        """
        Validate email JSON using Guardrails and Pydantic
        
        Args:
            json_str: JSON string to validate
            
        Returns:
            Tuple of (is_valid, email_request, error_message)
        """
        try:
            # First, try to parse as JSON
            json_data = json.loads(json_str)
            
            # Use Guardrails to validate JSON structure (basic validation)
            try:
                validated_json = self.guard.validate(json_str)
            except Exception as guard_error:
                # If Guardrails fails, we'll still try Pydantic validation
                print(f"Guardrails validation warning: {guard_error}")
            
            # Map common field names to our expected format
            mapped_data = self._map_email_fields(json_data)
            
            # Validate with Pydantic
            email_request = EmailRequest(**mapped_data)
            
            return True, email_request, None
            
        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON format: {str(e)}"
        except ValidationError as e:
            return False, None, f"Validation error: {str(e)}"
        except Exception as e:
            return False, None, f"Validation failed: {str(e)}"
    
    def _map_email_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map various field names to our expected format
        
        Args:
            data: Raw JSON data
            
        Returns:
            Mapped data with standard field names
        """
        mapped = {}
        
        # Map 'to' field
        for field in ['to', 'recipient', 'email', 'address']:
            if field in data:
                mapped['to'] = data[field]
                break
        
        # Map 'subject' field
        for field in ['subject', 'title', 'topic']:
            if field in data:
                mapped['subject'] = data[field]
                break
        
        # Map 'message' field
        for field in ['message', 'body', 'content', 'text']:
            if field in data:
                mapped['message'] = data[field]
                break
        
        return mapped
    
    async def send_email(self, email_request: EmailRequest) -> Tuple[bool, str]:
        """
        Send email via n8n webhook
        
        Args:
            email_request: Validated email request
            
        Returns:
            Tuple of (success, message)
        """
        try:
            payload = {
                "to": email_request.to,
                "subject": email_request.subject,
                "message": email_request.message
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return True, "Email sent successfully"
                    else:
                        error_text = await response.text()
                        return False, f"Failed to send email: {response.status} - {error_text}"
                        
        except asyncio.TimeoutError:
            return False, "Email sending timed out"
        except Exception as e:
            return False, f"Error sending email: {str(e)}"
    
    def create_validation_error_prompt(self, error_message: str) -> str:
        """
        Create a prompt to ask the agent to fix JSON validation errors
        
        Args:
            error_message: Error message from validation
            
        Returns:
            Prompt string for agent injection
        """
        return f"""The JSON you provided has validation errors: {error_message}

Please provide a valid email request in this exact JSON format:
{{
    "to": "recipient@example.com",
    "subject": "Your email subject",
    "message": "Your email message content"
}}

Make sure all three fields (to, subject, message) are present and properly formatted."""
    
    def create_success_confirmation_prompt(self, email_request: EmailRequest) -> str:
        """
        Create a confirmation prompt for successful email sending
        
        Args:
            email_request: The email request that was sent
            
        Returns:
            Confirmation prompt string
        """
        return f"""✅ Email sent successfully!

Recipient: {email_request.to}
Subject: {email_request.subject}
Message: {email_request.message}

The email has been delivered via the automation system."""
    
    async def process_agent_response(self, response: str) -> Tuple[bool, Optional[str], Optional[EmailRequest]]:
        """
        Process agent response to detect and handle email requests
        
        Args:
            response: Agent response text
            
        Returns:
            Tuple of (has_email_request, injection_prompt, email_request)
        """
        # Detect JSON in response
        json_str = self.detect_json_in_response(response)
        
        if not json_str:
            return False, None, None
        
        # Validate the JSON
        is_valid, email_request, error_message = self.validate_email_json(json_str)
        
        if not is_valid:
            # Create error correction prompt
            correction_prompt = self.create_validation_error_prompt(error_message)
            return True, correction_prompt, None
        
        # JSON is valid, return the email request
        return True, None, email_request


# Test function
async def test_email_automation():
    """Test the email automation service"""
    service = EmailAutomationService()
    
    # Test cases
    test_cases = [
        '{"to": "test@example.com", "subject": "Test", "message": "Hello"}',
        '{"recipient": "test@example.com", "title": "Test", "body": "Hello"}',
        '{"to": "test@example.com", "subject": "Test"}',  # Missing message
        'Invalid JSON',
        '{"to": "test@example.com", "subject": "Test", "message": "Hello", "extra": "field"}',
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest {i+1}: {test_case}")
        is_valid, email_request, error = service.validate_email_json(test_case)
        print(f"Valid: {is_valid}")
        if email_request:
            print(f"Email: {email_request.to} - {email_request.subject}")
        if error:
            print(f"Error: {error}")


if __name__ == "__main__":
    asyncio.run(test_email_automation())
