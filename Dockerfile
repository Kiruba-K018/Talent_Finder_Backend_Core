
FROM python:3.12-slim

WORKDIR /app

# Upgrade pip, setuptools, and wheel before installing requirements
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements file
COPY requirements.txt ./

# Install Python dependencies (psycopg needs libpq-dev to be installed first)
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from chromadb.utils import embedding_functions; embedding_functions.DefaultEmbeddingFunction()"

# Copy application source code
COPY src/ ./src/
COPY chroma_data/ ./chroma_data/

# Copy environment file if it exists
COPY .env* ./

# Expose port for FastAPI
EXPOSE 8000

# Set environment variable to prevent buffering
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "-m", "uvicorn", "src.api.rest.app:app", "--host", "0.0.0.0", "--port", "8000","--reload", "--workers", "4"]
