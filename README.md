# tigor monorepo

Minimax h3
mkpasswd -m yescrypt -R 11

ssh-keygen -R 192.168.1.28
ssh root@192.168.1.28

nix build
mkdir /root/mnt
mount /dev/sde1 /root/mnt
df -h /root/mnt
cd /root/mnt/EFI/BOOT/
mv BOOTX64.efi "$(date '+%Y-%m-%d_%H-%M-%S')_BOOTX64.efi"
cp /root/result/BOOTX64.efi /root/mnt/EFI/BOOT/
sync
cd ~
umount /root/mnt
reboot now

--

add passwordless sudo
pack flake nix into EFI as well
Slow start
Mouse
Console - VM
do nvidia can be present even without gui?
net egress
fast start
