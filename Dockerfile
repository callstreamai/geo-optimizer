FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger'); nltk.download('stopwords')"

# Copy application
COPY backend/ ./backend/
COPY frontend/ ./frontend/

EXPOSE 8081

CMD ["python3", "backend/server.py"]
