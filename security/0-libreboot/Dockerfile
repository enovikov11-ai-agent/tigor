# docker build -t libreboot .

FROM ubuntu:24.04

ENV XBMK_THREADS=64
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Belgrade

RUN apt update
RUN apt upgrade -y
RUN apt install -y ca-certificates git curl xz-utils

USER ubuntu
WORKDIR /home/ubuntu

RUN git config --global user.name "John Doe" && git config --global user.email "johndoe@example.com"
RUN git clone https://codeberg.org/libreboot/lbmk.git

RUN curl https://rsync.libreboot.org/stable/26.01rev1/roms/libreboot-26.01rev1_t480_vfsp_16mb.tar.xz -o ./lbmk/libreboot-26.01rev1_t480_vfsp_16mb.tar.xz

USER root
WORKDIR /home/ubuntu/lbmk
RUN yes | ./mk dependencies ubuntu

USER ubuntu

#setmac "$MAC"
RUN ./mk inject libreboot-26.01rev1_t480_vfsp_16mb.tar.xz
RUN tar -xf libreboot-26.01rev1_t480_vfsp_16mb.tar.xz