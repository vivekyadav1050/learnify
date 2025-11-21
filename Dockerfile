FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# DO NOT set your own PORT. Render provides it.
# ENV PORT=8000   <-- Remove this

CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "app:app"]
