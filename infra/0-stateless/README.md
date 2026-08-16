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
nixos-rebuild switch --flake .#host

xsltproc vm.xsl vm.xml > /tmp/vm.xml
virsh define /tmp/vm.xml
virsh start hermes-r10

virsh dumpxml hermes-r10
virsh destroy hermes-r10
virsh undefine hermes-r10 --nvram

apt install wireguard-tools
ufw allow 2026/udp
wg-quick up ./wg-hermes.conf

ip addr add 10.67.69.2/24 dev eth0
ip route add 10.67.69.1/32 dev eth0

echo o > /proc/sysrq-trigger

nft flush ruleset

## Learnings

Memory can be encrypted with TSME, but it hurts perf
Numa, prefetcher, cpu timings, ram timings, boot guard
UMAF inspect

## Ideas

Console/vsock
Control plane
Template production xml+xsl in one file
Make host ssh not respond on wg0 :22
Check --outbound-if4 wg0 --outbound-if6 wg0 Not -i wg0
Check --no-map-gw --map-host-loopback present
Better hash algo: mkpasswd -m yescrypt -R 11
nvidia-smi conf-compute -q
USB mouse passthrough to VM
Pack SSH key
Lightweight repo and nix build github:owner/repo
