# Infrastructure Patterns

## Caddy Reverse Proxy

- All public websites/services through Caddy. Automatic HTTPS (Let's Encrypt), HTTP→HTTPS redirect.
- Static sites via `file_server` from `/var/www/`, backends via `reverse_proxy`.
- mTLS for internal services: `import mtls` snippet, must use `mode require_and_verify`.
- PROXY protocol (when TCP proxy sits in front): global `listener_wrappers` block with `proxy_protocol { allow <proxy-ip>/32 }` + `tls`. Applies to all ports. `{remote_host}` then reflects real client IP. Restrict `allow` to proxy IP.

### Caddy routing to internet-isolated services

Join Caddy to the service's existing `internal: true` network. Do NOT create a new non-internal bridge.

### Config-in-volume pattern

Bake default config into image, entrypoint copies on first boot if missing.

## Container Security

### Docker/podman socket
**Never mount `/var/run/docker.sock`** (or podman equivalent) into services. It's effectively root on the host.

### no-new-privileges + sudo
`no-new-privileges:true` blocks `sudo` inside containers (prevents setuid). If a container needs `sudo`: remove `security_opt: no-new-privileges:true` and add `NOPASSWD` sudoers entry in Dockerfile.

### Network isolation
- `internal: true` networks for internet isolation — app-level flags (`OFFLINE_MODE=true`) are hints, not guarantees.
- Before adding a network: inspect existing networks. If service is only on `internal: true` networks, that's a **hard constraint**. Don't break it.

### Host volume permissions
New directories on `/hdd/` and `/ssd/` have restrictive default permissions. Containers running as non-root (`user: "33:33"` or `1000:1000`) get access errors. Need to `chmod` on host before deploy. Warn about this when proposing new volume mounts.

## Scripts That Generate Secrets

Write to a dedicated directory (e.g. `/root/vpns/`) with `chmod 600/700`, then SCP to local. Never rely on terminal scrollback — it disappears. Pattern: write → secure → scp.

## Cross-Filesystem File Operations

`mv` across filesystems silently falls back to copy+delete — non-atomic, data loss risk. Use `mv --no-copy` (shell) or `os.rename()` (Python) for atomic-or-fail. For intentional cross-mount moves: `cp -r` → verify → `rm -rf`.

## WireGuard Exit Routing on NixOS

For a WireGuard server routing client internet traffic, keep server-side peer `allowedIPs` scoped to each client's tunnel IP (`/32`). Put `0.0.0.0/0` in the client config's peer `AllowedIPs`; on the server, enable IPv4 forwarding, NAT from `wg0` to the outbound interface, and explicit firewall forward rules for `wg0 -> outbound` plus established return traffic. Do not place the WireGuard subnet inside the LAN subnet clients need to reach.

## Verifying Files Are in Repo Before Deleting

Use `infra/0-utils/repo-contains.py` — indexes monorepo by sha256, checks candidate paths.
