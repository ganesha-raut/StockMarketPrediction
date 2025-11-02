from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, OTP
from utils.email_service import send_otp_email, send_welcome_email
from datetime import datetime, timedelta
import random
import string

auth_bp = Blueprint('auth', __name__)

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

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
        return jsonify({'success': False, 'message': str(e)}), 500

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
        return jsonify({'success': False, 'message': str(e)}), 500

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
        
        # Mark old OTPs as used
        OTP.query.filter_by(email=email, is_used=False).update({'is_used': True})
        
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
        return jsonify({'success': False, 'message': str(e)}), 500

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
        return jsonify({'success': False, 'message': str(e)}), 500

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    return redirect(url_for('index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password"""
    if request.method == 'GET':
        return render_template('auth/forgot_password.html')
    
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email required'}), 400
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            # Don't reveal if email exists
            return jsonify({
                'success': True,
                'message': 'If email exists, reset instructions have been sent'
            })
        
        # Generate OTP
        otp_code = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Mark old OTPs as used
        OTP.query.filter_by(email=email, purpose='password_reset', is_used=False).update({'is_used': True})
        
        # Create new OTP
        otp = OTP(
            email=email,
            otp_code=otp_code,
            purpose='password_reset',
            expires_at=expires_at
        )
        db.session.add(otp)
        db.session.commit()
        
        # Send email
        send_otp_email(email, otp_code, 'password reset')
        
        return jsonify({
            'success': True,
            'message': 'Password reset OTP sent to your email',
            'email': email
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

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
        return jsonify({'success': False, 'message': str(e)}), 500
