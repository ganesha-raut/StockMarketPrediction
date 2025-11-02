"""Test email configuration"""
from app import create_app
from flask_mail import Message
from utils.email_service import mail

app = create_app()

with app.app_context():
    print("=" * 60)
    print("Testing Email Configuration")
    print("=" * 60)
    print()
    print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
    print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
    print(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
    print(f"MAIL_PASSWORD: {'*' * len(app.config.get('MAIL_PASSWORD', ''))}")
    print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
    print()
    
    # Test sending email
    try:
        print("Sending test email...")
        msg = Message(
            subject="Test Email - AI Stock Platform",
            recipients=[app.config.get('MAIL_USERNAME')],
            body="This is a test email from your AI Stock Market Prediction Platform. If you receive this, email is working!"
        )
        mail.send(msg)
        print("✓ Email sent successfully!")
        print(f"✓ Check your inbox: {app.config.get('MAIL_USERNAME')}")
    except Exception as e:
        print(f"✗ Email failed: {e}")
    
    print("=" * 60)
