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
# Cloud Run Defaults
# -----------------------------
ENV PORT=8080

# -----------------------------
# Expose Port
# -----------------------------
EXPOSE 8080

# -----------------------------
# Start App (Gunicorn)
# -----------------------------
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
