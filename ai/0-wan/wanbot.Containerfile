FROM wan

RUN pip install --break-system-packages python-telegram-bot==22.7

COPY bot.py /root/Wan2.2/bot.py

CMD ["python", "bot.py"]