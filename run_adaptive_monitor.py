"""
Run Adaptive Monitor Service
Starts the self-learning background prediction service
"""

from app import create_app
from services.adaptive_monitor import start_adaptive_monitor
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 STARTING COMPLETE BACKGROUND SERVICE")
    print("=" * 80)
    print()
    print("This service will:")
    print("  • Test 8 different ML algorithms")
    print("  • Select the best performing algorithm")
    print("  • Make predictions at 10:00 AM daily")
    print("  • Generate AI stock recommendations")
    print("  • Send email with predictions & recommendations")
    print("  • Check accuracy at 3:30 PM")
    print("  • Self-learn from prediction errors")
    print("  • Send email with accuracy report")
    print("  • Automatically retrain when needed")
    print()
    print("=" * 80)
    print()
    
    # Email configuration (CONFIGURE THIS!)
    email_config = {
        'enabled': False,  # Set to True to enable email notifications
        'sender_email': 'your_email@gmail.com',
        'sender_password': 'your_app_password',  # Use Gmail App Password
        'recipient_email': 'recipient@gmail.com',
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587
    }
    
    print("📧 Email Configuration:")
    print(f"   Enabled: {email_config['enabled']}")
    if email_config['enabled']:
        print(f"   Sender: {email_config['sender_email']}")
        print(f"   Recipient: {email_config['recipient_email']}")
    else:
        print("   ⚠️  Email disabled - Edit email_config to enable")
    print()
    print("=" * 80)
    print()
    
    # Create Flask app
    app = create_app()
    
    # Start adaptive monitor with email config
    start_adaptive_monitor(app, email_config)
