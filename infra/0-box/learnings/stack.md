# I value purity, isolation and ease of orchestration

# OS

## Proxmox / ESXi / Xen
Too bulky, stuff lives in VM and attack surface is the same because dom0 is ubuntu

## Alpine / Custom Kernel / Buildroot
Lack of usable drivers, too hard to maintain

## Linux Mint
Still not pure and isolated enough

## Ubuntu Server
Package installs not a config

## NixOS
Current solution with declarative config

# Workload

## libvirt / QEMU
Need to maintain OS inside

## Docker Compose
Daemon + rootful + no ingress/egress rules

## Rootless Podman
Sweet spot but not made it to work

## k3s
Was too clunky for the AI stack.

## MicroVMs / Cloud Hypervisor
Networking was hard

## Kata containers
GPU is a mess

## Firecracker / crosvm / kvmtool / other small VMMs
Cool for microvms

## Podman Compose
Current spot. Managed by `podman-compose.service` (oneshot, RemainAfterExit=true).

**Restart traps:**
- Never use `ExecStop = compose down` — `restartTriggers` and nixos-rebuild will kill all containers, even unchanged ones. `ExecReload = compose up -d --remove-orphans` suffices; `ExecStop` can be omitted entirely.
- Don't add extra files (e.g. `haproxy.cfg`) to `restartTriggers` — same full-stop problem. Use an activation script (`system.activationScripts`) to selectively restart individual containers on nixos-rebuild.
