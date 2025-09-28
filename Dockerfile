FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Rust for bcrypt compilation
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy shared package and dependencies
COPY auth_shared/ ./auth_shared/
COPY requirements.txt .

# Install bcrypt first to avoid conflicts
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir bcrypt==4.0.1 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
