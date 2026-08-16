# Useful

ssh-keygen -R 192.168.1.3

openssl rand -base64 12

hdparm -Y /dev/sdd

ssh -L 3306:127.0.0.1:3306 tgr

docker stats --no-stream

Xen/ESXi

Finder -> Cmd + K -> vnc://192.168.1.3:5901

qemu-img create -f qcow2 -b win11-orig.qcow2 -F qcow2 win11.qcow2

## unattended upgrade

apt update
apt install unattended-upgrades apt-listchanges

dpkg-reconfigure --priority=low unattended-upgrades

cat /etc/apt/apt.conf.d/20auto-upgrades

systemctl status unattended-upgrades.service

## SHA256

find /hdd -type f -exec sha256sum {} + > /root/data-4-bak-hashes
bash /root/notify.sh

## mTLS nginx

ssl_client_certificate /root/client.crt;
ssl_verify_client on;

/etc/letsencrypt/renewal/tgr.rs.conf 

renew_hook = docker exec nginx nginx -s reload

## MySQL

GRANT SELECT ON yahonkbot.users TO 'honkstat'@'%';
GRANT SELECT ON yahonkbot.honcoin_txns TO 'honkstat'@'%';

## Wireguard

priv=$(wg genkey); pub=$(echo "$priv" | wg pubkey); echo "Private: $priv"; echo "Public:  $pub"

service wg-quick@wg0 status

## Backup

echo "backuping monorepo"
tar -czf /Users/enovikov11/Code/backups/monorepo-$(date +%Y-%m-%d-%H-%M).tar.gz /Users/enovikov11/Code/monorepo/

### VM

virsh list --all

virsh dumpxml masked > masked.xml
virsh dumpxml win11 > win11.xml

https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/archive-virtio/virtio-win-0.1.285-1/

genisoimage -o winfsp.iso -R -J ./winfsp/
https://github.com/winfsp/winfsp

sc.exe create VirtioFsSvc binpath="C:\Program Files\Virtio-Win\VioFS\virtiofs.exe" start=auto depend="WinFsp.Launcher/VirtioFsDrv"
sc start VirtioFsSvc

## Energy

https://www.eps.rs/lat/snabdevanje/Stranice/cene.aspx
https://www.eps.rs/cir/snabdevanje/Documents/20250825_Odluka%20Skupštine%20EPS%20AD_regulisana%20cena%20EE_01.10.2025.pdf

Total avg 550W
1W = 10 RSD/mo or 1 RSD/mo if only night (0:00 - 8:00)

Idle 150W (16x5W + 40W GPU + 30W CPU)
CPU +170W
GPU +470W

Multigpu 300W / 1600W
Boiler 200W
Total max 2200W

No PSU change, batteries or solar is good

Memory speed is likely a cap for GPU+CPU

# hackrf

sudo apt install hackrf

sudo cp /usr/lib/udev/rules.d/60-libhackrf0.rules /etc/udev/rules.d/

sudo udevadm control --reload-rules
sudo udevadm trigger

/dev/bus/usb/003/007

OpenWebRX
SDR++ Web
Soapysdr-server + Web-based clients
GNU Radio

https://github.com/greatscottgadgets/hackrf
https://greatscottgadgets.com/sdr/
