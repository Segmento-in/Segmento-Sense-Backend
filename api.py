from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
import pandas as pd
import io
import json
from backend import RegexClassifier
from email_service import send_welcome_email

# Initialize FastAPI app
app = FastAPI(
    title="Segmento Sense API",
    description="AI-powered PII Detection and Data Classification Platform",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://segmento-sense.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize the classifier
classifier = RegexClassifier()

# Maximum file size (1GB)
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB in bytes

# ==================== PYDANTIC MODELS ====================

class TextAnalysisRequest(BaseModel):
    text: str = Field(..., description="Text to analyze for PII")

class PatternAddRequest(BaseModel):
    name: str = Field(..., description="Pattern name")
    regex: str = Field(..., description="Regex pattern")

class DatabaseConnectionRequest(BaseModel):
    host: str
    port: str
    database: str
    user: str
    password: str
    table: str = Field(None, description="Table name (or collection for MongoDB)")

class S3ConnectionRequest(BaseModel):
    access_key: str
    secret_key: str
    region: str
    bucket: str = Field(None, description="Bucket name")
    file_key: str = Field(None, description="File key/path")

class AzureConnectionRequest(BaseModel):
    connection_string: str
    container: str = Field(None, description="Container name")
    blob: str = Field(None, description="Blob name")

class GCSConnectionRequest(BaseModel):
    credentials: Dict[str, Any]
    bucket: str = Field(None, description="Bucket name")
    file_name: str = Field(None, description="File name")

class GoogleDriveRequest(BaseModel):
    credentials: Dict[str, Any]
    file_id: str = Field(None, description="Drive file ID")
    mime_type: str = Field(None, description="File MIME type")

class SlackRequest(BaseModel):
    token: str
    channel_id: str

class ConfluenceRequest(BaseModel):
    url: str
    username: str
    token: str
    page_id: str

class PDFPageRequest(BaseModel):
    page_number: int = 0

class WelcomeEmailRequest(BaseModel):
    name: str = Field(..., description="User's name")
    email: EmailStr = Field(..., description="User's email address")

# ==================== HELPER FUNCTIONS ====================

def validate_file_size(file: UploadFile):
    """Validate uploaded file size"""
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()  # Get position (file size)
    file.file.seek(0)  # Reset to beginning
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size ({size} bytes) exceeds maximum allowed size (1GB)"
        )
    return size

def format_pii_response(df: pd.DataFrame, source_df: pd.DataFrame = None, text: str = None) -> Dict:
    """Format PII analysis response"""
    count_df = classifier.get_pii_counts_dataframe(df) if source_df is not None else classifier.get_pii_counts(text)
    
    response = {
        "pii_counts": count_df.fillna("").to_dict(orient="records") if not count_df.empty else [],
        "total_pii_found": int(count_df["Count"].sum()) if not count_df.empty else 0
    }
    
    # Add schema if source dataframe provided
    if source_df is not None and not source_df.empty:
        schema_df = classifier.get_data_schema(source_df)
        response["schema"] = schema_df.fillna("").to_dict(orient="records")
    
    # Add inspector results if text provided
    if text:
        inspector_df = classifier.run_full_inspection(text)
        if not inspector_df.empty:
            response["inspector"] = inspector_df.fillna("").to_dict(orient="records")
    
    return response

# ==================== FILE UPLOAD ENDPOINTS ====================

@app.post("/api/upload/csv")
async def upload_csv(file: UploadFile = File(...), mask: bool = Form(False)):
    """Upload and analyze CSV file"""
    try:
        validate_file_size(file)
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        text_sample = df.head(10).to_string()
        response = format_pii_response(df, df, text_sample)
        
        if mask:
            masked_df = classifier.mask_dataframe(df.head(50))
            response["data"] = masked_df.fillna("").to_dict(orient="records")
        else:
            highlighted_df = classifier.scan_dataframe_with_html(df.head(50))
            response["data"] = highlighted_df.fillna("").to_dict(orient="records")
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/json")
async def upload_json(file: UploadFile = File(...), mask: bool = Form(False)):
    """Upload and analyze JSON file"""
    try:
        validate_file_size(file)
        df = classifier.get_json_data(file.file)
        
        text_sample = df.head(10).to_string()
        response = format_pii_response(df, df, text_sample)
        
        if mask:
            masked_df = classifier.mask_dataframe(df.head(50))
            response["data"] = masked_df.fillna("").to_dict(orient="records")
        else:
            highlighted_df = classifier.scan_dataframe_with_html(df.head(50))
            response["data"] = highlighted_df.fillna("").to_dict(orient="records")
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/parquet")
async def upload_parquet(file: UploadFile = File(...), mask: bool = Form(False)):
    """Upload and analyze Parquet file"""
    try:
        validate_file_size(file)
        content = await file.read()
        df = classifier.get_parquet_data(content)
        
        text_sample = df.head(10).to_string()
        response = format_pii_response(df, df, text_sample)
        
        if mask:
            masked_df = classifier.mask_dataframe(df.head(50))
            response["data"] = masked_df.fillna("").to_dict(orient="records")
        else:
            highlighted_df = classifier.scan_dataframe_with_html(df.head(50))
            response["data"] = highlighted_df.fillna("").to_dict(orient="records")
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/avro")
async def upload_avro(file: UploadFile = File(...), mask: bool = Form(False)):
    """Upload and analyze Apache Avro file"""
    try:
        validate_file_size(file)
        content = await file.read()
        df = classifier.get_avro_data(content)
        
        text_sample = df.head(10).to_string()
        response = format_pii_response(df, df, text_sample)
        
        if mask:
            masked_df = classifier.mask_dataframe(df.head(50))
            response["data"] = masked_df.fillna("").to_dict(orient="records")
        else:
            highlighted_df = classifier.scan_dataframe_with_html(df.head(50))
            response["data"] = highlighted_df.fillna("").to_dict(orient="records")
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/pdf")
async def upload_pdf(file: UploadFile = File(...), page_number: int = Form(0)):
    """Upload and analyze PDF file (with pagination)"""
    try:
        validate_file_size(file)
        content = await file.read()
        
        # Get total pages and extract text from specific page
        total_pages = classifier.get_pdf_total_pages(content)
        text = classifier.get_pdf_page_text(content, page_number)
        
        # Format PII response
        response = format_pii_response(None, None, text)
        response["total_pages"] = total_pages
        response["current_page"] = page_number
        
        # Get labeled PDF image
        img = classifier.get_labeled_pdf_image(content, page_number)
        if img:
            import base64
            from PIL import Image
            
            # Check if img is already bytes or a PIL Image
            if isinstance(img, bytes):
                # Already bytes, just encode
                img_str = base64.b64encode(img).decode()
            elif isinstance(img, Image.Image):
                # PIL Image, need to convert to bytes
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
            else:
                # Unknown type, skip image
                img_str = None
            
            if img_str:
                response["image"] = f"data:image/png;base64,{img_str}"
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/image")
async def upload_image(file: UploadFile = File(...), mask: bool = Form(False)):
    """Upload and analyze image with OCR"""
    try:
        validate_file_size(file)
        content = await file.read()
        
        # Extract text via OCR
        text = classifier.get_ocr_text_from_image(content)
        
        if not text:
            raise HTTPException(status_code=400, detail="No text could be extracted from the image")
        
        df = pd.DataFrame({"Content": [text]})
        response = format_pii_response(df, df, text)
        
        if mask:
            masked_df = classifier.mask_dataframe(df)
            response["data"] = masked_df.fillna("").to_dict(orient="records")
        else:
            highlighted_df = classifier.scan_dataframe_with_html(df)
            response["data"] = highlighted_df.fillna("").to_dict(orient="records")
        
        # Return original image as base64
        import base64
        img_str = base64.b64encode(content).decode()
        response["original_image"] = f"data:image/png;base64,{img_str}"
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ANALYSIS ENDPOINTS ====================

@app.post("/api/analyze/text")
async def analyze_text(request: TextAnalysisRequest):
    """Analyze plain text for PII"""
    try:
        matches = classifier.analyze_text_hybrid(request.text)
        count_df = classifier.get_pii_counts(request.text)
        
        return JSONResponse(content={
            "matches": matches,
            "pii_counts": count_df.fillna("").to_dict(orient="records") if not count_df.empty else [],
            "total_pii_found": len(matches)
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/inspect")
async def inspect_text(request: TextAnalysisRequest):
    """Run full model inspection on text"""
    try:
        inspector_df = classifier.run_full_inspection(request.text)
        
        if inspector_df.empty:
            return JSONResponse(content={
                "inspector": [],
                "message": "No PII detected by any model"
            })
        
        return JSONResponse(content={
            "inspector": inspector_df.fillna("").to_dict(orient="records")
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mask")
async def mask_text(request: TextAnalysisRequest):
    """Mask PII in text"""
    try:
        df = pd.DataFrame({"Content": [request.text]})
        masked_df = classifier.mask_dataframe(df)
        
        return JSONResponse(content={
            "original": request.text,
            "masked": masked_df.iloc[0]["Content"]
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PATTERN MANAGEMENT ====================

@app.get("/api/patterns")
async def get_patterns():
    """Get all regex patterns"""
    try:
        patterns = classifier.list_patterns()
        return JSONResponse(content={
            "patterns": [{"name": k, "regex": v} for k, v in patterns.items()]
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/patterns")
async def add_pattern(request: PatternAddRequest):
    """Add a new regex pattern"""
    try:
        classifier.add_pattern(request.name, request.regex)
        return JSONResponse(content={
            "message": f"Pattern '{request.name}' added successfully",
            "pattern": {"name": request.name, "regex": request.regex}
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/patterns/{pattern_name}")
async def delete_pattern(pattern_name: str):
    """Remove a regex pattern"""
    try:
        classifier.remove_pattern(pattern_name)
        return JSONResponse(content={
            "message": f"Pattern '{pattern_name}' removed successfully"
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== DATABASE CONNECTORS ====================

@app.post("/api/connect/postgresql")
async def connect_postgresql(request: DatabaseConnectionRequest):
    """Connect to PostgreSQL and scan table"""
    try:
        df = classifier.get_postgres_data(
            request.host, request.port, request.database,
            request.user, request.password, request.table
        )
        
        text_sample = df.head(10).to_string()
        response = format_pii_response(df, df, text_sample)
        
        masked_df = classifier.mask_dataframe(df.head(50))
        response["data"] = masked_df.fillna("").to_dict(orient="records")
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PostgreSQL connection failed: {str(e)}")

@app.post("/api/connect/mysql")
async def connect_mysql(request: DatabaseConnectionRequest):
    """Connect to MySQL and scan table"""
    try:
        df = classifier.get_mysql_data(
            request.host, request.port, request.database,
            request.user, request.password, request.table
        )
        
        text_sample = df.head(10).to_string()
        response = format_pii_response(df, df, text_sample)
        
        masked_df = classifier.mask_dataframe(df.head(50))
        response["data"] = masked_df.fillna("").to_dict(orient="records")
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MySQL connection failed: {str(e)}")

@app.post("/api/connect/mongodb")
async def connect_mongodb(request: DatabaseConnectionRequest):
    """Connect to MongoDB and scan collection"""
    try:
        df = classifier.get_mongodb_data(
            request.host, request.port, request.database,
            request.user, request.password, request.table
        )
        
        text_sample = df.head(10).to_string()
        response = format_pii_response(df, df, text_sample)
        
        masked_df = classifier.mask_dataframe(df.head(50))
        response["data"] = masked_df.fillna("").to_dict(orient="records")
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB connection failed: {str(e)}")

# ==================== CLOUD STORAGE - AWS S3 ====================

@app.post("/api/cloud/s3/list-buckets")
async def list_s3_buckets(request: S3ConnectionRequest):
    """List S3 buckets"""
    try:
        buckets = classifier.get_s3_buckets(request.access_key, request.secret_key, request.region)
        return JSONResponse(content={"buckets": buckets})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 connection failed: {str(e)}")

@app.post("/api/cloud/s3/list-files")
async def list_s3_files(request: S3ConnectionRequest):
    """List files in S3 bucket"""
    try:
        if not request.bucket:
            raise HTTPException(status_code=400, detail="Bucket name is required")
        
        files = classifier.get_s3_files(
            request.access_key, request.secret_key, request.region, request.bucket
        )
        return JSONResponse(content={"files": files})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list S3 files: {str(e)}")

@app.post("/api/cloud/s3/scan")
async def scan_s3_file(request: S3ConnectionRequest):
    """Download and scan S3 file"""
    try:
        if not request.bucket or not request.file_key:
            raise HTTPException(status_code=400, detail="Bucket and file_key are required")
        
        content = classifier.download_s3_file(
            request.access_key, request.secret_key, request.region,
            request.bucket, request.file_key
        )
        
        # Assume CSV for now
        df = pd.read_csv(io.BytesIO(content))
        text_sample = df.head(10).to_string()
        response = format_pii_response(df, df, text_sample)
        
        masked_df = classifier.mask_dataframe(df.head(50))
        response["data"] = masked_df.fillna("").to_dict(orient="records")
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 scan failed: {str(e)}")

# ==================== CLOUD STORAGE - AZURE ====================

@app.post("/api/cloud/azure/list-containers")
async def list_azure_containers(request: AzureConnectionRequest):
    """List Azure containers"""
    try:
        containers = classifier.get_azure_containers(request.connection_string)
        return JSONResponse(content={"containers": containers})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Azure connection failed: {str(e)}")

@app.post("/api/cloud/azure/list-blobs")
async def list_azure_blobs(request: AzureConnectionRequest):
    """List blobs in Azure container"""
    try:
        if not request.container:
            raise HTTPException(status_code=400, detail="Container name is required")
        
        blobs = classifier.get_azure_blobs(request.connection_string, request.container)
        return JSONResponse(content={"blobs": blobs})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list blobs: {str(e)}")

@app.post("/api/cloud/azure/scan")
async def scan_azure_blob(request: AzureConnectionRequest):
    """Download and scan Azure blob"""
    try:
        if not request.container or not request.blob:
            raise HTTPException(status_code=400, detail="Container and blob are required")
        
        content = classifier.download_azure_blob(
            request.connection_string, request.container, request.blob
        )
        
        df = pd.read_csv(io.BytesIO(content))
        text_sample = df.head(10).to_string()
        response = format_pii_response(df, df, text_sample)
        
        masked_df = classifier.mask_dataframe(df.head(50))
        response["data"] = masked_df.fillna("").to_dict(orient="records")
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Azure scan failed: {str(e)}")

# ==================== CLOUD STORAGE - GCS ====================

@app.post("/api/cloud/gcs/list-buckets")
async def list_gcs_buckets(request: GCSConnectionRequest):
    """List GCS buckets"""
    try:
        buckets = classifier.get_gcs_buckets(request.credentials)
        return JSONResponse(content={"buckets": buckets})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GCS connection failed: {str(e)}")

@app.post("/api/cloud/gcs/list-files")
async def list_gcs_files(request: GCSConnectionRequest):
    """List files in GCS bucket"""
    try:
        if not request.bucket:
            raise HTTPException(status_code=400, detail="Bucket name is required")
        
        files = classifier.get_gcs_files(request.credentials, request.bucket)
        return JSONResponse(content={"files": files})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list GCS files: {str(e)}")

@app.post("/api/cloud/gcs/scan")
async def scan_gcs_file(request: GCSConnectionRequest):
    """Download and scan GCS file"""
    try:
        if not request.bucket or not request.file_name:
            raise HTTPException(status_code=400, detail="Bucket and file_name are required")
        
        content = classifier.download_gcs_file(
            request.credentials, request.bucket, request.file_name
        )
        
        df = pd.read_csv(io.BytesIO(content))
        text_sample = df.head(10).to_string()
        response = format_pii_response(df, df, text_sample)
        
        masked_df = classifier.mask_dataframe(df.head(50))
        response["data"] = masked_df.fillna("").to_dict(orient="records")
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GCS scan failed: {str(e)}")

# ==================== CLOUD STORAGE - GOOGLE DRIVE ====================

@app.post("/api/cloud/drive/list-files")
async def list_drive_files(request: GoogleDriveRequest):
    """List Google Drive files"""
    try:
        files = classifier.get_google_drive_files(request.credentials)
        return JSONResponse(content={"files": files})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Drive connection failed: {str(e)}")

@app.post("/api/cloud/drive/scan")
async def scan_drive_file(request: GoogleDriveRequest):
    """Download and scan Google Drive file"""
    try:
        if not request.file_id or not request.mime_type:
            raise HTTPException(status_code=400, detail="file_id and mime_type are required")
        
        content = classifier.download_drive_file(
            request.file_id, request.mime_type, request.credentials
        )
        
        if isinstance(content, bytes):
            try:
                text = content.decode('utf-8')
                df = pd.DataFrame({"Content": [text]})
                
                response = format_pii_response(df, df, text)
                highlighted_df = classifier.scan_dataframe_with_html(df)
                response["data"] = highlighted_df.fillna("").to_dict(orient="records")
                
                return JSONResponse(content=response)
            except:
                raise HTTPException(status_code=400, detail="Binary file cannot be processed")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Drive scan failed: {str(e)}")

# ==================== ENTERPRISE CONNECTORS ====================

@app.post("/api/enterprise/gmail")
async def scan_gmail(file: UploadFile = File(...), num_emails: int = Form(10)):
    """Scan Gmail messages"""
    try:
        df = classifier.get_gmail_data(file.file, num_emails)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="No emails fetched")
        
        text_sample = df.iloc[0]['Content']
        response = format_pii_response(df, df, text_sample)
        
        masked_df = classifier.mask_dataframe(df)
        response["data"] = masked_df.fillna("").to_dict(orient="records")
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gmail scan failed: {str(e)}")

@app.post("/api/enterprise/slack")
async def scan_slack(request: SlackRequest):
    """Scan Slack messages"""
    try:
        df = classifier.get_slack_messages(request.token, request.channel_id)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="No messages found or authentication failed")
        
        text_sample = df.iloc[0]['Content']
        response = format_pii_response(df, df, text_sample)
        
        masked_df = classifier.mask_dataframe(df)
        response["data"] = masked_df.fillna("").to_dict(orient="records")
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Slack scan failed: {str(e)}")

@app.post("/api/enterprise/confluence")
async def scan_confluence(request: ConfluenceRequest):
    """Scan Confluence page"""
    try:
        df = classifier.get_confluence_page(
            request.url, request.username, request.token, request.page_id
        )
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Failed to fetch page")
        
        text_sample = df.iloc[0]['Content']
        response = format_pii_response(df, df, text_sample)
        
        highlighted_df = classifier.scan_dataframe_with_html(df)
        response["data"] = highlighted_df.fillna("").to_dict(orient="records")
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Confluence scan failed: {str(e)}")

# ==================== EMAIL FUNCTIONALITY ====================

@app.post("/api/send-welcome")
async def send_welcome(request: WelcomeEmailRequest):
    """
    Send a welcome email to a new user.
    This endpoint is called by the frontend after a user submits the contact form.
    """
    try:
        # Send the welcome email
        success = send_welcome_email(request.name, request.email)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": f"Welcome email sent to {request.email}"
            })
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send welcome email. SMTP configuration may be missing."
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Email sending failed: {str(e)}"
        )

# ==================== HEALTH CHECK ====================

@app.get("/")
async def root():
    """API health check"""
    return {
        "message": "Segmento Sense API",
        "status": "operational",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "classifiers": {
            "regex": True,
            "nltk": True,
            "spacy": True,
            "presidio": True,
            "gliner": True,
            "deberta": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)  # HuggingFace Spaces default port