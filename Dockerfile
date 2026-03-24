# Use Python 3.11-slim (Better performance and support)
FROM python:3.11-slim


# Set working directory
WORKDIR /app

# 1. Install system dependencies
# Added 'tesseract-ocr' and 'libtesseract-dev' for OCR
# 'libgl1' and 'build-essential' for library compatibility
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Upgrade pip first
RUN pip install --upgrade pip

# 3. Copy requirements and install
COPY requirements.txt .
# Using --prefer-binary avoids compiling from source for stability
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# 4. Download AI Models (Baked into the image to speed up startup)
# Spacy Large model
RUN python -m spacy download en_core_web_lg
# NLTK Data for backend.py
RUN python -m nltk.downloader punkt punkt_tab averaged_perceptron_tagger maxent_ne_chunker words

# 5. Setup Cache Permissions for Hugging Face Transformers (DeBERTa/GLiNER)
# This prevents "Permission Denied" errors during model inference
ENV TRANSFORMERS_CACHE=/app/cache
ENV HF_HOME=/app/cache
RUN mkdir -p /app/cache && chmod 777 /app/cache

# 6. Copy the rest of the application
COPY . .

# 7. Expose the port (Hugging Face Spaces expects 7860)
EXPOSE 7860

# 8. Start FastAPI (api:app for Sense)
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
