FROM python:3.10-slim

WORKDIR /app

# Install system deps for lxml build (if wheel not available)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libxml2-dev libxslt-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cleanup build deps
RUN apt-get purge -y --auto-remove gcc

# Download NLTK data
RUN python3 -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('averaged_perceptron_tagger', quiet=True); nltk.download('stopwords', quiet=True)"

COPY backend/ ./backend/
COPY frontend/ ./frontend/

ENV PORT=10000
EXPOSE 10000

CMD python3 -m uvicorn backend.server:app --host 0.0.0.0 --port $PORT
