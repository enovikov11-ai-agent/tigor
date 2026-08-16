#!/usr/bin/env bash
set -ex

exec > >(tee -a efi-build.log) 2>&1

TAR="buildroot-2025.02.4.tar.gz"
SHA256="1ef6b74581fbe3547108950c4429c06f5ad86605aa141a7217a7169372aa3df8"

mkdir -p build
cd build

[ ! -f "$TAR" ] && wget "https://buildroot.org/downloads/$TAR"

if [ $(sha256sum "$TAR" | awk '{print $1}') != "$SHA256" ]; then
  echo "Hash mismatch!"
  exit 1
fi

rm -rf buildroot
mkdir buildroot
tar -xf "$TAR" -C ./buildroot/ --strip-components=1
cd buildroot

cp ../../linux.config ./board/pc/linux.config
cp ../../my_defconfig ./configs/my_defconfig

mkdir -p ./custom_overlay/root/.ssh

cp ../../init ./custom_overlay/init
chmod +x ./custom_overlay/init

cp ../../authorized_keys ./custom_overlay/root/.ssh/authorized_keys

make my_defconfig
make -j"$(nproc)"

cp ./output/images/bzImage ../../BOOTX64.EFI
echo "Put BOOTX64.EFI at /EFI/BOOT/ of your ESP"
