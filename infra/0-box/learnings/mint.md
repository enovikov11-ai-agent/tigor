
# EPYC box

Linux mint
Menu -> Administration -> Driver Manager -> NVIDIA

## GPU on/off

### GPU to VM

docker stop llama-gpu

systemctl isolate multi-user.target
systemctl stop lightdm
systemctl stop nvidia-persistenced

modprobe -r nvidia_drm nvidia_modeset nvidia_uvm nvidia snd_hda_intel

modprobe vfio
modprobe vfio_pci

echo "10de 2204" > /sys/bus/pci/drivers/vfio-pci/new_id
echo "10de 1aef" > /sys/bus/pci/drivers/vfio-pci/new_id

virsh start win11-personal

### GPU to host

virsh shutdown win11

virsh event --domain win11 --event lifecycle

echo -n "0000:41:00.0" > /sys/bus/pci/drivers/vfio-pci/unbind
echo -n "0000:41:00.1" > /sys/bus/pci/drivers/vfio-pci/unbind

modprobe snd_hda_intel nvidia nvidia_uvm nvidia_modeset nvidia_drm

systemctl isolate graphical.target
systemctl start lightdm
systemctl start nvidia-persistenced

docker start llama-gpu

### Check

lspci -k -s 41:00.0
lspci -k -s 41:00.1

### Kernel modules

```
# /etc/udev/rules.d/99-vfio-gpu.rules
SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{device}=="0x2204", \
  ATTR{driver_override}="vfio-pci"
SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{device}=="0x1aef", \
  ATTR{driver_override}="vfio-pci"

KERNEL=="0000:41:00.0", SUBSYSTEM=="pci", RUN+="/bin/sh -c 'modprobe vfio-pci; echo 0000:41:00.0 > /sys/bus/pci/drivers/vfio-pci/bind'"
KERNEL=="0000:41:00.1", SUBSYSTEM=="pci", RUN+="/bin/sh -c 'modprobe vfio-pci; echo 0000:41:00.1 > /sys/bus/pci/drivers/vfio-pci/bind'"

# /etc/modprobe.d/blacklist-host-gpu.conf
blacklist nvidia_drm
blacklist nvidia_modeset
blacklist nvidia
blacklist nouveau
blacklist snd_hda_intel
```

## install

### init.sh

zfs load-key hdd/enc
zfs load-key ssd/enc
zfs mount hdd/enc
zfs mount ssd/enc
docker-compose up -d

### gpu

sudo apt-get update && sudo apt-get install -y --no-install-recommends \
   curl \
   gnupg2

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update

export NVIDIA_CONTAINER_TOOLKIT_VERSION=1.18.0-1
sudo apt-get install -y \
    nvidia-container-toolkit=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    nvidia-container-toolkit-base=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container-tools=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container1=${NVIDIA_CONTAINER_TOOLKIT_VERSION}

### zfs

vim /etc/apt/preferences.d/ubuntu-zfs.pref

Package: zfsutils-linux zfs-zed libzfslinux-dev libzfs4linux zfs-doc
Pin: release o=Ubuntu
Pin-Priority: 900


apt install zfsutils-linux zfs-zed

zfs version

modprobe zfs
zpool import

dkms status

#### create hdd

truncate -s 18000207937536 /mnt/ssd/fake-disk
losetup /dev/loop100 /mnt/ssd/fake-disk

zpool create -o ashift=12 hdd raidz1 /dev/sda /dev/sdb /dev/sdc /dev/loop100
zfs set compression=zstd hdd
zfs set atime=off hdd
zfs set xattr=sa hdd
zfs set acltype=posixacl hdd

zpool offline hdd loop100
losetup -d /dev/loop100
rm /mnt/ssd/fake-disk

#### hdd status

zpool list hdd
zpool status -v hdd
zpool get all hdd
zfs get all hdd
zfs list -p hdd
zfs list hdd

ls /dev | grep loop

#### hdd enc

zfs create -o encryption=on -o keyformat=passphrase -o keylocation=prompt hdd/enc
zfs set mountpoint=/hdd hdd/enc
zfs set canmount=on hdd/enc
zfs set canmount=off hdd
zfs set mountpoint=none hdd

zfs load-key hdd/enc
zfs mount hdd/enc

#### create ssd

zpool create ssd raidz1 /dev/nvme1n1 /dev/nvme2n1 /dev/nvme3n1 /dev/nvme4n1
zfs set atime=off ssd
zfs set xattr=sa ssd
zfs set acltype=posixacl ssd

#### ssd enc

zfs create -o encryption=on -o keyformat=passphrase -o keylocation=prompt ssd/enc
zfs set mountpoint=/ssd ssd/enc
zfs set canmount=on ssd/enc
zfs set canmount=off ssd
zfs set mountpoint=none ssd

zfs load-key ssd/enc
zfs mount ssd/enc

### ssh

apt install openssh-server
sudo apt install --yes wireguard wireguard-tools resolvconf

### vm

apt install qemu-system-x86 qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager virtinst

sudo usermod -aG libvirt,kvm box

modprobe virtiofs

vim /etc/modules

comet   /mnt/comet      virtiofs        defaults 0 0
sun   /mnt/sun      virtiofs        defaults 0 0

### vpn

sudo mkdir -p /etc/wireguard
sudo install -m 600 -o root -g root wg0.conf /etc/wireguard/wg0.conf

sudo systemctl enable --now wg-quick@wg0

### docker

apt install docker.io docker-compose-v2

### old btrfs

modprobe btrfs
mkdir -p /mnt/data

cryptsetup open /dev/sdc1 crypt_sda
cryptsetup open /dev/sdd1 crypt_sdb

mount -o noatime,compress=zstd:3,space_cache=v2,device=/dev/mapper/crypt_sdb /dev/mapper/crypt_sda /mnt/data
