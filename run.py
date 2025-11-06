"""
Quick start script for AI Stock Market Prediction Platform
"""
import os
import sys
import threading

def check_requirements():
    """Check if all requirements are installed"""
    try:
        import flask
        import flask_sqlalchemy
        import flask_login
        import flask_mail
        import pandas
        import sklearn
        
        import requests
        import bs4
        import google.generativeai
        print("✓ All required packages are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing package: {e}")
        print("\nPlease install requirements:")
        print("  pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists('.env'):
        print("✗ .env file not found")
        print("\nPlease create .env file from .env.example:")
        print("  1. Copy .env.example to .env")
        print("  2. Update the configuration values")
        return False
    print("✓ .env file found")
    return True

def initialize_database():
    """Initialize database"""
    try:
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            db.create_all()
            print("✓ Database initialized")
        return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False

def start_background_training(app):
    """Start self-training service in background thread"""
    try:
        from services.adaptive_monitor import start_adaptive_monitor
        
        # Email configuration
        # CONFIGURE YOUR EMAIL SETTINGS HERE:
        email_config = {
            'enabled': True,  # Set to True to enable email notifications
            'sender_email': os.getenv('EMAIL_SENDER', 'rautganesh9370@gmail.com'),  # Your Gmail address
            'sender_password': os.getenv('EMAIL_PASSWORD', 'sqjd qggz vwee kybi'),  # Gmail App Password (not regular password)
            'recipient_email': os.getenv('EMAIL_RECIPIENT', 'rautganesh9370@gmail.com'),  # Where to receive emails
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587))
        }
        
        # Check if email is properly configured
        if email_config['enabled']:
            if 'your_email' in email_config['sender_email'] or 'your_app_password' in email_config['sender_password']:
                print("\n⚠️  WARNING: Email is enabled but not configured!")
                print("   Please update email settings in run.py or .env file")
                print("   Email notifications will be disabled for now.\n")
                email_config['enabled'] = False
        
        print("\n" + "=" * 60)
        print("  🤖 Starting Self-Training Background Service")
        print("=" * 60)
        print()
        print("Background Service Features:")
        print("  • Automatic daily predictions at 10:00 AM")
        print("  • Tests 8 ML algorithms and selects best one")
        print("  • AI-powered stock recommendations")
        print("  • Accuracy checking at 3:45 PM")
        print("  • Self-learning from prediction errors")
        print("  • Auto-retraining when accuracy drops")
        print("  • Weekly model refresh")
        print()
        print(f"📧 Email Notifications: {'Enabled' if email_config['enabled'] else 'Disabled'}")
        if not email_config['enabled']:
            print("   (Configure email settings in .env to enable)")
        print("=" * 60)
        print()
        
        # Start in background thread
        monitor_thread = threading.Thread(
            target=start_adaptive_monitor,
            args=(app, email_config),
            daemon=True,
            name="AdaptiveMonitor"
        )
        monitor_thread.start()
        
        print("✓ Background training service started successfully")
        print()
        
    except Exception as e:
        print(f"⚠️  Warning: Could not start background training service: {e}")
        print("   Application will continue without self-training")
        print()

def main():
    """Main function"""
    print("=" * 60)
    print("  AI Stock Market Prediction Platform - Quick Start")
    print("=" * 60)
    print()
    
    # Check requirements
    print("[1/3] Checking requirements...")
    if not check_requirements():
        sys.exit(1)
    print()
    
    # Check .env file
    print("[2/3] Checking configuration...")
    if not check_env_file():
        sys.exit(1)
    print()
    
    # Initialize database
    print("[3/3] Initializing database...")
    if not initialize_database():
        sys.exit(1)
    print()
    
    print("=" * 60)
    print("  Setup Complete! Starting application...")
    print("=" * 60)
    print()
    print("Default Admin Credentials:")
    print("  Email: admin@stockai.com")
    print("  Password: admin123")
    print()
    print("⚠️  Please change admin password after first login!")
    print()
    print("Application will start at: http://localhost:5000")
    print("=" * 60)
    print()
    
    # Start application
    from app import create_app
    from utils.scheduler import start_scheduler
    
    app = create_app('development')
    
    # Start background self-training service
    start_background_training(app)
    
    # Start scheduler for other tasks
    start_scheduler(app)
    
    # Run Flask application
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()
