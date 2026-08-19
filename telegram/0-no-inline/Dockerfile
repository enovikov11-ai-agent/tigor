FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY main.py .

RUN pip install --no-cache-dir "python-telegram-bot[http2]==22.4"

CMD ["python", "main.py"]
