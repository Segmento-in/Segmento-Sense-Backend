"""
Email Service Usage Examples
=============================

This file demonstrates how to use the email_service module
in your Python code.
"""

from email_service import EmailService, get_email_service, send_welcome_email


# ==================== Example 1: Quick Welcome Email ====================
def example_quick_welcome():
    """Send a welcome email using the convenience function"""
    
    # This is the simplest way - just import and call
    success = send_welcome_email("John Doe", "john@example.com")
    
    if success:
        print("✅ Welcome email sent!")
    else:
        print("❌ Failed to send email")


# ==================== Example 2: Using the Service Instance ====================
def example_using_service():
    """Use the EmailService instance for more control"""
    
    # Get the global email service instance
    email_service = get_email_service()
    
    # Check if SMTP is configured
    if not email_service.is_configured():
        print("⚠️  SMTP not configured. Set environment variables:")
        print("   SMTP_EMAIL, SMTP_PASSWORD, SMTP_HOST, SMTP_PORT")
        return
    
    # Send welcome email
    success = email_service.send_welcome_email("Jane Smith", "jane@example.com")
    print(f"Email sent: {success}")


# ==================== Example 3: Custom Email ====================
def example_custom_email():
    """Send a custom email with your own content"""
    
    email_service = get_email_service()
    
    # Custom email content
    subject = "Your Report is Ready"
    html_body = """
    <html>
    <body style="font-family: Arial;">
        <h2>Your PII Scan Report</h2>
        <p>Hi there,</p>
        <p>Your data scan has been completed. Here are the results:</p>
        <ul>
            <li>Total records scanned: 1,000</li>
            <li>PII instances found: 45</li>
            <li>Compliance score: 92%</li>
        </ul>
        <p>Download your full report here: <a href="#">View Report</a></p>
    </body>
    </html>
    """
    
    text_body = """
    Your PII Scan Report
    
    Hi there,
    
    Your data scan has been completed. Here are the results:
    - Total records scanned: 1,000
    - PII instances found: 45
    - Compliance score: 92%
    
    Download your full report at: https://example.com/report
    """
    
    success = email_service.send_email(
        to_email="customer@example.com",
        subject=subject,
        html_body=html_body,
        text_body=text_body
    )
    
    print(f"Custom email sent: {success}")


# ==================== Example 4: Create Your Own Service ====================
def example_custom_service():
    """Create a new EmailService instance with custom config"""
    
    # You can also create your own instance
    # (though using the global instance is recommended)
    custom_service = EmailService()
    
    # The service automatically reads from environment variables
    # But you can check configuration
    if custom_service.is_configured():
        print(f"✅ Email configured: {custom_service.smtp_email}")
        print(f"   SMTP Host: {custom_service.smtp_host}:{custom_service.smtp_port}")
    else:
        print("❌ Email not configured")


# ==================== Example 5: Using in FastAPI ====================
def example_fastapi_endpoint():
    """Example of how it's used in api.py"""
    
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, EmailStr
    from email_service import send_welcome_email
    
    app = FastAPI()
    
    class WelcomeEmailRequest(BaseModel):
        name: str
        email: EmailStr
    
    @app.post("/send-welcome")
    async def send_welcome(request: WelcomeEmailRequest):
        """Send welcome email endpoint"""
        success = send_welcome_email(request.name, request.email)
        
        if success:
            return {"success": True, "message": f"Email sent to {request.email}"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send email"
            )


# ==================== Example 6: Batch Email Sending ====================
def example_batch_emails():
    """Send emails to multiple users"""
    
    email_service = get_email_service()
    
    # List of new users
    new_users = [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
        {"name": "Charlie", "email": "charlie@example.com"},
    ]
    
    results = []
    for user in new_users:
        success = email_service.send_welcome_email(user["name"], user["email"])
        results.append({
            "user": user["name"],
            "email": user["email"],
            "sent": success
        })
    
    # Print summary
    successful = sum(1 for r in results if r["sent"])
    print(f"✅ Sent {successful}/{len(new_users)} emails successfully")
    
    # Show failures
    failures = [r for r in results if not r["sent"]]
    if failures:
        print("❌ Failed to send to:")
        for f in failures:
            print(f"   - {f['user']} ({f['email']})")


# ==================== Run Examples ====================
if __name__ == "__main__":
    print("=" * 60)
    print("Email Service Examples")
    print("=" * 60)
    
    print("\n1. Quick Welcome Email:")
    example_quick_welcome()
    
    print("\n2. Using Service Instance:")
    example_using_service()
    
    print("\n3. Custom Email:")
    example_custom_email()
    
    print("\n4. Check Configuration:")
    example_custom_service()
    
    print("\n5. Batch Emails:")
    example_batch_emails()
