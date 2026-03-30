FROM python:3.10-slim

WORKDIR /app

# System dependencies for lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger'); nltk.download('stopwords')"

# Copy application
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Render uses PORT env variable (default 10000)
ENV PORT=10000
EXPOSE 10000

CMD python3 -c "import uvicorn; uvicorn.run('backend.server:app', host='0.0.0.0', port=int(__import__('os').environ.get('PORT', '10000')))"
