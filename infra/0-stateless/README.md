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

xsltproc vm.xsl vm.xml > /tmp/vm.xml
virsh define /tmp/vm.xml
virsh dumpxml nixos-r8
virsh start nixos-r8
virsh destroy nixos-r8
virsh undefine nixos-r8 --nvram

apt install wireguard-tools
wg-quick up ./wg0.conf
ufw allow 2026/udp

ip addr add 10.67.69.2/24 dev eth0
ip route add 10.67.69.1/32 dev eth0

## Learnings

Memory can be encrypted with TSME, but it hurts perf
Numa, prefetcher, cpu timings, ram timings, boot guard
UMAF inspect

## Ideas

Make host ssh not respond on wg0 :22
Port forwarding

Template nodes
Sysrq sillswitch for VM: echo o > /proc/sysrq-trigger
Check it is --outbound-if4 wg0 --outbound-if6 wg0 Not -i wg0
Harden with --no-map-gw --map-host-loopback none
Better hash algo: mkpasswd -m yescrypt -R 11
nvidia-smi conf-compute -q
USB mouse passthrough to VM
TPM SSH & VPN key handling
Lightweight repo and nix build github:owner/repo
