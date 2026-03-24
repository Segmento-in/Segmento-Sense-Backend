"""
Email Service Module
====================

Handles email sending functionality for the Segmento Sense platform.
This module provides a clean interface for sending welcome emails and other
email notifications via SMTP.

Author: Segmento Team
"""

import os
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content


class EmailService:
    """
    Email service class for sending emails via SMTP.
    Reads configuration from environment variables.
    """
    
    def __init__(self):
        """Initialize email service with SendGrid API configuration from environment."""
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "info@segmento.in")
        
        # Validate configuration
        if not self.sendgrid_api_key:
            print("⚠️  WARNING: SendGrid API key not configured in environment variables")
            print("   Set SENDGRID_API_KEY to enable email sending")
        if not self.from_email:
            print("⚠️  WARNING: FROM_EMAIL not configured, using default")
    
    def is_configured(self) -> bool:
        """Check if SendGrid API key is properly configured."""
        return bool(self.sendgrid_api_key)
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Send an email using SendGrid HTTP API.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML version of the email
            text_body: Plain text version (optional)
        
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured():
            print("❌ Cannot send email: SendGrid API key not configured")
            return False
        
        try:
            # Create SendGrid email message
            message = Mail(
                from_email=Email(self.from_email, "Segmento Sense"),
                to_emails=To(to_email),
                subject=subject,
                plain_text_content=Content("text/plain", text_body if text_body else ""),
                html_content=Content("text/html", html_body)
            )
            
            # Send via SendGrid HTTP API
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)
            
            print(f"✅ Email sent successfully to {to_email} (Status: {response.status_code})")
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
