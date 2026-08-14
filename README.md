# Tigor monorepo

## Ideas

Run minimax h3

## Home AI Box

### Login

ssh-keygen -R 192.168.1.28
ssh root@192.168.1.28

### Rebuild

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

cat /etc/nixos/flake.nix > flake.nix
nix build .#vm

./vm.py --cpu 32 --ram 32 --gpu --ui --net wg0 --disk /ssd/vm/vm-pod-nv-r4.qcow2

### VM

virsh define /ssd/vm/nixos.xml
virsh dumpxml nixos
virsh undefine nixos

### Wireguard

Table = off
wg-quick up ./wg0.conf

### Learnings

Memory can be encrypted with TSME, but it hurts perf
Numa, prefetcher, cpu timings, ram timings, boot guard
UMAF inspect

### Ideas

Permanent SSH keys
Disable sudo flag
Produce wg0.conf pair
SEV-ES
Add docker images to vm pkgs.dockerTools.pullImage
Sysrq sillswitch for VM: echo o > /proc/sysrq-trigger
Check it is --outbound-if4 wg0 --outbound-if6 wg0 Not -i wg0
Harden with --no-map-gw --map-host-loopback none
Better hash algo: mkpasswd -m yescrypt -R 11
USB mouse passthrough to VM
nvidia-smi conf-compute -q
