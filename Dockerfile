FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 7860

# Set environment variables (WEB_PORT is read by main.py if PORT is unset at runtime)
ENV HOST=0.0.0.0
ENV PORT=7860
ENV WEB_PORT=7860

# Run the application
CMD ["python", "main.py"]
