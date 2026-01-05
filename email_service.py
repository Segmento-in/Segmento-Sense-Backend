"""
Email Service Module
====================

Handles email sending functionality for the Segmento Sense platform.
This module provides a clean interface for sending welcome emails and other
email notifications via SMTP.

Author: Segmento Team
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional


class EmailService:
    """
    Email service class for sending emails via SMTP.
    Reads configuration from environment variables.
    """
    
    def __init__(self):
        """Initialize email service with SMTP configuration from environment."""
        self.smtp_email = os.getenv("SMTP_EMAIL")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        
        # Validate configuration
        if not self.smtp_email or not self.smtp_password:
            print("⚠️  WARNING: SMTP credentials not configured in environment variables")
            print("   Set SMTP_EMAIL and SMTP_PASSWORD to enable email sending")
    
    def is_configured(self) -> bool:
        """Check if SMTP credentials are properly configured."""
        return bool(self.smtp_email and self.smtp_password)
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Send an email with both HTML and plain text versions.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML version of the email
            text_body: Plain text version (optional, will strip HTML if not provided)
        
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured():
            print("❌ Cannot send email: SMTP credentials not configured")
            return False
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"Segmento Sense <{self.smtp_email}>"
            message["To"] = to_email
            
            # Attach plain text version
            if text_body:
                part1 = MIMEText(text_body, "plain")
                message.attach(part1)
            
            # Attach HTML version
            part2 = MIMEText(html_body, "html")
            message.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Enable TLS encryption
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(message)
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_welcome_email(self, name: str, email: str) -> bool:
        """
        Send a welcome email to a new user.
        
        Args:
            name: User's name
            email: User's email address
        
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "Welcome to Segmento Sense - Your PII Detection Platform"
        
        # HTML email body with professional styling
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9fafb;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #666;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Segmento Sense!</h1>
                </div>
                <div class="content">
                    <p>Hi {name},</p>
                    
                    <p>Thank you for reaching out to us! We're excited to help you protect sensitive data with our AI-powered PII detection platform.</p>
                    
                    <p>Our team has received your message and will get back to you within 24 hours with:</p>
                    <ul>
                        <li>Answers to your questions</li>
                        <li>A personalized demo of our platform</li>
                        <li>Information about pricing and features</li>
                    </ul>
                    
                    <p>In the meantime, feel free to explore our platform and see how Segmento Sense can help you:</p>
                    <ul>
                        <li>Detect SSNs, credit cards, emails, and 50+ PII types</li>
                        <li>Scan databases, cloud storage, and enterprise apps</li>
                        <li>Mask sensitive data in real-time</li>
                        <li>Stay compliant with GDPR, HIPAA, and more</li>
                    </ul>
                    
                    <a href="https://segmento-sense.vercel.app" class="button">Explore Segmento Sense</a>
                    
                    <p style="margin-top: 30px;">If you have any urgent questions, feel free to reply to this email or call us at +91 990 872 7027.</p>
                    
                    <p>Best regards,<br>
                    <strong>The Segmento Sense Team</strong></p>
                </div>
                <div class="footer">
                    <p>Segmento Sense - AI-Powered PII Detection Platform</p>
                    <p>Aathidyam Restaurant, Rama Talkies Opposite Road, Waltair Uplands, Visakhapatnam</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version as fallback
        text_body = f"""
        Hi {name},
        
        Thank you for reaching out to Segmento Sense!
        
        We've received your message and will get back to you within 24 hours.
        
        Our AI-powered PII detection platform helps you:
        - Detect 50+ types of sensitive data
        - Scan databases, cloud storage, and enterprise apps
        - Mask sensitive data in real-time
        - Stay compliant with GDPR, HIPAA, and more
        
        Visit us at: https://segmento-sense.vercel.app
        
        Best regards,
        The Segmento Sense Team
        """
        
        return self.send_email(email, subject, html_body, text_body)


# Global email service instance
_email_service = None


def get_email_service() -> EmailService:
    """
    Get the global email service instance (singleton pattern).
    
    Returns:
        EmailService instance
    """
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


# Convenience function for quick access
def send_welcome_email(name: str, email: str) -> bool:
    """
    Send a welcome email to a new user (convenience function).
    
    Args:
        name: User's name
        email: User's email address
    
    Returns:
        True if email sent successfully, False otherwise
    """
    service = get_email_service()
    return service.send_welcome_email(name, email)
