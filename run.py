"""
Quick start script for AI Stock Market Prediction Platform
"""
import os
import sys

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
    start_scheduler(app)
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()
