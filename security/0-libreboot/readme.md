# Libreboot

P0: Screen
P1: Keyboard, WiFi module, M2.2242 SSD
P2: RTL-SDR, RPi compute

Hardened libreboot (seagrub + keys)
Reproducible libreboot
Read tooling documentation how to manipulate data

# Build

sudo apt install -y git build-essential libpci-dev zlib1g-dev pkg-config genisoimage

git clone https://review.coreboot.org/coreboot.git
cd coreboot
cd util/ifdtool
make -j128
cp ifdtool /usr/local/bin/

ifdtool -x seabios_t480_vfsp_16mb_libgfxinit_txtmode.rom --platform sklkbl

cd lbmk/util/nvmutil
make
cp nvm /usr/local/bin/

nvm flashregion_3_gbe.bin dump
nvm flashregion_3_gbe.bin setmac

docker exec -it libreboot bash
./mk -b coreboot t480_vfsp_16mb

## Reproducible

cd /path/to/lbmk
export TZ=UTC LC_ALL=C LANG=C UMASK=022
umask 022

export SOURCE_DATE_EPOCH="$(git log -1 --pretty=%ct)"
./mk -b coreboot

# Serprog SPI

ssh-keygen -R "[10.69.42.2]:27"
ssh-keygen -R "[192.168.1.3]:27"
ssh libreboot-box

./mk -b pico-serprog

winbond 25Q128JVSQ 1827 (bios)
winbond 25Q80DVSIG 1821 (thunderbolt)

-r read.bin
-w write.bin

flashrom -p serprog:dev=/dev/cu.usbmodem1101,spispeed=16M

# Hardware

Model:        Lenovo ThinkPad T480 (20L6)
CPU:          Intel Core i7-8550U (4C/8T, 1.8–4.0 GHz)
RAM:          32 GB DDR4 (2×16 GB, 2400 MHz)
iGPU:         Intel UHD Graphics 620
Screen:       SD10N46911
Storage:      1 TB NVMe (SK hynix PC401)
Wi-Fi:        Intel 8265NGW
Ethernet:     Intel I219-V
Audio:        Intel HD Audio (PCH)
Camera:       Integrated laptop webcam
Bluetooth:    Integrated
Fingerprint:  Metallica MIS Reader
Thunderbolt:  Alpine Ridge LP (JHL6240)
USB:          USB 3.0 + USB-C/TB3
Keyboard:     ThinkPad keyboard + TrackPoint
Battery:      01AV489 + 01AV452

Daimler
1a:7c:87:7b:e3:8b

# Links

- https://libreboot.org/docs/install/t480.html
- https://libreboot.org/docs/install/nvmutil.html
- https://libreboot.org/docs/linux/grub_hardening.html
- https://www.intel.com/content/www/us/en/products/sku/122589/intel-core-i78550u-processor-8m-cache-up-to-4-00-ghz/-specifications.html
- https://www.lenovo.com/us/en/p/laptops/thinkpad/thinkpadt/thinkpad-t480/22tp2tt4800
- https://pcsupport.lenovo.com/us/en/products/laptops-and-netbooks/thinkpad-t-series-laptops/thinkpad-t480-type-20l5-20l6
- https://polovni-laptopovi.com/
- https://konovo.rs/
- https://support.lenovo.com/us/en/downloads/ds502355-bios-update-utility-bootable-cd-for-windows-10-64-bit-linux-thinkpad-t480

# nix

nix shell nixpkgs#git nixpkgs#bashInteractive --command bash

git config --global user.name "John Doe"
git config --global user.email johndoe@example.com

8BB1 F7D2 8CF7 696D BF4F 7192 5C65 4067 D383 B1FF

https://libreboot.org/docs/install/t480.html
https://libreboot.org/docs/install/ivy_has_common.html#insert-vendor-files
https://libreboot.org/docs/build/
https://libreboot.org/docs/
https://libreboot.org/docs/install/
https://libreboot.org/download.html
https://libreboot.org/docs/install/nvmutil.html
https://rsync.libreboot.org/stable/26.01rev1/
https://codeberg.org/libreboot/lbmk/commit/1cf3181537b8d1fe1df0e91681f700850a3d9bf6
https://codeberg.org/Kyronix/myLibrebootT480/src/branch/master/src/english.md
https://codeberg.org/Kyronix/myLibrebootT480/src/branch/master/src/english.md
https://rsync.libreboot.org/stable/26.01rev1/roms/libreboot-26.01rev1_t480_vfsp_16mb.tar.xz
