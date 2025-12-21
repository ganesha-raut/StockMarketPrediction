from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, OTP
from utils.email_service import send_otp_email, send_welcome_email
from datetime import datetime, timedelta
import random
import string
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def get_user_friendly_error(error):
    """Convert database and technical errors to user-friendly messages"""
    error_str = str(error).lower()
    
    if 'readonly' in error_str or 'database' in error_str:
        return 'A technical issue occurred. Please try again in a moment.'
    elif 'foreign key' in error_str:
        return 'Invalid data provided. Please check your input.'
    elif 'unique constraint' in error_str:
        return 'This email is already registered.'
    else:
        return 'An unexpected error occurred. Please try again.'

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Validation
        if not username or not email or not password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Username already taken'}), 400
        
        # Generate OTP
        otp_code = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Save OTP
        otp = OTP(
            email=email,
            otp_code=otp_code,
            purpose='registration',
            expires_at=expires_at
        )
        db.session.add(otp)
        
        # Create unverified user
        user = User(
            username=username,
            email=email,
            is_verified=False
        )
        user.set_password(password)
        db.session.add(user)
        
        db.session.commit()
        
        # Send OTP email
        send_otp_email(email, otp_code, 'registration')
        
        # Store email in session for verification
        session['pending_verification_email'] = email
        
        return jsonify({
            'success': True,
            'message': 'OTP sent to your email. Please verify.',
            'email': email
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Register error: {str(e)}")
        return jsonify({'success': False, 'message': get_user_friendly_error(e)}), 500
@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP"""
    try:
        data = request.get_json()
        email = data.get('email')
        otp_code = data.get('otp')
        
        if not email or not otp_code:
            return jsonify({'success': False, 'message': 'Email and OTP required'}), 400
        
        # Find valid OTP
        otp = OTP.query.filter_by(
            email=email,
            otp_code=otp_code,
            is_used=False
        ).filter(OTP.expires_at > datetime.utcnow()).first()
        
        if not otp:
            return jsonify({'success': False, 'message': 'Invalid or expired OTP'}), 400
        
        # Mark OTP as used
        otp.is_used = True
        
        # Verify user
        user = User.query.filter_by(email=email).first()
        if user:
            user.is_verified = True
            db.session.commit()
            
            # Send welcome email
            send_welcome_email(email, user.username)
            
            # Clear session
            session.pop('pending_verification_email', None)
            
            return jsonify({
                'success': True,
                'message': 'Email verified successfully! You can now login.'
            })
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Verify OTP error: {str(e)}")
        return jsonify({'success': False, 'message': get_user_friendly_error(e)}), 500

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email required'}), 400
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Generate new OTP
        otp_code = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Mark old OTPs as used (fetch and update individually for better error handling)
        old_otps = OTP.query.filter_by(email=email, is_used=False).all()
        for old_otp in old_otps:
            old_otp.is_used = True
        
        # Create new OTP
        otp = OTP(
            email=email,
            otp_code=otp_code,
            purpose='registration',
            expires_at=expires_at
        )
        db.session.add(otp)
        db.session.commit()
        
        # Send email
        send_otp_email(email, otp_code, 'verification')
        
        return jsonify({
            'success': True,
            'message': 'New OTP sent to your email'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Resend OTP error: {str(e)}")
        return jsonify({'success': False, 'message': get_user_friendly_error(e)}), 500

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        remember = data.get('remember', False)
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
        
        if not user.is_verified:
            return jsonify({
                'success': False,
                'message': 'Please verify your email first',
                'needs_verification': True,
                'email': email
            }), 403
        
        if not user.is_active:
            return jsonify({'success': False, 'message': 'Account is deactivated'}), 403
        
        # Login user
        login_user(user, remember=remember)
        
        # Redirect based on role
        redirect_url = url_for('admin.dashboard') if user.is_admin else url_for('user.home')
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'redirect': redirect_url,
            'is_admin': user.is_admin
        })
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'success': False, 'message': get_user_friendly_error(e)}), 500

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    return redirect(url_for('index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password - Send OTP to email"""
    if request.method == 'GET':
        return render_template('auth/forgot_password.html')
    
    try:
        logger.info("=" * 80)
        logger.info("📧 FORGOT PASSWORD REQUEST RECEIVED")
        logger.info("=" * 80)
        
        # Get request data
        data = request.get_json()
        email = data.get('email', '').strip() if data else ''
        action = data.get('action')
        
        logger.info(f"Email: {email}")
        logger.info(f"Action: {action}")
        
        if not email:
            logger.warning("❌ Email not provided")
            return jsonify({'success': False, 'message': 'Email required'}), 400
        
        # Handle OTP verification
        if action == 'verify_otp':
            logger.info(f"🔐 Verifying OTP for {email}")
            otp_code = data.get('otp')
            
            if not otp_code:
                logger.warning("❌ OTP code not provided")
                return jsonify({'success': False, 'message': 'OTP required'}), 400
            
            # Verify OTP
            otp = OTP.query.filter_by(
                email=email,
                otp_code=otp_code,
                purpose='password_reset',
                is_used=False
            ).filter(OTP.expires_at > datetime.utcnow()).first()
            
            if not otp:
                logger.warning(f"❌ Invalid or expired OTP for {email}")
                return jsonify({'success': False, 'message': 'Invalid or expired OTP'}), 400
            
            logger.info(f"✅ OTP verified for {email}")
            return jsonify({
                'success': True,
                'message': 'OTP verified successfully'
            })
        
        # ========== SEND OTP MODE ==========
        logger.info("🔍 CHECKING IF USER EXISTS")
        logger.info(f"Looking for email: {email}")
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            logger.warning(f"❌ USER NOT FOUND: {email}")
            return jsonify({
                'success': False,
                'message': 'This email is not registered. Please sign up first.'
            }), 404
        
        logger.info(f"✅ USER FOUND: {email} (ID: {user.id})")
        
        # ========== GENERATE OTP ==========
        logger.info("🎲 GENERATING OTP")
        otp_code = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        logger.info(f"Generated OTP: {otp_code}")
        logger.info(f"Expires: {expires_at}")
        
        # ========== MARK OLD OTPs ==========
        logger.info("🔄 MARKING OLD OTPs AS USED")
        old_otps = OTP.query.filter_by(email=email, purpose='password_reset', is_used=False).all()
        logger.info(f"Found {len(old_otps)} old OTPs")
        for old_otp in old_otps:
            old_otp.is_used = True
        
        # ========== CREATE NEW OTP ==========
        logger.info("💾 CREATING NEW OTP RECORD")
        otp = OTP(
            email=email,
            otp_code=otp_code,
            purpose='password_reset',
            expires_at=expires_at
        )
        db.session.add(otp)
        
        # ========== COMMIT TO DATABASE ==========
        logger.info("💾 COMMITTING TO DATABASE")
        try:
            db.session.commit()
            logger.info(f"✅ OTP COMMITTED: ID={otp.id}")
        except Exception as db_error:
            logger.error(f"❌ DATABASE ERROR: {str(db_error)}")
            db.session.rollback()
            raise db_error
        
        # ========== SEND EMAIL ==========
        logger.info("📧 SENDING EMAIL")
        logger.info(f"To: {email}")
        logger.info(f"OTP: {otp_code}")
        
        try:
            result = send_otp_email(email, otp_code, 'password reset')
            logger.info(f"✅ EMAIL SENT: {result}")
        except Exception as email_error:
            logger.error(f"❌ EMAIL ERROR: {str(email_error)}")
            import traceback
            logger.error(traceback.format_exc())
            raise email_error
        
        # ========== SUCCESS ==========
        logger.info("=" * 80)
        logger.info("✅ FORGOT PASSWORD COMPLETE")
        logger.info("=" * 80)
        
        return jsonify({
            'success': True,
            'message': 'Password reset OTP sent to your email',
            'email': email
        })
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ FORGOT PASSWORD ERROR")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        db.session.rollback()
        
        return jsonify({
            'success': False,
            'message': get_user_friendly_error(e),
            'error': str(e)  # Include error for debugging
        }), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with OTP"""
    try:
        data = request.get_json()
        email = data.get('email')
        otp_code = data.get('otp')
        new_password = data.get('password')
        
        if not email or not otp_code or not new_password:
            return jsonify({'success': False, 'message': 'All fields required'}), 400
        
        # Verify OTP
        otp = OTP.query.filter_by(
            email=email,
            otp_code=otp_code,
            purpose='password_reset',
            is_used=False
        ).filter(OTP.expires_at > datetime.utcnow()).first()
        
        if not otp:
            return jsonify({'success': False, 'message': 'Invalid or expired OTP'}), 400
        
        # Update password
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user.set_password(new_password)
        otp.is_used = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password reset successful. You can now login.'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Reset password error: {str(e)}")
        return jsonify({'success': False, 'message': get_user_friendly_error(e)}), 500
