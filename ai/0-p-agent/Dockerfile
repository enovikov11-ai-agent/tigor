FROM node:22-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    git \
    sudo \
    shellcheck \
    moreutils \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/cd-code opencode-ai @ai-sdk/openai-compatible

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir "python-telegram-bot[http2]==21.10" pytest

RUN useradd -m -s /bin/bash cd && echo "cd ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

RUN mkdir -p /work && chown cd:cd /work

WORKDIR /app
COPY main.py entrypoint.sh test_security.py opencode.json agent-task.sh ./
RUN chmod +x entrypoint.sh && chown -R cd:cd /app && shellcheck agent-task.sh entrypoint.sh

USER cd
ENV HOME=/home/cd

RUN mkdir -p /home/cd/.config/opencode && cp /app/opencode.json /home/cd/.config/opencode/opencode.json

ENV PYTHONUNBUFFERED=1

# Run security tests during build - build will fail if tests fail
RUN python3 -m pytest test_security.py -v

ENTRYPOINT ["/app/entrypoint.sh"]
