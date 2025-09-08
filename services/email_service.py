import openai
import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import re

class EmailService:
    def __init__(self, openai_api_key: str = None, gmail_email: str = "axm2022@case.edu", gmail_password: str = None):
        """
        Initialize email service with OpenAI and Gmail SMTP integration
        
        Args:
            openai_api_key: OpenAI API key
            gmail_email: Gmail email address
            gmail_password: Gmail app password (if None, will use GMAIL_PASSWORD env var)
        """
        if openai_api_key is None:
            openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not openai_api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or pass openai_api_key parameter.")
        
        if gmail_password is None:
            gmail_password = os.getenv("GMAIL_PASSWORD")
        
        if not gmail_password:
            raise ValueError("Gmail password not provided. Set GMAIL_PASSWORD environment variable or pass gmail_password parameter.")
        
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.gmail_email = gmail_email
        self.gmail_password = gmail_password
        
    def send_test_email(self, recipient: str = "axm2022@case.edu", subject: str = "Testing", body: str = "testing") -> bool:
        """
        Send a simple test email
        
        Args:
            recipient: Email recipient (default: axm2022@case.edu)
            subject: Email subject (default: "Testing")
            body: Email body (default: "testing")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart()
            message['From'] = self.gmail_email
            message['To'] = recipient
            message['Subject'] = subject
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Connect to Gmail SMTP server
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.gmail_email, self.gmail_password)
            
            # Send email
            text = message.as_string()
            server.sendmail(self.gmail_email, recipient, text)
            server.quit()
            
            print(f"✅ Test email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending test email: {e}")
            return False
    
    def check_and_trigger_email(self, agent_reply: str) -> bool:
        """
        Check if agent reply contains 'email' and trigger email sending
        
        Args:
            agent_reply: The agent's response text
            
        Returns:
            True if email was sent, False otherwise
        """
        if "email" in agent_reply.lower():
            print("📧 Agent reply contains 'email' - triggering test email...")
            return self.send_test_email()
        return False
        
    def generate_email_content(self, recipient: str, description: str, context: str = "") -> Dict[str, str]:
        """
        Generate email content using OpenAI
        
        Args:
            recipient: Email recipient
            description: Description of what the email should contain
            context: Additional context (e.g., diary entries)
            
        Returns:
            Dictionary with subject and body
        """
        try:
            prompt = f"""
You are an AI assistant helping to compose a professional email. Based on the following information, create a well-structured email:

Recipient: {recipient}
Description: {description}
Additional Context: {context}

Please create:
1. A professional subject line
2. A well-structured email body that is:
   - Professional and appropriate
   - Clear and concise
   - Engaging and relevant to the recipient
   - Properly formatted

Return the response in JSON format:
{{
    "subject": "Your subject line here",
    "body": "Your email body here"
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional email writing assistant. Always respond with valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                email_data = json.loads(content)
                return {
                    "subject": email_data.get("subject", "No Subject"),
                    "body": email_data.get("body", "No content generated")
                }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                lines = content.split('\n')
                subject = "Generated Email"
                body = content
                
                for line in lines:
                    if line.strip().startswith('Subject:'):
                        subject = line.replace('Subject:', '').strip()
                    elif line.strip().startswith('Body:'):
                        body = '\n'.join(lines[lines.index(line)+1:])
                        break
                
                return {
                    "subject": subject,
                    "body": body
                }
                
        except Exception as e:
            print(f"Error generating email content: {e}")
            return {
                "subject": "Generated Email",
                "body": f"Error generating email content: {str(e)}"
            }
    
    def create_draft_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        Create a draft email using Gmail SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart()
            message['From'] = self.gmail_email
            message['To'] = to_email
            message['Subject'] = subject
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Connect to Gmail SMTP server
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.gmail_email, self.gmail_password)
            
            # Send email
            text = message.as_string()
            server.sendmail(self.gmail_email, to_email, text)
            server.quit()
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
    
    def save_draft_to_file(self, to_email: str, subject: str, body: str) -> bool:
        """
        Save draft email to a file (alternative to sending)
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create drafts directory if it doesn't exist
            os.makedirs('drafts', exist_ok=True)
            
            # Create filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"drafts/email_{timestamp}_{to_email.replace('@', '_at_')}.txt"
            
            # Write draft to file
            with open(filename, 'w') as f:
                f.write(f"To: {to_email}\n")
                f.write(f"From: {self.gmail_email}\n")
                f.write(f"Subject: {subject}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 50 + "\n")
                f.write(body)
            
            print(f"✅ Draft saved to {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving draft: {e}")
            return False
    
    def process_email_request(self, user_message: str, context: str = "", send_email: bool = False) -> Dict[str, Any]:
        """
        Process a user's email request and create a draft or send email
        
        Args:
            user_message: User's message about sending an email
            context: Additional context (e.g., diary entries)
            send_email: If True, sends email; if False, saves as draft
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Extract recipient and description from user message
            recipient, description = self._extract_email_info(user_message)
            
            if not recipient:
                return {
                    "success": False,
                    "error": "Could not extract recipient email address",
                    "message": "Please provide a valid email address"
                }
            
            # Generate email content
            print(f"🔄 Generating email content for {recipient}...")
            email_content = self.generate_email_content(recipient, description, context)
            
            # Create or send email
            if send_email:
                print(f"📧 Sending email...")
                success = self.create_draft_email(
                    to_email=recipient,
                    subject=email_content["subject"],
                    body=email_content["body"]
                )
                action = "sent"
            else:
                print(f"📧 Saving draft email...")
                success = self.save_draft_to_file(
                    to_email=recipient,
                    subject=email_content["subject"],
                    body=email_content["body"]
                )
                action = "saved as draft"
            
            if success:
                return {
                    "success": True,
                    "message": f"Email {action} successfully for {recipient}",
                    "subject": email_content["subject"],
                    "preview": email_content["body"][:200] + "..." if len(email_content["body"]) > 200 else email_content["body"],
                    "action": action
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to {action}",
                    "message": f"There was an error {action} the email"
                }
                
        except Exception as e:
            print(f"❌ Error processing email request: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred while processing your email request"
            }
    
    def _extract_email_info(self, message: str) -> tuple:
        """
        Extract recipient email and description from user message
        
        Args:
            message: User's message
            
        Returns:
            Tuple of (recipient_email, description)
        """
        # Email regex pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Find email addresses
        emails = re.findall(email_pattern, message)
        recipient = emails[0] if emails else None
        
        # Extract description (remove email and common phrases)
        description = message
        if recipient:
            description = description.replace(recipient, "")
        
        # Remove common email request phrases
        phrases_to_remove = [
            "send an email to",
            "email to",
            "send email",
            "write an email",
            "compose an email",
            "draft an email"
        ]
        
        for phrase in phrases_to_remove:
            description = description.replace(phrase, "")
        
        description = description.strip()
        
        return recipient, description

def main():
    """
    Example usage of the EmailService
    """
    try:
        # Initialize the service
        service = EmailService()
        
        # Test email generation
        test_message = "send an email to john.doe@example.com with all the details about the project update"
        context = "User has been working on a machine learning project and wants to update stakeholders"
        
        print("🧪 Testing Email Service")
        print("=" * 50)
        
        # Test saving as draft
        result = service.process_email_request(test_message, context, send_email=False)
        
        if result["success"]:
            print("✅ Email draft created successfully!")
            print(f"📧 Subject: {result['subject']}")
            print(f"📝 Preview: {result['preview']}")
            print(f"📁 Action: {result['action']}")
        else:
            print(f"❌ Error: {result['error']}")
            print(f"💬 Message: {result['message']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure to set the OPENAI_API_KEY and GMAIL_PASSWORD environment variables")

if __name__ == "__main__":
    main()
