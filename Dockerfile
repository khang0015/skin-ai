FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        libpq5 \
        libsm6 \
        libxext6 \
        openssh-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
