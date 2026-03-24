---
title: Sense Backend
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Backend Module Structure


## 📁 Directory Organization

```
backend/
├── api.py                      # FastAPI routes and endpoints
├── app.py                      # Application entry point
├── backend.py                  # RegexClassifier and PII detection
├── email_service.py            # Email sending service (NEW ✨)
├── email_service_examples.py   # Usage examples (NEW 📖)
├── requirements.txt            # Python dependencies
└── packages.txt                # Additional packages
```

---

## 🔧 Core Modules

### api.py
**Purpose**: FastAPI application with REST API endpoints

**Key Features**:
- File upload endpoints (CSV, JSON, PDF, images, etc.)
- Database connectors (PostgreSQL, MySQL, MongoDB)
- Cloud storage integrations (S3, Azure, GCS)
- Enterprise connectors (Gmail, Slack, Confluence)
- PII analysis and masking endpoints
- **Email endpoints** (`/api/send-welcome`)

**Imports**:
```python
from backend import RegexClassifier        # PII detection
from email_service import send_welcome_email  # Email sending
```

---

### backend.py
**Purpose**: Core PII detection and classification logic

**Key Features**:
- `RegexClassifier` - Pattern-based PII detection
- Multiple PII types (SSN, credit cards, emails, etc.)
- Database and file format support
- Data masking and anonymization

---

### email_service.py ✨ **NEW**
**Purpose**: Standalone email service module

**Key Features**:
- `EmailService` class for sending emails via SMTP
- Singleton pattern via `get_email_service()`
- Welcome email template with HTML styling
- Generic `send_email()` method for custom emails
- Configuration management from environment variables

**Usage**:
```python
# Quick usage
from email_service import send_welcome_email
send_welcome_email("User Name", "user@example.com")

# Advanced usage
from email_service import get_email_service
email_service = get_email_service()
email_service.send_email(to_email, subject, html_body, text_body)
```

**Configuration** (Environment Variables):
- `SMTP_EMAIL` - Sender email address
- `SMTP_PASSWORD` - SMTP password/app password
- `SMTP_HOST` - SMTP server (default: smtp.gmail.com)
- `SMTP_PORT` - SMTP port (default: 587)

---

### email_service_examples.py 📖 **NEW**
**Purpose**: Comprehensive usage examples

**Contains 6 examples**:
1. Quick welcome email
2. Using service instance
3. Custom email
4. Configuration checking
5. FastAPI integration
6. Batch email sending

**Run examples**:
```bash
cd backend
python email_service_examples.py
```

---

### app.py
**Purpose**: Application entry point for running the API

**Usage**:
```bash
python app.py
# or
uvicorn app:app --host 0.0.0.0 --port 7860
```

---

## 🔄 Module Dependencies

```
app.py
  └── api.py
       ├── backend.py (RegexClassifier)
       └── email_service.py (send_welcome_email)
```

**Key Benefits**:
- ✅ Clean separation of concerns
- ✅ Each module has a single responsibility
- ✅ Easy to import and reuse
- ✅ Testable independently
- ✅ Follows Python best practices

---

## 📦 Email Service API

### EmailService Class

```python
class EmailService:
    def __init__(self)
        """Initialize with SMTP config from environment"""
    
    def is_configured(self) -> bool
        """Check if SMTP credentials are set"""
    
    def send_email(to_email, subject, html_body, text_body) -> bool
        """Send generic email with HTML and text versions"""
    
    def send_welcome_email(name, email) -> bool
        """Send pre-configured welcome email"""
```

### Convenience Functions

```python
def get_email_service() -> EmailService
    """Get singleton instance of EmailService"""

def send_welcome_email(name, email) -> bool
    """Quick access to send welcome email"""
```

---

## 🚀 Quick Start

### Send Welcome Email

```python
from email_service import send_welcome_email

# That's it!
success = send_welcome_email("John Doe", "john@example.com")
```

### Send Custom Email

```python
from email_service import get_email_service

service = get_email_service()
service.send_email(
    to_email="user@example.com",
    subject="Custom Subject",
    html_body="<h1>Hello!</h1>",
    text_body="Hello!"
)
```

### Use in FastAPI

```python
from fastapi import FastAPI
from email_service import send_welcome_email

app = FastAPI()

@app.post("/welcome")
async def welcome(name: str, email: str):
    success = send_welcome_email(name, email)
    return {"success": success}
```

---

## 🧪 Testing

### Test Email Service

```bash
cd backend
python -c "from email_service import send_welcome_email; send_welcome_email('Test', 'test@example.com')"
```

### Run Examples

```bash
python email_service_examples.py
```

---

## 📚 Documentation

- **[email_service.py](email_service.py)** - Module source code with docstrings
- **[email_service_examples.py](email_service_examples.py)** - Usage examples
- **[WELCOME_EMAIL_SETUP.md](../WELCOME_EMAIL_SETUP.md)** - SMTP configuration guide
- **[QUICK_START.md](../QUICK_START.md)** - Quick setup guide

---

## 🎯 Design Principles

1. **Modularity**: Each module has a single, well-defined purpose
2. **Reusability**: Email service can be used anywhere in the backend
3. **Simplicity**: Simple API with sensible defaults
4. **Configurability**: Environment-based configuration
5. **Error Handling**: Graceful failures with helpful messages
6. **Documentation**: Comprehensive docstrings and examples

---

## 🔧 Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (for email)
export SMTP_EMAIL="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"

# Run the API
python app.py
```

---

## 📞 Support

For email service setup help, see:
- [WELCOME_EMAIL_SETUP.md](../WELCOME_EMAIL_SETUP.md) - Complete setup guide
- [QUICK_START.md](../QUICK_START.md) - 5-minute quickstart
- [email_service_examples.py](email_service_examples.py) - Code examples