#!/usr/bin/env python3
"""
Example script demonstrating the email service
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.email_service import EmailService

def main():
    """
    Example usage of the email service
    """
    print("📧 Email Service Example")
    print("=" * 50)
    
    # Check environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY='your-openai-api-key'")
        return
    
    try:
        # Initialize service
        print("🔄 Initializing email service...")
        service = EmailService()
        print("✅ Email service initialized")
        print(f"📧 Using Gmail: axm2022@case.edu")
        print(f"🔑 Using Gmail password: iwtn sges urbz tkuo")
        
        # Example email requests
        examples = [
            {
                "message": "send an email to john.doe@company.com with all the details about the project update",
                "context": "User has been working on a machine learning project and wants to update stakeholders about progress"
            },
            {
                "message": "email sarah@example.org about the meeting tomorrow at 2pm",
                "context": "User has a meeting scheduled and wants to confirm details"
            },
            {
                "message": "write an email to team@startup.io with the quarterly report summary",
                "context": "User has completed quarterly analysis and wants to share results with the team"
            }
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"\n--- Example {i} ---")
            print(f"Message: {example['message']}")
            print(f"Context: {example['context']}")
            
            # Process the email request (save as draft)
            result = service.process_email_request(example['message'], example['context'], send_email=False)
            
            if result["success"]:
                print("✅ Email draft created successfully!")
                print(f"📧 Subject: {result['subject']}")
                print(f"📝 Preview: {result['preview']}")
                print(f"📁 Action: {result['action']}")
            else:
                print(f"❌ Error: {result['error']}")
                print(f"💬 Message: {result['message']}")
            
            print("-" * 50)
        
        print("\n🎉 Example completed!")
        print("\n📋 To use in your voice agent:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Integrate with your voice agent")
        print("3. Emails will be saved as drafts in the 'drafts' folder")
        
        # Show drafts folder
        if os.path.exists('drafts'):
            draft_files = [f for f in os.listdir('drafts') if f.endswith('.txt')]
            if draft_files:
                print(f"\n📁 Found {len(draft_files)} draft files in 'drafts' folder:")
                for file in draft_files[:3]:  # Show first 3
                    print(f"  - {file}")
                if len(draft_files) > 3:
                    print(f"  ... and {len(draft_files) - 3} more")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
