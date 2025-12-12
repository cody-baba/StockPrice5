FROM python:3.11-slim

# Install system dependencies for building scientific packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libatlas-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY main.py .

# Run FastAPI app on Zeabur's expected port
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
