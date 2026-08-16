FROM ubuntu:24.04

RUN apt update -y && apt install -y git build-essential cmake libcurl4-openssl-dev python3 python3-pip ninja-build vim && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone --depth 1 --branch b6689 https://github.com/ggml-org/llama.cpp.git

WORKDIR /build/llama.cpp
RUN cmake -DLLAMA_BUILD_SERVER=ON -DLLAMA_MAX_CONTEXT=32768 -S . -B build && \
    cmake --build build --config Release -j$(nproc) --target llama-server && \
    cp ./build/bin/llama-* /bin/

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --break-system-packages

COPY ./src ./src

COPY models.json .

ENTRYPOINT ["python3", "/app/src/server.py"]
