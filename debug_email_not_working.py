#!/usr/bin/env python
"""
Complete Email Debug - Shows exactly what's being sent and why
"""

import sys
sys.path.insert(0, r'c:\Users\rautg\Desktop\StockMarket_prediction')

from app import create_app
from models import User, OTP, db
from routes.auth import generate_otp
from datetime import datetime, timedelta
import os

app = create_app('development')

print("\n" + "="*80)
print(" " * 20 + "EMAIL DEBUG DIAGNOSTIC")
print("="*80 + "\n")

# Check .env file
print("STEP 1: Checking .env file")
print("-" * 80)
env_path = r'c:\Users\rautg\Desktop\StockMarket_prediction\.env'
with open(env_path, 'r') as f:
    lines = f.readlines()
    for line in lines:
        if 'MAIL' in line and not line.startswith('#'):
            # Show masked version
            if 'PASSWORD' in line:
                print(f"  {line.strip()[:50]}...")
            else:
                print(f"  {line.strip()}")

print("\n✅ .env file read\n")

# Check Flask config
print("STEP 2: Checking Flask Configuration")
print("-" * 80)
with app.app_context():
    print(f"  MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
    print(f"  MAIL_PORT: {app.config.get('MAIL_PORT')}")
    print(f"  MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
    print(f"  MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
    mail_pwd = app.config.get('MAIL_PASSWORD', '')
    print(f"  MAIL_PASSWORD: {'*' * len(mail_pwd)} (length: {len(mail_pwd)})")
    print(f"  MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
    
print("\n✅ Configuration loaded\n")

# Test with registered user
print("STEP 3: Checking Registered Users")
print("-" * 80)
with app.app_context():
    users = User.query.all()
    print(f"  Total users in database: {len(users)}\n")
    
    if not users:
        print("  ❌ NO USERS REGISTERED!")
        print("  You must register at: http://localhost:5000/auth/register first\n")
        sys.exit(1)
    
    test_user = users[0]
    print(f"  Using user: {test_user.username}")
    print(f"  Email: {test_user.email}")
    print(f"  Verified: {test_user.is_verified}\n")

print("STEP 4: Simulating Forgot Password Request")
print("-" * 80)
with app.app_context():
    test_email = test_user.email
    
    # Check if user exists
    user = User.query.filter_by(email=test_email).first()
    print(f"  Email entered: {test_email}")
    print(f"  User exists: {user is not None}")
    
    if not user:
        print("\n  ❌ User not found! OTP won't be sent")
        sys.exit(1)
    
    print(f"  ✅ User found: {user.username}\n")
    
    # Generate OTP
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    print(f"  Generating OTP...")
    print(f"    OTP Code: {otp_code}")
    print(f"    Expires: {expires_at}")
    
    # Create OTP record
    print(f"\n  Creating OTP record...")
    otp = OTP(
        email=test_email,
        otp_code=otp_code,
        purpose='password_reset',
        expires_at=expires_at
    )
    db.session.add(otp)
    db.session.commit()
    print(f"    ✅ OTP stored in database")
    print(f"    ID: {otp.id}\n")
    
    # Verify OTP was stored
    print(f"  Verifying OTP in database...")
    stored = OTP.query.filter_by(otp_code=otp_code).first()
    if stored:
        print(f"    ✅ OTP verified in database\n")
    else:
        print(f"    ❌ OTP NOT FOUND in database!\n")
        sys.exit(1)

print("STEP 5: Sending Email")
print("-" * 80)

from utils.email_service import mail, send_otp_email

with app.app_context():
    try:
        print(f"  Attempting to send OTP email...")
        print(f"    To: {test_email}")
        print(f"    OTP: {otp_code}")
        print(f"    From: {app.config.get('MAIL_DEFAULT_SENDER')}")
        print(f"    Via: {app.config.get('MAIL_SERVER')}:{app.config.get('MAIL_PORT')}\n")
        
        # Send email
        result = send_otp_email(test_email, otp_code, 'password reset')
        
        print(f"  ✅ Email function executed successfully!")
        print(f"    Result: {result}\n")
        
    except Exception as e:
        print(f"\n  ❌ ERROR SENDING EMAIL:")
        print(f"  {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print("="*80)
print(" " * 25 + "✅ DIAGNOSTIC COMPLETE")
print("="*80)

print("\n📧 What Should Happen Now:")
print(f"  1. Email sent FROM: {app.config.get('MAIL_DEFAULT_SENDER')}")
print(f"  2. Email sent TO: {test_email}")
print(f"  3. Subject: Your OTP Code - AI Stock Market Prediction")
print(f"  4. OTP Code in email: {otp_code}")
print(f"  5. Email delivery: 1-5 minutes")

print("\n❓ If Email Not Received:")
print(f"  1. Check SPAM/JUNK folder")
print(f"  2. Wait 5 minutes (sometimes slow)")
print(f"  3. Check email address: {test_email}")
print(f"  4. Check MAIL_PASSWORD in .env is correct")
print(f"     Current password (first 10 chars): {app.config.get('MAIL_PASSWORD', '')[:10]}")
print(f"  5. Regenerate Gmail app password:")
print(f"     https://myaccount.google.com/apppasswords")
print(f"  6. Update .env and restart app")

print("\n🔗 Check .env file:")
print(f"  Path: {env_path}")
print(f"  Username: {app.config.get('MAIL_USERNAME')}")
print(f"  Password should be: app-specific password (16 chars with spaces)")

print("\n" + "="*80 + "\n")
