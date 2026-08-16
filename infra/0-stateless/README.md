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

# Edit CONFIG_JSON in vm.py, then define the VM
python3 vm.py

`mounts` maps each host `src` to an independent guest `dst`; `readonly` defaults to true.
`net.forwards` maps `host` to `guest` for TCP or UDP. A forward can also set `address` or `dev` to restrict the host listener.

mount -t virtiofs /ssd/internet /ssd/internet
mount -t virtiofs /var/lib/containers /var/lib/containers

## Learnings

Memory can be encrypted with TSME, but it hurts perf
Numa, prefetcher, cpu timings, ram timings, boot guard
UMAF inspect

## Ideas

Reusable EFI target, only params do change

Template nodes
Sysrq sillswitch for VM: echo o > /proc/sysrq-trigger
Check it is --outbound-if4 wg0 --outbound-if6 wg0 Not -i wg0
Harden with --no-map-gw --map-host-loopback none
Better hash algo: mkpasswd -m yescrypt -R 11
nvidia-smi conf-compute -q
USB mouse passthrough to VM
TPM SSH & VPN key handling
Lightweight repo and nix build github:owner/repo
