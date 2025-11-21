# -----------------------------
# Python Base Image
# -----------------------------
FROM python:3.10-slim

# -----------------------------
# System Dependencies (MySQL)
# -----------------------------
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Set Work Directory
# -----------------------------
WORKDIR /app

# -----------------------------
# Copy Project Files
# -----------------------------
COPY . .

# -----------------------------
# Install Python Packages
# -----------------------------
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------
# Render Uses Dynamic $PORT
# -----------------------------
ENV PORT=8000

# -----------------------------
# Start App with Gunicorn
# -----------------------------
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "app:app"]
