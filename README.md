# Tigor monorepo

## Ideas

Run minimax h3

## Home AI Box

### Commands

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

cat /etc/nixos/flake.nix > flake.nix
nix build .#vm

nixos-rebuild switch --flake .#stateless

virsh define /ssd/vm/nixos.xml
virsh dumpxml nixos
virsh undefine nixos --nvram

apt install wireguard-tools
wg-quick up ./wg0.conf
ufw allow 2026/udp

python3 vm.py --cpu 32 --ram 32 --disk /ssd/vm/vm-pod-nv-r6-rc1.qcow2 --net eno1 --ui --gpu --ro /ssd/internet --rw /ssd/vm/containers

mount -t virtiofs /ssd/internet /ssd/internet
mount -t virtiofs /ssd/vm/containers /var/lib/containers

### Learnings

Memory can be encrypted with TSME, but it hurts perf
Numa, prefetcher, cpu timings, ram timings, boot guard
UMAF inspect

### Ideas

Virtiofs automount
VM EFI UKI -kernel
Flag for <portForward proto='tcp'><range start='2222' to='22'/></portForward>
Sudo flag, password param
Set 450W nvidia limit in VM
Add SEV-ES attestation and key wrapping
Add file sharing via --ro and --rw
Check should I downgrade Linux kernel and is it using latest due to ZFS https://wiki.nixos.org/wiki/ZFS
Build nix with github URL as a source
Check do ZFS checks and guarantees integrity
Permanent SSH keys
Disable sudo flag
Produce wg0.conf pair
Add docker images to vm pkgs.dockerTools.pullImage
Sysrq sillswitch for VM: echo o > /proc/sysrq-trigger
Check it is --outbound-if4 wg0 --outbound-if6 wg0 Not -i wg0
Harden with --no-map-gw --map-host-loopback none
Better hash algo: mkpasswd -m yescrypt -R 11
USB mouse passthrough to VM
nvidia-smi conf-compute -q
