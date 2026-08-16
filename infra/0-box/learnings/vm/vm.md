
kata

firecracker

vmVariant is for testing

| VM | Purpose | Services |
|---|---|---|
| public-vm | Public services | forgejo-xecut, pixelwars, resident-storage, leetch, honkbot, 101bots |
| personal-vm | Personal services | p-forgejo, p-chat, p-agent |
| gpu-vm | GPU services | p-vllm, p-whisper, p-llama |
| hardened-vm | Agent sandboxes | on-demand |
| privacy-vm | Privacy services | transmission, bitcoin |
| vpn-gw | VPN gateway | WireGuard/OpenVPN client, NAT for privacy-vm |

| Hypervisor | Language | Restrictions |
|---|---|---|
| qemu | C | none |
| cloud-hypervisor | Rust | no 9p shares |
| firecracker | Rust | no 9p, no virtiofs, no PCI passthrough |
| crosvm | Rust | 9p shares broken |
| kvmtool | C | no virtiofs, no control socket |
| stratovirt | Rust | no 9p, no virtiofs, no control socket |
| alioth | Rust | no virtiofs, no control socket |

```nix
microvm.shares = [
  { tag = "hdd"; source = "/hdd"; mountPoint = "/hdd"; proto = "virtiofs"; }
  { tag = "ssd"; source = "/ssd"; mountPoint = "/ssd"; proto = "virtiofs"; }
];
```

Cloud Hypervisor runs virtiofsd per share. ZFS stays on host — VM sees regular directories. Near-native performance. UIDs pass through — if host files are `1000:1000` and containers run as `1000:1000`, it just works.

### GPU passthrough (VFIO)

Host gives up GPU entirely (bind to `vfio-pci` instead of nvidia driver). VM owns it exclusively, runs its own nvidia driver + CUDA + container-toolkit. Performance: bare metal (no overhead, direct hardware mapping).

Requires: IOMMU enabled (`iommu=on` kernel param), GPU in its own IOMMU group (EPYC is usually clean here), microvm.nix `microvm.devices` config.

## Networking

### Inter-VM firewall (infra-as-code)

Each VM gets a TAP interface with a static IP on its own /24. Host kernel routes between TAPs. nftables in the FORWARD chain enforces deny-all + explicit allowlist:

```nix
# conceptual — host nftables config
chain forward {
  type filter hook forward priority 0; policy drop;

  # public-vm → personal-vm: mysql only
  iifname "tap-public" oifname "tap-personal" tcp dport 3306 accept

  # personal-vm → gpu-vm: vllm API
  iifname "tap-personal" oifname "tap-gpu" tcp dport 8000 accept

  # everything else: denied by policy
}
```

This is standard Linux networking — nothing exotic. The rule table is the single source of truth for what can talk to what.

### Exposing VM ports on host (DNAT)

Same mechanism Docker uses for `-p`:

```nix
# host nftables — expose public-vm ports
tcp dport { 80, 443 } dnat to 10.0.1.2  # public-vm caddy
```

VPS nginx → WireGuard → host:443 → DNAT → public-vm:443.

Private services: don't DNAT from public interface, only route from WireGuard interface. `*.private.tgr.rs` DNS points to host WG IP (10.69.42.x), host DNATs to personal-vm. Anyone not on WG can't reach it. TLS works because certs use DNS-01 challenge.

```bash
sudo virtiofsd --socket-path=<SOCKET_PATH_FOR_HDD> --shared-dir=/hdd
```

## Gotchas

- TAP must have `multi_queue` flag or Cloud Hypervisor fails with `MultiQueueNoTapSupport`
- `nix run` requires `experimental-features = nix-command flakes` in `~/.config/nix/nix.conf`
- First build is slow (compiles kernel, builds squashfs). Subsequent cached in `/nix/store/`
- Console login won't work with key-only SSH (no password set). Use SSH.
- `chattr: Operation not supported` on volume creation is harmless
- `flake.lock` should be committed — pins dependency versions (like `package-lock.json`)
