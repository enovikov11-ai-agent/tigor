
# Install ubuntu

https://ubuntu.com/download/server/thank-you?version=24.04.3&architecture=amd64&lts=true

echo "c3514bf0056180d09376462a7a1b4f213c1d6e8ea67fae5c25099c6fd3d8274b *ubuntu-24.04.3-live-server-amd64.iso" | shasum -a 256 --check

non-minimal
no drivers

manual net

subnet: 192.168.1.0/24
address: 192.168.1.3
gateway: 192.168.1.1
name servers: 192.168.1.1
search domains: (empty)

no extras

ssh-keygen -R 192.168.1.3

apt update
apt upgrade

apt install -y zfsutils-linux

zpool import -f ssd
zpool import -f hdd

sudo zfs set keylocation=prompt ssd/enc
sudo zfs set keylocation=prompt hdd/enc

sudo systemctl enable zfs-import-cache.service
sudo systemctl enable zfs-mount.service


sudo systemctl edit zfs-mount.service

[Service]

StandardInput=tty-force
StandardOutput=inherit
StandardError=inherit
TTYPath=/dev/console
TTYReset=yes
TTYVHangup=yes
TTYVTDisallocate=yes

ExecStartPre=/sbin/zfs load-key -a

apt install -y \
  ca-certificates \
  curl \
  gnupg \
  lsb-release \
  software-properties-common

apt install -y podman
apt install -y docker.io

systemctl enable docker

sudo ubuntu-drivers install
reboot now
nvidia-smi

sudo apt-get update && sudo apt-get install -y --no-install-recommends \
   curl \
   gnupg2

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt install -y nvidia-container-toolkit

sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

sudo apt install -y wireguard

vim /etc/wireguard/wg0.conf
sudo systemctl enable wg-quick@wg0.service
sudo systemctl start wg-quick@wg0.service

apt install -y podman-compose

apt install -y docker-compose-v2

## Nix (for declarative VMs)

```
sh <(curl --proto '=https' --tlsv1.2 -L https://nixos.org/nix/install) --daemon
```

Open a new shell, then verify:

```
nix --version
```

Enable flakes:

```
mkdir -p ~/.config/nix
echo 'experimental-features = nix-command flakes' > ~/.config/nix/nix.conf
```
