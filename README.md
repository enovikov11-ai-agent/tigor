# tigor
Personal public monorepo

public password hash = tradeoff between usability and security (underlying is high entropy pwd)

# etc

Minimax h3

NVIDIA GeForce GT 710
mkpasswd -m yescrypt -R 11

mkdir /root/mnt
mount /dev/sde1 /root/mnt
cd /root/mnt/EFI/BOOT/

mv BOOTX64.efi 2026-08-11_stateless_BOOTX64.efi

cp /root/result/BOOTX64.efi /root/mnt/EFI/BOOT/

ssh-keygen -R 192.168.1.28
