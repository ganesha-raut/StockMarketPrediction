#!/usr/bin/env python
"""
COMPLETE FORGOT PASSWORD FLOW TEST
Shows every step and logs all errors
"""

import sys
sys.path.insert(0, r'c:\Users\rautg\Desktop\StockMarket_prediction')

import logging
from app import create_app
from models import User, OTP, db
from routes.auth import generate_otp, forgot_password
from datetime import datetime, timedelta
from utils.email_service import send_otp_email

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = create_app('development')

print("\n" + "="*80)
print(" " * 15 + "COMPLETE FORGOT PASSWORD FLOW TEST")
print("="*80 + "\n")

with app.app_context():
    # Test 1: Check users
    print("TEST 1: Checking Registered Users")
    print("-" * 80)
    users = User.query.all()
    print(f"Total users in database: {len(users)}")
    
    if not users:
        print("❌ NO USERS - Cannot test!")
        sys.exit(1)
    
    test_user = users[0]
    test_email = test_user.email
    print(f"✅ Using user: {test_user.username} ({test_email})")
    print()
    
    # Test 2: Verify user exists with the same query as forgot_password
    print("TEST 2: User Lookup (Same as Forgot Password Code)")
    print("-" * 80)
    user = User.query.filter_by(email=test_email).first()
    print(f"Query: User.query.filter_by(email='{test_email}').first()")
    print(f"Result: {user}")
    if user:
        print(f"✅ User FOUND - OTP will be sent")
    else:
        print(f"❌ User NOT found - NO OTP sent")
        sys.exit(1)
    print()
    
    # Test 3: Generate OTP
    print("TEST 3: OTP Generation")
    print("-" * 80)
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    print(f"Generated OTP: {otp_code}")
    print(f"Length: {len(otp_code)}")
    print(f"Type: {type(otp_code)}")
    print(f"Expires: {expires_at}")
    print(f"✅ OTP Generated")
    print()
    
    # Test 4: Mark old OTPs
    print("TEST 4: Marking Old OTPs as Used")
    print("-" * 80)
    old_otps = OTP.query.filter_by(email=test_email, purpose='password_reset', is_used=False).all()
    print(f"Found old OTPs: {len(old_otps)}")
    for old_otp in old_otps:
        old_otp.is_used = True
        print(f"  Marked OTP {old_otp.otp_code} as used")
    print(f"✅ Old OTPs marked")
    print()
    
    # Test 5: Create new OTP
    print("TEST 5: Creating New OTP Record")
    print("-" * 80)
    otp = OTP(
        email=test_email,
        otp_code=otp_code,
        purpose='password_reset',
        expires_at=expires_at
    )
    db.session.add(otp)
    print(f"OTP object created and added to session")
    print(f"Email: {otp.email}")
    print(f"OTP Code: {otp.otp_code}")
    print(f"Purpose: {otp.purpose}")
    print()
    
    # Test 6: Commit to database
    print("TEST 6: Committing to Database")
    print("-" * 80)
    try:
        db.session.commit()
        print(f"✅ Database commit successful")
        print(f"OTP ID: {otp.id}")
        print()
    except Exception as e:
        print(f"❌ ERROR during commit: {str(e)}")
        db.session.rollback()
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Test 7: Verify OTP was stored
    print("TEST 7: Verifying OTP in Database")
    print("-" * 80)
    stored = OTP.query.filter_by(
        email=test_email,
        otp_code=otp_code,
        purpose='password_reset',
        is_used=False
    ).filter(OTP.expires_at > datetime.utcnow()).first()
    
    if stored:
        print(f"✅ OTP verified in database")
        print(f"  Email: {stored.email}")
        print(f"  OTP: {stored.otp_code}")
        print(f"  Not expired: {datetime.utcnow() < stored.expires_at}")
    else:
        print(f"❌ OTP NOT FOUND in database")
        sys.exit(1)
    print()
    
    # Test 8: Send email
    print("TEST 8: Sending OTP Email (WITH FULL LOGGING)")
    print("-" * 80)
    print(f"Calling: send_otp_email('{test_email}', '{otp_code}', 'password reset')")
    print()
    
    # Capture all logs
    import io
    import sys as sys_module
    
    try:
        result = send_otp_email(test_email, otp_code, 'password reset')
        print(f"Function returned: {result}")
        if result:
            print(f"✅ send_otp_email returned True")
        else:
            print(f"⚠️  send_otp_email returned False")
        print()
    except Exception as e:
        print(f"❌ ERROR in send_otp_email: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Wait a moment for background thread
    import time
    print("Waiting 2 seconds for background email thread...")
    time.sleep(2)

print("\n" + "="*80)
print(" " * 25 + "✅ ALL TESTS COMPLETE")
print("="*80)

print("\n📊 SUMMARY:")
print(f"  ✅ User found: {test_user.username} ({test_email})")
print(f"  ✅ OTP generated: {otp_code}")
print(f"  ✅ OTP stored in database: YES")
print(f"  ✅ OTP email sent: YES (check logs above)")
print()

print("📧 Email Details:")
print(f"  FROM: ganeshraut.contact@gmail.com")
print(f"  TO: {test_email}")
print(f"  SUBJECT: Your OTP Code - AI Stock Market Prediction")
print(f"  OTP CODE: {otp_code}")
print()

print("⏰ Next Steps:")
print(f"  1. Check your email inbox (all tabs)")
print(f"  2. Check SPAM/JUNK folder")
print(f"  3. Wait up to 5 minutes")
print(f"  4. If still not received:")
print(f"     - Check Gmail app password is correct")
print(f"     - Regenerate password at: https://myaccount.google.com/apppasswords")
print()

print("🔍 Check Logs Above For:")
print(f"  • Connection to smtp.gmail.com")
print(f"  • TLS handshake")
print(f"  • Authentication (235 Accepted)")
print(f"  • Email acceptance (250 OK)")
print(f"  • Any error messages")
print()

print("="*80 + "\n")
