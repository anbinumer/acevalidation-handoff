#!/usr/bin/env python3
"""
Email Invitation Service for RTO Validator Onboarding
Handles sending and managing validator invitation emails
"""

import os
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from datetime import datetime
import logging
from typing import Dict, Optional
import secrets
import hashlib

logger = logging.getLogger(__name__)

class InvitationService:
    """Service for sending and managing validator invitations via email"""
    
    def __init__(self, smtp_server: str = None, smtp_port: int = 587, 
                 smtp_user: str = None, smtp_password: str = None):
        # Email configuration from environment variables
        self.smtp_server = smtp_server or os.getenv('SMTP_SERVER', 'smtp.office365.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = smtp_user or os.getenv('SMTP_USER', '')
        self.smtp_password = smtp_password or os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        self.from_name = os.getenv('FROM_NAME', 'RTO Assessment Validation System')
        
        # Application configuration
        self.app_url = os.getenv('APP_URL', 'http://localhost:5001')
        self.app_name = os.getenv('APP_NAME', 'RTO Assessment Validation Tool')
    
    def send_validator_invitation(self, invitation: Dict) -> bool:
        """
        Send invitation email to a validator
        
        Args:
            invitation: Invitation details from ValidatorManager
        
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Generate secure invitation link
            invitation_token = self._generate_invitation_token(invitation)
            invitation_link = f"{self.app_url}/validator/accept-invitation?token={invitation_token}"
            
            # Create email content
            subject = f"Invitation to Join {self.app_name}"
            html_content = self._create_invitation_email_html(invitation, invitation_link)
            text_content = self._create_invitation_email_text(invitation, invitation_link)
            
            # Send email
            return self._send_email(
                to_email=invitation['email'],
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending invitation to {invitation['email']}: {e}")
            return False
    
    def send_welcome_email(self, validator_info: Dict) -> bool:
        """
        Send welcome email after validator first login
        
        Args:
            validator_info: Validator information
        
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = f"Welcome to {self.app_name}!"
            html_content = self._create_welcome_email_html(validator_info)
            text_content = self._create_welcome_email_text(validator_info)
            
            return self._send_email(
                to_email=validator_info['email'],
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending welcome email to {validator_info['email']}: {e}")
            return False
    
    def _generate_invitation_token(self, invitation: Dict) -> str:
        """Generate secure invitation token for Entra External ID"""
        # Create a secure token based on invitation details
        token_data = f"{invitation['id']}:{invitation['email']}:{invitation['invited_at']}"
        secret_key = os.getenv('SECRET_KEY', 'default-secret-key')
        
        # Generate hash
        token_hash = hashlib.sha256(f"{token_data}:{secret_key}".encode()).hexdigest()
        return f"{invitation['id']}:{token_hash[:32]}"
    
    def verify_invitation_token(self, token: str, invitation: Dict) -> bool:
        """Verify invitation token is valid"""
        try:
            invitation_id, token_hash = token.split(':', 1)
            
            if invitation_id != invitation['id']:
                return False
            
            # Regenerate expected token
            expected_token = self._generate_invitation_token(invitation)
            expected_hash = expected_token.split(':', 1)[1]
            
            return token_hash == expected_hash
            
        except Exception as e:
            logger.error(f"Error verifying invitation token: {e}")
            return False
    
    def _send_email(self, to_email: str, subject: str, html_content: str, 
                   text_content: str) -> bool:
        """Send email using SMTP"""
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured - email not sent")
            # For development, log the email content instead
            logger.info(f"EMAIL TO: {to_email}")
            logger.info(f"SUBJECT: {subject}")
            logger.info(f"CONTENT: {text_content}")
            return True  # Return True for development
        
        try:
            # Create message
            message = MimeMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = to_email
            
            # Add text and HTML parts
            text_part = MimeText(text_content, 'plain')
            html_part = MimeText(html_content, 'html')
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"Invitation email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    def _create_invitation_email_html(self, invitation: Dict, invitation_link: str) -> str:
        """Create HTML content for invitation email"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RTO Validator Invitation</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #667eea;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}
        .title {{
            color: #667eea;
            margin: 0;
        }}
        .content {{
            margin-bottom: 30px;
        }}
        .invitation-details {{
            background-color: #f8f9ff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .cta-button {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
            font-size: 1.1rem;
            text-align: center;
            margin: 20px 0;
        }}
        .footer {{
            border-top: 1px solid #ddd;
            padding-top: 20px;
            margin-top: 30px;
            font-size: 0.9rem;
            color: #666;
        }}
        .warning {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🎯</div>
            <h1 class="title">RTO Assessment Validation</h1>
            <p>You've been invited as a validator</p>
        </div>
        
        <div class="content">
            <h2>Hello!</h2>
            <p>You have been invited to join the RTO Assessment Validation system as a <strong>{invitation['role']}</strong>.</p>
            
            <div class="invitation-details">
                <h3>Invitation Details:</h3>
                <ul>
                    <li><strong>Role:</strong> {invitation['role']}</li>
                    <li><strong>Validator Type:</strong> {invitation['validator_type'].title()}</li>
                    <li><strong>Invited by:</strong> {invitation['invited_by']}</li>
                    <li><strong>Organization:</strong> RTO ID {invitation['rto_id']}</li>
                </ul>
            </div>
            
            <p>As a validator, you will help ensure the quality and compliance of assessment mappings for ASQA audits. Your expertise is valuable in maintaining educational standards.</p>
            
            <div style="text-align: center;">
                <a href="{invitation_link}" class="cta-button">Accept Invitation & Sign In</a>
            </div>
            
            <div class="warning">
                <strong>⏰ Important:</strong> This invitation expires in 7 days. Please accept it as soon as possible.
            </div>
            
            <h3>What happens next?</h3>
            <ol>
                <li>Click the "Accept Invitation" button above</li>
                <li>Sign in with your Microsoft account (personal or organizational)</li>
                <li>Complete your validator profile</li>
                <li>Start reviewing assessment mappings</li>
            </ol>
            
            <p>If you have any questions about this invitation or the validation process, please contact the administrator who invited you.</p>
        </div>
        
        <div class="footer">
            <p>This invitation was sent by {invitation['invited_by']} on {datetime.fromisoformat(invitation['invited_at']).strftime('%B %d, %Y at %I:%M %p')}.</p>
            <p>If you didn't expect this invitation, you can safely ignore this email.</p>
        </div>
    </div>
</body>
</html>
        """
    
    def _create_invitation_email_text(self, invitation: Dict, invitation_link: str) -> str:
        """Create plain text content for invitation email"""
        return f"""
RTO Assessment Validation - Validator Invitation

Hello!

You have been invited to join the RTO Assessment Validation system as a {invitation['role']}.

Invitation Details:
- Role: {invitation['role']}
- Validator Type: {invitation['validator_type'].title()}
- Invited by: {invitation['invited_by']}
- Organization: RTO ID {invitation['rto_id']}

As a validator, you will help ensure the quality and compliance of assessment mappings for ASQA audits. Your expertise is valuable in maintaining educational standards.

Accept Invitation: {invitation_link}

IMPORTANT: This invitation expires in 7 days. Please accept it as soon as possible.

What happens next?
1. Click the invitation link above
2. Sign in with your Microsoft account (personal or organizational)
3. Complete your validator profile
4. Start reviewing assessment mappings

If you have any questions about this invitation or the validation process, please contact the administrator who invited you.

---
This invitation was sent by {invitation['invited_by']} on {datetime.fromisoformat(invitation['invited_at']).strftime('%B %d, %Y at %I:%M %p')}.

If you didn't expect this invitation, you can safely ignore this email.
        """
    
    def _create_welcome_email_html(self, validator_info: Dict) -> str:
        """Create HTML content for welcome email"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to RTO Assessment Validation</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background-color: #f4f4f4;">
    <div style="max-width: 600px; margin: 0 auto; padding: 30px; background-color: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="text-align: center; border-bottom: 2px solid #667eea; padding-bottom: 20px; margin-bottom: 30px;">
            <div style="font-size: 2.5rem; margin-bottom: 10px;">🎉</div>
            <h1 style="color: #667eea; margin: 0;">Welcome to the Team!</h1>
        </div>
        
        <div style="margin-bottom: 30px;">
            <h2>Hello {validator_info.get('profile', {}).get('displayName', 'Validator')}!</h2>
            <p>Welcome to the RTO Assessment Validation system! Your account has been successfully activated.</p>
            
            <div style="background-color: #f8f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>Your Validator Profile:</h3>
                <ul>
                    <li><strong>Role:</strong> {validator_info['role']}</li>
                    <li><strong>Type:</strong> {validator_info['validator_type'].title()}</li>
                    <li><strong>Organization:</strong> RTO ID {validator_info['rto_id']}</li>
                </ul>
            </div>
            
            <p>You can now access the validation dashboard and start reviewing assessment mappings.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{self.app_url}/dashboard" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 1.1rem;">Access Dashboard</a>
            </div>
            
            <h3>Getting Started:</h3>
            <ol>
                <li>Familiarize yourself with the validation interface</li>
                <li>Review the assessment mapping guidelines</li>
                <li>Start with practice assessments if available</li>
                <li>Contact your administrator if you need assistance</li>
            </ol>
        </div>
        
        <div style="border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px; font-size: 0.9rem; color: #666;">
            <p>Thank you for joining our validation team. Your expertise helps maintain the quality of vocational education assessments.</p>
        </div>
    </div>
</body>
</html>
        """
    
    def _create_welcome_email_text(self, validator_info: Dict) -> str:
        """Create plain text content for welcome email"""
        return f"""
Welcome to RTO Assessment Validation!

Hello {validator_info.get('profile', {}).get('displayName', 'Validator')}!

Welcome to the RTO Assessment Validation system! Your account has been successfully activated.

Your Validator Profile:
- Role: {validator_info['role']}
- Type: {validator_info['validator_type'].title()}
- Organization: RTO ID {validator_info['rto_id']}

You can now access the validation dashboard and start reviewing assessment mappings.

Access Dashboard: {self.app_url}/dashboard

Getting Started:
1. Familiarize yourself with the validation interface
2. Review the assessment mapping guidelines
3. Start with practice assessments if available
4. Contact your administrator if you need assistance

Thank you for joining our validation team. Your expertise helps maintain the quality of vocational education assessments.
        """