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

# Download NLTK data
RUN python3 -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True); nltk.download('averaged_perceptron_tagger', quiet=True); nltk.download('stopwords', quiet=True)"

# Copy application
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Render uses PORT env variable
ENV PORT=10000
EXPOSE 10000

# Simple startup 
COPY start.sh .
RUN chmod +x start.sh
CMD ["./start.sh"]
