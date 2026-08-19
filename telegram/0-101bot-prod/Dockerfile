FROM python:latest

RUN useradd --uid 1000 --create-home --shell /usr/sbin/nologin appuser

WORKDIR /usr/src/app

COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./main.py ./
CMD [ "python", "./main.py" ]