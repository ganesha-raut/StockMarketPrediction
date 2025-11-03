"""
Email Notification System
Sends email alerts to users
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
import logging

logger = logging.getLogger(__name__)

class EmailNotifier:
    """Email notification handler"""
    
    def __init__(self):
        self.smtp_server = getattr(Config, 'MAIL_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(Config, 'MAIL_PORT', 587)
        self.sender_email = getattr(Config, 'MAIL_USERNAME', None)
        self.sender_password = getattr(Config, 'MAIL_PASSWORD', None)
        self.enabled = self.sender_email and self.sender_password
        
        if not self.enabled:
            logger.warning("Email notifications disabled - MAIL_USERNAME or MAIL_PASSWORD not configured")
    
    def send_email(self, to_email, subject, body, is_html=False):
        """Send email notification"""
        if not self.enabled:
            logger.warning(f"Email not sent to {to_email} - Email notifications disabled")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
