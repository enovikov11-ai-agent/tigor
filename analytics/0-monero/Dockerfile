FROM ubuntu:24.04

RUN apt update

RUN apt install -y git build-essential cmake libuv1-dev libssl-dev libhwloc-dev python3

RUN git clone https://github.com/xmrig/xmrig

RUN mkdir xmrig/build && cd xmrig/build && cmake .. && make -j$(nproc)

CMD ["sleep", "infinity"]
