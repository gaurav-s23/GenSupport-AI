# ---- GenSupport AI Production Dockerfile ----

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required for OCR & SentenceTransformers
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "web/ui.py", "--server.port=8501", "--server.address=0.0.0.0"]
