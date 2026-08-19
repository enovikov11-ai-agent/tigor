# Guides

## Ephermal

ssh-keygen -R 192.168.1.41
ssh root@192.168.1.41

mnt

nixos-rebuild switch --flake .#host

nix shell nixpkgs#opencode nixpkgs#cloud-hypervisor nixpkgs#virtiofsd

NIXPKGS_ALLOW_UNFREE=1 nix build .#cloudHypervisorVm --impure

warning: Nix search path entry '/nix/var/nix/profiles/per-user/root/channels' does not exist, ignoring
warning: download buffer is full; consider increasing the 'download-buffer-size' setting

## Redeploy tgr.rs on Contabo VPS

Generate keys and add them to https://github.com/tgr-rs/monorepo
git clone git@github.com:tgr-rs/monorepo.git

vim ~/monorepo/infra/0-tgr/.env

cd ~/monorepo/infra/0-tgr
docker compose up -d --remove-orphans

## Regular update tgr.rs / backup

cd ~/monorepo/infra/0-tgr

nixos-rebuild boot --upgrade

## Redeploy box

scp ~/Desktop/monorepo/infra/0-box/configuration.nix box:/etc/nixos/configuration.nix
nixos-rebuild switch -I nixos-config=/etc/nixos/configuration.nix

## Huggingface

### Login

hf auth whoami
hf auth login

### List

find /ssd/internet/huggingface.co/ -mindepth 2 -maxdepth 2

### Download

repo="Wan-AI/Wan2.2-I2V-A14B"
hf download "$repo" --local-dir "/ssd/internet/huggingface.co/$repo"

### Fix permissions

chown -R root:root /ssd/internet/huggingface.co
find /ssd/internet/huggingface.co -type d -exec chmod 0755 {} +
find /ssd/internet/huggingface.co -type f -exec chmod 0644 {} +
find /ssd/internet/huggingface.co -mindepth 1 -maxdepth 1 -type d -exec chmod 1777 {} +

## Wan 2.2

box
cd ~/monorepo/ai/0-wan

### Build base WAN

podman build -t wan -f wan.Containerfile .
podman image inspect wan --format '{{.Id}}  {{.Created}}'

### Stop/start vLLM

podman stop p-vllm
podman start p-vllm

### Build bot

podman build -t wanbot -f wanbot.Containerfile .
podman run --name wanbot --device nvidia.com/gpu=all --shm-size=16g -v /ssd/internet:/ssd/internet:ro -d --restart=unless-stopped -e TELEGRAM_BOT_TOKEN= wanbot
