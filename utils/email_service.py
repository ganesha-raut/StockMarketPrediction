from flask_mail import Mail, Message
from flask import render_template, current_app
from threading import Thread

mail = Mail()

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

def send_email(subject, recipients, html_body, text_body=None):
    """Send email with HTML content"""
    try:
        app = current_app._get_current_object()
        
        msg = Message(
            subject=subject,
            recipients=recipients if isinstance(recipients, list) else [recipients],
            html=html_body,
            body=text_body or "Please view this email in HTML format."
        )
        
        # Send asynchronously
        Thread(target=send_async_email, args=(app, msg)).start()
        return True
        
    except Exception as e:
        print(f"Error preparing email: {e}")
        return False

def send_otp_email(email, otp_code, purpose="verification"):
    """Send OTP verification email"""
    subject = f"Your OTP Code - {current_app.config['APP_NAME']}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .otp-box {{ background: white; border: 2px dashed #667eea; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }}
            .otp-code {{ font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 5px; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Email Verification</h1>
            </div>
            <div class="content">
                <h2>Hello!</h2>
                <p>Your OTP code for {purpose} is:</p>
                <div class="otp-box">
                    <div class="otp-code">{otp_code}</div>
                </div>
                <p><strong>This code will expire in 10 minutes.</strong></p>
                <p>If you didn't request this code, please ignore this email.</p>
                <div class="footer">
                    <p>© 2024 {current_app.config['APP_NAME']}. All rights reserved.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(subject, email, html_body)

def send_notification_email(user_email, notification_data):
    """Send stock notification alert email"""
    stock_name = notification_data.get('stock_name', 'Stock')
    symbol = notification_data.get('symbol', '')
    notification_type = notification_data.get('type', 'ALERT')
    live_price = notification_data.get('live_price', 0)
    predicted_price = notification_data.get('predicted_price', 0)
    confidence = notification_data.get('confidence', 0)
    change_percent = notification_data.get('change_percent', 0)
    trend = notification_data.get('trend', 'neutral')
    message = notification_data.get('message', '')
    
    # Determine color based on type
    color_map = {
        'BUY': '#10b981',
        'SELL': '#ef4444',
        'DROP': '#f59e0b',
        'TARGET': '#3b82f6'
    }
    color = color_map.get(notification_type, '#667eea')
    
    # Determine icon
    icon_map = {
        'BUY': '📈',
        'SELL': '📉',
        'DROP': '⚠️',
        'TARGET': '🎯'
    }
    icon = icon_map.get(notification_type, '🔔')
    
    subject = f"{icon} [{notification_type}] {stock_name} ({symbol}) - AI Alert"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: {color}; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .alert-box {{ background: white; border-left: 4px solid {color}; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .price-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            .price-table td {{ padding: 12px; border-bottom: 1px solid #e5e7eb; }}
            .price-table td:first-child {{ font-weight: bold; color: #666; }}
            .price-table td:last-child {{ text-align: right; font-weight: bold; }}
            .recommendation {{ background: {color}; color: white; padding: 15px; text-align: center; border-radius: 8px; font-size: 18px; font-weight: bold; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            .trend-badge {{ display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
            .bullish {{ background: #d1fae5; color: #065f46; }}
            .bearish {{ background: #fee2e2; color: #991b1b; }}
            .neutral {{ background: #e5e7eb; color: #374151; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{icon} Stock Alert</h1>
                <h2>{stock_name} ({symbol})</h2>
            </div>
            <div class="content">
                <div class="alert-box">
                    <h3>🤖 AI Prediction Alert</h3>
                    <p>{message}</p>
                </div>
                
                <table class="price-table">
                    <tr>
                        <td>Live Price</td>
                        <td>₹{live_price:,.2f}</td>
                    </tr>
                    <tr>
                        <td>Predicted Price</td>
                        <td>₹{predicted_price:,.2f}</td>
                    </tr>
                    <tr>
                        <td>Change</td>
                        <td style="color: {'#10b981' if change_percent > 0 else '#ef4444'};">{change_percent:+.2f}%</td>
                    </tr>
                    <tr>
                        <td>Confidence</td>
                        <td>{confidence:.1f}%</td>
                    </tr>
                    <tr>
                        <td>Trend</td>
                        <td><span class="trend-badge {trend}">{trend.upper()}</span></td>
                    </tr>
                </table>
                
                <div class="recommendation">
                    Suggested Action: {notification_type}
                </div>
                
                <p style="color: #666; font-size: 14px; margin-top: 20px;">
                    <strong>Disclaimer:</strong> This is an AI-generated prediction and should not be considered as financial advice. 
                    Please do your own research before making any investment decisions.
                </p>
                
                <div class="footer">
                    <p>© 2024 {current_app.config['APP_NAME']}. All rights reserved.</p>
                    <p>You're receiving this because you enabled notifications for this stock.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(subject, user_email, html_body)

def send_password_reset_email(email, reset_link):
    """Send password reset email"""
    subject = f"Password Reset - {current_app.config['APP_NAME']}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔑 Password Reset Request</h1>
            </div>
            <div class="content">
                <h2>Hello!</h2>
                <p>We received a request to reset your password. Click the button below to reset it:</p>
                <div style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Password</a>
                </div>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #667eea;">{reset_link}</p>
                <p><strong>This link will expire in 1 hour.</strong></p>
                <p>If you didn't request a password reset, please ignore this email.</p>
                <div class="footer">
                    <p>© 2024 {current_app.config['APP_NAME']}. All rights reserved.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(subject, email, html_body)

def send_welcome_email(email, username):
    """Send welcome email to new users"""
    subject = f"Welcome to {current_app.config['APP_NAME']}!"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .feature {{ background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #667eea; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Welcome to AI Stock Prediction!</h1>
            </div>
            <div class="content">
                <h2>Hello {username}!</h2>
                <p>Thank you for joining our AI-powered stock market prediction platform. We're excited to help you make smarter investment decisions!</p>
                
                <h3>🚀 Get Started:</h3>
                <div class="feature">
                    <strong>📊 Live Market Data</strong><br>
                    Track real-time stock prices and market trends
                </div>
                <div class="feature">
                    <strong>🤖 AI Predictions</strong><br>
                    Get AI-powered price predictions with confidence scores
                </div>
                <div class="feature">
                    <strong>⭐ Watchlist</strong><br>
                    Create your personalized watchlist and get alerts
                </div>
                <div class="feature">
                    <strong>💬 AI Chatbot</strong><br>
                    Ask questions and get instant stock insights
                </div>
                
                <p style="margin-top: 20px;">Start exploring and make your first prediction today!</p>
                
                <div class="footer">
                    <p>© 2024 {current_app.config['APP_NAME']}. All rights reserved.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(subject, email, html_body)
