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

# WEB_PORT / PORT read by main.py for the API. APP_MODE splits one repo across two HF Spaces:
#   AISocialMediaweb Space  → leave unset or APP_MODE=web  (FastAPI)
#   AISocialAgents Space    → set APP_MODE=agents in Space Settings → Variables (worker only)
ENV HOST=0.0.0.0
ENV PORT=7860
ENV WEB_PORT=7860
ENV APP_MODE=web

CMD ["sh", "-c", "if [ \"$APP_MODE\" = \"agents\" ]; then exec python main.py agents; else exec python main.py web; fi"]
