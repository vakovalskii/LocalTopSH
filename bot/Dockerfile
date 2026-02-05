# LocalTopSH Telegram Bot - Python/aiogram
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY *.py ./
COPY *.json ./

CMD ["python", "-u", "main.py"]
