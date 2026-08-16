#!/usr/bin/env python3
"""Create one Ubuntu Droplet and install Hermes Agent."""

import base64
import json
import os
import sys
import time

import requests


API = "https://api.digitalocean.com/v2"
REGION = "ams3"
IMAGE = "ubuntu-26-04-x64"
SIZE = "s-1vcpu-2gb"  # Basic, shared CPU: 1 vCPU, 2 GB RAM, 50 GB SSD.


def die(message):
    sys.exit(f"error: {message}")


def required(name):
    value = os.environ.get(name)
    if not value:
        die(f"{name} is required")
    return value


DO_PAT = required("DIGITALOCEAN_PAT")
BOT_TOKEN = required("TELEGRAM_BOT_TOKEN")
ADMIN_ID = required("TELEGRAM_ADMIN_ID")
NAME = required("DROPLET_NAME")
ALLOW_EXISTING = required("ALLOW_EXISTING_DROPLETS").lower()
OPENROUTER_KEY = required("OPENROUTER_API_KEY")
OPENROUTER_MODEL = required("OPENROUTER_MODEL")

if ALLOW_EXISTING not in {"true", "false"}:
    die("ALLOW_EXISTING_DROPLETS must be true or false")
if not ADMIN_ID.isdigit():
    die("TELEGRAM_ADMIN_ID must be numeric")
bot_id, separator, bot_secret = BOT_TOKEN.partition(":")
if not (
    separator
    and bot_id.isdigit()
    and bot_secret
    and all(character.isalnum() or character in "_-" for character in bot_secret)
):
    die("TELEGRAM_BOT_TOKEN is invalid")
if any(character in OPENROUTER_KEY + OPENROUTER_MODEL for character in "\r\n\0"):
    die("OpenRouter key and model cannot contain newlines or NUL")


session = requests.Session()
session.headers.update({"Authorization": f"Bearer {DO_PAT}"})


def api(method, path, **kwargs):
    try:
        response = session.request(method, API + path, timeout=60, **kwargs)
    except requests.RequestException as exc:
        die(f"{method} {path} failed; state may be unknown: {exc}")
    if not response.ok:
        try:
            message = response.json().get("message", response.text)
        except ValueError:
            message = response.text
        die(f"DigitalOcean returned HTTP {response.status_code}: {message}")
    try:
        return response.json()
    except ValueError:
        die("DigitalOcean returned invalid JSON")


# DigitalOcean lists normal and GPU Droplets separately. Any result is a no-go
# unless the operator explicitly opted in.
existing = []
for droplet_type in ("droplets", "gpus"):
    existing += api(
        "GET", "/droplets", params={"per_page": 1, "type": droplet_type}
    )["droplets"]

if existing and ALLOW_EXISTING != "true":
    die("the account already has a Droplet; set ALLOW_EXISTING_DROPLETS=true to override")

ssh_keys = api("GET", "/account/keys", params={"per_page": 2})["ssh_keys"]
if len(ssh_keys) != 1:
    die(f"the account must have exactly one SSH key; found {len(ssh_keys)}")
ssh_public_key = ssh_keys[0].get("public_key", "").strip()
if not ssh_public_key or "\n" in ssh_public_key or "\0" in ssh_public_key:
    die("the account SSH key has an invalid public key")


env_file = "\n".join(
    [
        f"OPENROUTER_API_KEY={json.dumps(OPENROUTER_KEY)}",
        f"TELEGRAM_BOT_TOKEN={json.dumps(BOT_TOKEN)}",
        f"TELEGRAM_ALLOWED_USERS={json.dumps(ADMIN_ID)}",
        "",
    ]
)
config_file = f"""model:
  provider: openrouter
  default: {json.dumps(OPENROUTER_MODEL)}
gateway:
  platforms:
    telegram:
      extra:
        allow_from: ["{ADMIN_ID}"]
        allow_admin_from: ["{ADMIN_ID}"]
        group_allow_admin_from: ["{ADMIN_ID}"]
"""

env_b64 = base64.b64encode(env_file.encode()).decode()
config_b64 = base64.b64encode(config_file.encode()).decode()
ssh_key_b64 = base64.b64encode(ssh_public_key.encode()).decode()

cloud_init = f"""#!/bin/bash
set -euo pipefail
exec > >(tee -a /var/log/hermes-bootstrap.log) 2>&1

# Do not rely on DigitalOcean's image-specific SSH-key injection.
install -d -m 0700 -o root -g root /root/.ssh
printf %s {ssh_key_b64!r} | base64 -d > /root/.ssh/authorized_keys
printf '\n' >> /root/.ssh/authorized_keys
chmod 0600 /root/.ssh/authorized_keys

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y
apt-get install -y ca-certificates curl git unattended-upgrades \
    build-essential python3-dev libffi-dev ripgrep ffmpeg

cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
systemctl enable --now apt-daily.timer apt-daily-upgrade.timer

id hermes >/dev/null 2>&1 || useradd --create-home --shell /bin/bash hermes
install -d -m 0700 -o hermes -g hermes /home/hermes/.hermes

curl -fsSL https://hermes-agent.nousresearch.com/install.sh -o /tmp/hermes-install.sh
chmod 0755 /tmp/hermes-install.sh
runuser -u hermes -- env HOME=/home/hermes HERMES_HOME=/home/hermes/.hermes \
    /tmp/hermes-install.sh --skip-setup --skip-browser --non-interactive
rm /tmp/hermes-install.sh

printf %s {env_b64!r} | base64 -d > /home/hermes/.hermes/.env
printf %s {config_b64!r} | base64 -d > /home/hermes/.hermes/config.yaml
chown -R hermes:hermes /home/hermes/.hermes
chmod 0600 /home/hermes/.hermes/.env /home/hermes/.hermes/config.yaml

cat > /etc/systemd/system/hermes-gateway.service <<'EOF'
[Unit]
Description=Hermes Agent Telegram Gateway
Wants=network-online.target
After=network-online.target

[Service]
User=hermes
Group=hermes
WorkingDirectory=/home/hermes
Environment=HOME=/home/hermes
Environment=HERMES_HOME=/home/hermes/.hermes
Environment=PATH=/home/hermes/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/home/hermes/.local/bin/hermes gateway
Restart=on-failure
RestartSec=5
UMask=0077

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now hermes-gateway
"""

droplet = api(
    "POST",
    "/droplets",
    json={
        "name": NAME,
        "region": REGION,
        "image": IMAGE,
        "size": SIZE,
        "ssh_keys": [ssh_keys[0]["id"]],
        "backups": True,
        # DigitalOcean backup hours are UTC: 04:00-08:00 = 06:00-10:00 CEST.
        "backup_policy": {"plan": "daily", "hour": 4},
        "public_networking": True,
        "ipv6": False,
        "monitoring": False,
        "with_droplet_agent": False,
        "user_data": cloud_init,
    },
)["droplet"]

droplet_id = droplet["id"]
for _ in range(60):
    time.sleep(5)
    droplet = api("GET", f"/droplets/{droplet_id}")["droplet"]
    public_ips = [
        network["ip_address"]
        for network in droplet["networks"]["v4"]
        if network["type"] == "public"
    ]
    if droplet["status"] == "active" and public_ips:
        print(f"created {NAME}: ssh root@{public_ips[0]}")
        print("Hermes is configuring; check /var/log/hermes-bootstrap.log on the Droplet.")
        break
else:
    die(f"Droplet {droplet_id} exists but did not become active within 5 minutes")
