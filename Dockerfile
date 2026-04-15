FROM python:3.12-slim-bookworm

# Install system dependencies for image processing and ARM stability
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

ADD requirements.txt /

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /requirements.txt \
    && rm /requirements.txt

ADD app /app/
WORKDIR /app

EXPOSE 3000

CMD ["gunicorn", "--bind", "0.0.0.0:3000", "main:app"]