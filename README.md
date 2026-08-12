# tigor
Personal public monorepo

# etc

Minimax h3

mkpasswd -m yescrypt -R 11

ssh-keygen -R 192.168.1.28
ssh root@192.168.1.28

mkdir /root/mnt
mount /dev/sde1 /root/mnt
cd /root/mnt/EFI/BOOT/
mv BOOTX64.efi 2026-08-12_stateless-r1_BOOTX64.efi
cp /root/result/BOOTX64.efi /root/mnt/EFI/BOOT/
sync
cd ~
umount /root/mnt
reboot now
