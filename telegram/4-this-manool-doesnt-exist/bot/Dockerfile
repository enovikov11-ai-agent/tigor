FROM python:3.8

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

ENV TELEGRAM_BOT_TOKEN <your_telegram_bot_token_here>

CMD ["python", "main.py"]
