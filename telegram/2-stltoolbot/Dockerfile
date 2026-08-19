FROM ubuntu:22.04

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

RUN apt update
RUN apt install -y blender python3 python3-pip

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY ./src/ ./
CMD ["blender", "--background", "--python", "bot.py"]
