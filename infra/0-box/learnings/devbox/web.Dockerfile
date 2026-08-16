FROM codercom/code-server:latest

USER root

ENV DEBIAN_FRONTEND=noninteractive

RUN usermod -aG sudo coder
RUN echo "coder ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/coder

RUN apt update && apt install -y curl git vim python3-pip
RUN python3 -m pip install --break-system-packages notebook z3-solver pyrogram requests yfinance pillow pandas numpy pydantic transformers accelerate "huggingface_hub[cli,hf_xet]"

USER coder

COPY clone-monorepo.sh /home/coder/clone-monorepo.sh

RUN git config --global user.email "coder@devbox" \
 && git config --global user.name "coder" \
 && git config --global init.defaultBranch main \
 && git config --global credential.helper store
