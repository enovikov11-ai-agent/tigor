# tigor monorepo

Minimax h3
mkpasswd -m yescrypt -R 11

ssh-keygen -R 192.168.1.28
ssh root@192.168.1.28

nix build
mkdir /root/mnt
mount /dev/sde1 /root/mnt
df -h /root/mnt
cd /root/mnt/EFI/BOOT/
mv BOOTX64.efi "$(date '+%Y-%m-%d_%H-%M-%S')_BOOTX64.efi"
cp /root/result/BOOTX64.efi /root/mnt/EFI/BOOT/
sync
cd ~
umount /root/mnt
reboot now

Mouse passthrough
Net egress

wg
Table = off

<interface type='user'>
  <model type='virtio'/>
  <backend type='passt'/>
  <source dev='wg0'/>
</interface>

You specifically want to see something equivalent to:

--outbound-if4 wg0
--outbound-if6 wg0

If you see merely:

-i wg0

I would not call that a reliable killswitch.
