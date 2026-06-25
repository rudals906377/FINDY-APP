FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8787
ENV FINDY_AUTH_DATABASE_PATH=/data/findy_auth.db

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY check_config.py .

RUN mkdir -p /data

EXPOSE 8787

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
