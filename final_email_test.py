#!/usr/bin/env python
"""
Final Email Verification Test
Shows the EXACT email being sent to Gmail
"""

import sys
sys.path.insert(0, r'c:\Users\rautg\Desktop\StockMarket_prediction')

import time
from app import create_app
from models import User, OTP, db
from routes.auth import generate_otp
from datetime import datetime, timedelta
from utils.email_service import send_otp_email

app = create_app('development')

print("\n" + "="*80)
print(" " * 20 + "FINAL EMAIL VERIFICATION TEST")
print("="*80 + "\n")

with app.app_context():
    # Get a user
    user = User.query.first()
    if not user:
        print("❌ No users in database")
        sys.exit(1)
    
    test_email = user.email
    
    # Generate OTP
    otp_code = generate_otp()
    
    print(f"📧 EMAIL TO BE SENT:")
    print("-" * 80)
    print(f"  FROM: ganeshraut.contact@gmail.com")
    print(f"  TO: {test_email}")
    print(f"  SUBJECT: Your OTP Code - AI Stock Market Prediction")
    print(f"  OTP CODE: {otp_code}")
    print(f"  EXPIRES: 10 minutes from now")
    print()
    
    print(f"📝 STORING OTP IN DATABASE:")
    print("-" * 80)
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    otp = OTP(
        email=test_email,
        otp_code=otp_code,
        purpose='password_reset',
        expires_at=expires_at
    )
    db.session.add(otp)
    db.session.commit()
    print(f"  ✅ OTP {otp_code} stored in database")
    print()
    
    print(f"📤 SENDING EMAIL:")
    print("-" * 80)
    print(f"  Calling send_otp_email('{test_email}', '{otp_code}', 'password reset')")
    print()
    
    # Send email
    result = send_otp_email(test_email, otp_code, 'password reset')
    print(f"  Result: {result}")
    print()
    
    # Wait for background thread
    print(f"⏳ Waiting 3 seconds for email to send in background...")
    time.sleep(3)

print("\n" + "="*80)
print(" " * 25 + "✅ COMPLETE")
print("="*80)

print(f"\n📬 Check Your Email:")
print(f"   Email address: {test_email}")
print(f"   From: ganeshraut.contact@gmail.com")
print(f"   Subject: Your OTP Code - AI Stock Market Prediction")
print(f"   OTP: {otp_code}")
print()

print(f"📍 Check These Folders:")
print(f"   1. Inbox")
print(f"   2. Spam/Junk")
print(f"   3. Promotions")
print(f"   4. Updates")
print()

print(f"⏰ Timing:")
print(f"   Typical delivery: 1-2 minutes")
print(f"   Maximum wait: 5 minutes")
print()

print(f"🔍 Verify Gmail Settings:")
print(f"   1. App-specific password is set (not Gmail password)")
print(f"   2. Gmail IMAP is enabled")
print(f"   3. Less secure apps is OFF")
print()

print(f"🆘 If still not received:")
print(f"   https://myaccount.google.com/apppasswords")
print(f"   Generate new app password and update .env")
print()

print("="*80 + "\n")
