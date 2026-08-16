# Home AI Box

## Commands

ssh-keygen -R 192.168.1.28
ssh root@192.168.1.28
ssh -J root@192.168.1.28 root@127.0.0.1 -p 2222

nix build
mkdir /root/mnt
mount /dev/sde1 /root/mnt
df -h /root/mnt
cd /root/mnt/EFI/BOOT/
mv BOOTX64.efi "$(date '+%Y-%m-%d_%H-%M-%S')_BOOTX64.efi"
cp /root/result/*-BOOTX64.efi /root/mnt/EFI/BOOT/BOOTX64.efi
sync
umount /root/mnt
reboot now

cat /etc/nixos/flake.nix > flake.nix
nix build .#vm

nixos-rebuild switch --flake .#stateless

virsh define /ssd/vm/nixos.xml
virsh dumpxml nixos
virsh undefine nixos --nvram

apt install wireguard-tools
wg-quick up ./wg0.conf
ufw allow 2026/udp

python3 vm.py --cpu 64 --ram 128 --kernel /ssd/vm/r8-rc2-vm-nv-pod-su-BOOTX64.efi --net wg-hermes --ui --gpu --ssh 2222 --ro /ssd/internet --rw /ssd/vm/containers

mount -t virtiofs /ssd/internet /ssd/internet
mount -t virtiofs /ssd/vm/containers /var/lib/containers

## Learnings

Memory can be encrypted with TSME, but it hurts perf
Numa, prefetcher, cpu timings, ram timings, boot guard
UMAF inspect

## Ideas

Reusable EFI target, only params do change

Template nodes
Template generation/json input
Folder path diff src dst

Sysrq sillswitch for VM: echo o > /proc/sysrq-trigger
Check it is --outbound-if4 wg0 --outbound-if6 wg0 Not -i wg0
Harden with --no-map-gw --map-host-loopback none
Better hash algo: mkpasswd -m yescrypt -R 11
nvidia-smi conf-compute -q
USB mouse passthrough to VM
TPM SSH & VPN key handling
Lightweight repo and nix build github:owner/repo
