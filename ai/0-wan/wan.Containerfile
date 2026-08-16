FROM pytorch/pytorch:2.11.0-cuda13.0-cudnn9-devel

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /root

RUN apt update && apt install -y git
RUN git clone https://github.com/Wan-Video/Wan2.2.git

WORKDIR /root/Wan2.2

RUN TORCH_CUDA_ARCH_LIST="12.0" MAX_JOBS=20 pip install -r requirements.txt --break-system-packages --no-build-isolation

RUN pip install -r requirements_s2v.txt --break-system-packages
RUN pip install --break-system-packages decord peft onnxruntime pandas matplotlib loguru

CMD ["bash"]
