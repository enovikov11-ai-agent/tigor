FROM ubuntu:latest
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
RUN ln -sf /dev/null /dev/tty && curl -fsSL https://openclaw.ai/install.sh | bash
COPY openclaw.json /etc/openclaw-default.json
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
RUN useradd -m -s /bin/bash node && \
    mkdir -p /home/node/.openclaw/workspace && \
    chown -R node:node /home/node
USER node
ENV HOME=/home/node
WORKDIR /home/node
CMD ["/usr/local/bin/entrypoint.sh"]