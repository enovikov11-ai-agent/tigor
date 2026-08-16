# my-little-kernel

This is a security-focused easy-auditable minimal ephermal linux distro for VM launching.  
When booted admin checks pubkey, connects to dropbear ssh by pre-configured ip.  
Mount fs using luks and btrfs, run qemu payloads.  

# setup

```
apk add lsblk sgdisk 
apk add qemu-system-x86_64
apk add bridge
apk add --no-cache kmod iproute2

modprobe zfs

sgdisk --zap-all /dev/nvme0n1
sgdisk --zap-all /dev/nvme1n1
sgdisk --zap-all /dev/nvme2n1

sgdisk -n 1:0:0 -t 1:BF00 /dev/nvme0n1
sgdisk -n 1:0:0 -t 1:BF00 /dev/nvme1n1
sgdisk -n 1:0:0 -t 1:BF00 /dev/nvme2n1

zpool create -f mypool /dev/nvme0n1p1 /dev/nvme1n1p1 /dev/nvme2n1p1

zfs set compression=lz4 mypool
zfs set atime=off mypool

zfs set mountpoint=/dev/ssd mypool

echo 'options zfs zfs_arc_max=17179869184' >> /etc/modprobe.d/zfs.conf
```

# alpine

apk add wireguard-tools cryptsetup btrfs-progs zfs tmux htop qemu qemu-img

rc-update add wg-quick.wg0 default

# TODO

## MVP

Should:
- Boot, print ssh key
- Spin up ssh
- Be able to mount
- Be able to start qemu
- Scp should work
- Poweroff/reboot should work

## Security hardening

- Pure kernel build
- musl
- static binaries
- apparmor
- selinux
- audit=1 lsm=lockdown,apparmor
- ro mount
- SEV-ES
- Compare with proxmox
- Remove unnecessary files
- fTPM or HSM (https://www.picokeys.com/pico-hsm/)
- seccomp
- firejail

## Production

- Test reproducability
- Spin up github actions
- Make it output versions
- Sign and enforce Secure Boot

# Useful info

https://buildroot.org/downloads/manual/manual.html

./build/buildroot/docs/

https://docs.kernel.org/kbuild/makefiles.html

Important: verify ssh key!
ssh-keygen -R 192.168.1.3

```
mount -t 9p -o trans=virtio,version=9p2000.L sd /mnt/sd
comet /mnt/comet 9p trans=virtio,version=9p2000.L 0 0
```

# net new

auto lo
iface lo inet loopback

auto eth0
iface eth0 inet manual

auto br0
iface br0 inet static
        address 192.168.1.3
        netmask 255.255.255.0
        gateway 192.168.1.1
        bridge_ports eth0
        bridge_stp off

# Old wg

[Interface]
PrivateKey = [redacted]
Address = [redacted]
DNS = [redacted]
PostUp = iptables -I OUTPUT ! -o %i -m mark ! --mark $(wg show %i fwmark) -m addrtype ! --dst-type LOCAL ! -d 192.168.0.0/16 -j REJECT && ip6tables -I OUTPUT ! -o %i -m mark ! --mark $(wg show %i fwmark) -m addrtype ! --dst-type LOCAL -j REJECT
PreDown = iptables -D OUTPUT ! -o %i -m mark ! --mark $(wg show %i fwmark) -m addrtype ! --dst-type LOCAL ! -d 192.168.0.0/16 -j REJECT && ip6tables -D OUTPUT ! -o %i -m mark ! --mark $(wg show %i fwmark) -m addrtype ! --dst-type LOCAL -j REJECT

[Peer]
PublicKey = [redacted]
AllowedIPs = 0.0.0.0/0,::0/0
Endpoint = [redacted]

# How to build on Ubuntu

sudo apt install build-essential

# Rig configuration

```
Gigabyte MZ32-AR0-00 (Rev 3.0)
- Intel I350 dual-port Gigabit Ethernet controller
- ASPEED AST1150 BMC VGA adapter
- Linux Foundation 2.0 root hub
- Linux Foundation 3.0 root hub
- Genesys Logic Hub (ID 05e3:0608, 05e3:0610)
- Genesys Logic GL3523 Hub

AMD EPYC 7702p
- AMD PSP cryptographic coprocessor
- AMD PTDMA DMA engine
- AMD Starship USB 3.0 controllers
- AMD FCH SATA (AHCI) controller
- AMD SMBus / TCO watchdog
- AMD k10temp temperature sensor

KINGSTON 32GB DDR4 3200MHz ECC KTH-PL432E/32G

KINGSTON 2TB NV3 M.2 PCIe M.2 2280 SNV3S/2000G

EVGA NVIDIA GeForce RTX 3090 FTW3 ULTRA GAMING, 24G-P5-3987-KR, 24GB GDDR6X (GA102 GPU)

Seagate Ironwolf ST18000NE000 18TB

Realtek RTL8153 Gigabit Ethernet Adapter (USB)

Generic USB Keyboard
Generic USB Mouse
Generic USB Stick
```

## Kernel modules

```
nouveau
nvidiafb
snd_hda_intel
igb
ast
ccp
ptdma
xhci_pci
ahci
nvme
i2c_piix4
sp5100_tco
k10temp
xhci_hcd
ehci_pci
ohci_pci
usbhid
hid_generic
usb_storage
uas
r8152
```

# Rest

modprobe btrfs
mkdir -p /mnt/data
cryptsetup open /dev/sdc1 crypt_sda
cryptsetup open /dev/sdd1 crypt_sdb
mount -o noatime,compress=zstd:3,space_cache=v2,device=/dev/mapper/crypt_sdb /dev/mapper/crypt_sda /mnt/data

# Mount BTRFS 18TB Data RAID1

print("""modprobe btrfs
mkdir -p /mnt/data
cryptsetup open /dev/sdc1 crypt_sda
cryptsetup open /dev/sdd1 crypt_sdb
mount -o noatime,compress=zstd:3,space_cache=v2,device=/dev/mapper/crypt_sdb /dev/mapper/crypt_sda /mnt/data""")