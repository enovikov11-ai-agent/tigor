#!/bin/bash
# scp infra/1-box/wg-genkeys.sh root@tgr:/root && ssh root@tgr 'nix-shell -p wireguard-tools --run "bash /root/wg-genkeys.sh"'
# scp -r root@tgr:/root/vpns ~/Downloads/
# scp ~/Downloads/vpns/box.key root@box:/etc/wireguard/private.key
set -e
umask 077

mkdir -p /root/vpns
chmod 700 /root/vpns

for name in server box mac iphone; do
  wg genkey > "/root/vpns/$name.key"
  wg pubkey < "/root/vpns/$name.key" > "/root/vpns/$name.pub"
done

SERVER_PUB=$(cat /root/vpns/server.pub)
BOX_PUB=$(cat /root/vpns/box.pub)
MAC_PUB=$(cat /root/vpns/mac.pub)
IPHONE_PUB=$(cat /root/vpns/iphone.pub)

# install server private key
mkdir -p /etc/wireguard
cp /root/vpns/server.key /etc/wireguard/private.key
chmod 600 /etc/wireguard/private.key

# mac client config
cat > /root/vpns/tgr-mac.conf << EOF
[Interface]
PrivateKey = $(cat /root/vpns/mac.key)
Address = 10.69.42.3/24

[Peer]
PublicKey = $SERVER_PUB
Endpoint = tgr.rs:44222
AllowedIPs = 10.69.42.0/24
PersistentKeepalive = 25
EOF

# iphone client config
cat > /root/vpns/tgr-iphone.conf << EOF
[Interface]
PrivateKey = $(cat /root/vpns/iphone.key)
Address = 10.69.42.4/24

[Peer]
PublicKey = $SERVER_PUB
Endpoint = tgr.rs:44222
AllowedIPs = 10.69.42.0/24
PersistentKeepalive = 25
EOF

chmod 600 /root/vpns/*

echo ""
echo "=== Nix config: tgr.nix ==="
echo ""
echo "Replace in tgr.nix peers:"
echo "  <BOX_PUBKEY>    → $BOX_PUB"
echo "  <MAC_PUBKEY>    → $MAC_PUB"
echo "  <IPHONE_PUBKEY> → $IPHONE_PUB"
echo ""
echo "=== Nix config: box.nix ==="
echo ""
echo "Replace in box.nix peer:"
echo "  <SERVER_PUBKEY> → $SERVER_PUB"
echo ""
echo "=== Files in /root/vpns/ ==="
echo ""
echo "  box.key         → scp to box as /etc/wireguard/private.key"
echo "  tgr-mac.conf    → import in WireGuard app"
echo "  tgr-iphone.conf → import via QR code"
echo ""
echo "Download all:"
echo "  scp -r root@tgr.rs:/root/vpns ~/Downloads/"
echo ""
