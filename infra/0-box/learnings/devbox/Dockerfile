FROM ubuntu:24.04

WORKDIR /root
RUN mkdir /run/sshd

ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y openssh-server curl git vim python3-pip
RUN python3 -m pip install --break-system-packages git+https://github.com/huggingface/diffusers
RUN python3 -m pip install --break-system-packages torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
RUN python3 -m pip install --break-system-packages notebook z3-solver pyrogram requests yfinance pillow pandas numpy pydantic transformers accelerate "huggingface_hub[cli,hf_xet]"

RUN git config --global user.email "Evgenii Novikov"
RUN git config --global user.name "enovikov11@yandex.ru"

RUN mkdir -p .ssh && chmod 700 .ssh
RUN echo "sk-ssh-ed25519@openssh.com AAAAGnNrLXNzaC1lZDI1NTE5QG9wZW5zc2guY29tAAAAIMltMQTMSIcxPbZLNCxkAT/MWRqJo1IFOfH95OoscQbCAAAABHNzaDo= enovikov11@novikov.local" > ./.ssh/authorized_keys
RUN chmod 600 .ssh/authorized_keys

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
