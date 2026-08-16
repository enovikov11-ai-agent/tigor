FROM pytorch/pytorch:2.11.0-cuda13.0-cudnn9-runtime

ARG DEBIAN_FRONTEND=noninteractive
ARG COMFY_REF=master

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone --depth 1 --branch "${COMFY_REF}" https://github.com/Comfy-Org/ComfyUI.git ComfyUI

WORKDIR /opt/ComfyUI
RUN python -m pip install --upgrade pip setuptools wheel --break-system-packages
RUN python -m pip install -r requirements.txt --break-system-packages
RUN mkdir -p /data/models /data/output /data/input /data/user /data/custom_nodes

EXPOSE 8188
VOLUME ["/data"]

CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188", "--base-directory", "/data"]
