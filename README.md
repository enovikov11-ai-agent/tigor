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

cp /etc/nixos/flake.nix .
nix build .#vm

virsh define /ssd/vm/nixos.xml
virsh dumpxml nixos
virsh undefine nixos

echo o > /proc/sysrq-trigger

Table = off
wg-quick up ./wg0.conf

USB mouse passthrough to VM
Add python3, node, rust, etc
Killswitch for VM
Check it is --outbound-if4 wg0 --outbound-if6 wg0 Not -i wg0
Harden with --no-map-gw --map-host-loopback none
Passwordless sudo as a flag
