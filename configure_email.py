"""
Email Configuration Helper
Run this to configure email for stock prediction alerts
"""

def configure_email():
    print("=" * 70)
    print("  📧 EMAIL CONFIGURATION FOR STOCK PREDICTION ALERTS")
    print("=" * 70)
    print()
    print("To receive email alerts with stock predictions, you need:")
    print("  1. A Gmail account")
    print("  2. Gmail App Password (NOT your regular password)")
    print()
    print("=" * 70)
    print()
    
    # Get email settings
    print("Step 1: Enter your Gmail address")
    sender_email = input("Your Gmail: ").strip()
    
    print()
    print("Step 2: Get Gmail App Password")
    print("  1. Go to: https://myaccount.google.com/")
    print("  2. Click 'Security' → '2-Step Verification' (enable it)")
    print("  3. Click 'Security' → 'App passwords'")
    print("  4. Select 'Mail' and 'Windows Computer'")
    print("  5. Click 'Generate' and copy the 16-character password")
    print()
    sender_password = input("Gmail App Password (16 characters): ").strip()
    
    print()
    print("Step 3: Where should we send the alerts?")
    recipient_email = input("Recipient Email (press Enter to use same): ").strip()
    if not recipient_email:
        recipient_email = sender_email
    
    print()
    print("=" * 70)
    print("  CONFIGURATION SUMMARY")
    print("=" * 70)
    print(f"Sender Email: {sender_email}")
    print(f"Recipient Email: {recipient_email}")
    print(f"App Password: {'*' * len(sender_password)}")
    print()
    
    confirm = input("Save this configuration? (y/n): ").lower()
    
    if confirm == 'y':
        # Update run.py
        try:
            with open('run.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace email settings
            content = content.replace(
                "'sender_email': os.getenv('EMAIL_SENDER', 'your_email@gmail.com')",
                f"'sender_email': os.getenv('EMAIL_SENDER', '{sender_email}')"
            )
            content = content.replace(
                "'sender_password': os.getenv('EMAIL_PASSWORD', 'your_app_password')",
                f"'sender_password': os.getenv('EMAIL_PASSWORD', '{sender_password}')"
            )
            content = content.replace(
                "'recipient_email': os.getenv('EMAIL_RECIPIENT', 'your_email@gmail.com')",
                f"'recipient_email': os.getenv('EMAIL_RECIPIENT', '{recipient_email}')"
            )
            
            with open('run.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print()
            print("✅ Email configuration saved successfully!")
            print()
            print("=" * 70)
            print("  WHAT HAPPENS NEXT")
            print("=" * 70)
            print()
            print("When you run 'python run.py', you will receive emails:")
            print()
            print("📧 Morning Email (10:00 AM):")
            print("   • Stock predictions for all active stocks")
            print("   • AI recommendations (Strong Buy/Sell)")
            print("   • Expected gains/losses")
            print("   • Confidence scores")
            print()
            print("📧 Evening Email (3:45 PM):")
            print("   • Accuracy report for today's predictions")
            print("   • Actual vs Predicted prices")
            print("   • Learning insights")
            print("   • Model performance stats")
            print()
            print("=" * 70)
            print()
            print("Ready to test? Run: python test_background_service.py")
            print()
            
        except Exception as e:
            print(f"\n❌ Error saving configuration: {e}")
            print("Please manually update email settings in run.py")
    else:
        print("\n❌ Configuration cancelled")
        print("You can run this script again anytime")

if __name__ == "__main__":
    configure_email()
