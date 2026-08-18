sudo apt update
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients ovmf virt-manager
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients ovmf swtpm swtpm-tools
sudo apt install -y acl ovmf qemu-kvm libvirt-daemon-system libvirt-clients
sudo systemctl enable --now libvirtd

su box
cd /hdd/sev-es

sudo setfacl -m u:libvirt-qemu:rwx /hdd/sev-es
sudo setfacl -m u:libvirt-qemu:rw  /hdd/sev-es/sev-es-test.qcow2
sudo setfacl -m u:libvirt-qemu:r   /hdd/sev-es/ubuntu-24.04.3-live-server-amd64.iso

wget https://releases.ubuntu.com/24.04/ubuntu-24.04.3-live-server-amd64.iso
qemu-img create -f qcow2 sev-es-test.qcow2 10G

sudo mkdir -p /var/lib/libvirt/qemu/nvram
sudo cp /usr/share/OVMF/OVMF_VARS_4M.fd \
        /var/lib/libvirt/qemu/nvram/sev-es-test_VARS.fd
sudo chmod 0644 /var/lib/libvirt/qemu/nvram/sev-es-test_VARS.fd

sudo virsh undefine sev-es-test 2>/dev/null || true

sudo virsh define /dev/stdin <<'XML'
<domain type='kvm'>
  <name>sev-es-test</name>
  <memory unit='MiB'>2048</memory>
  <vcpu>2</vcpu>

  <memoryBacking>
  <locked/>
  <allocation mode='immediate'/>
</memoryBacking>

  <os>
    <type arch='x86_64' machine='q35'>hvm</type>
    <loader readonly='yes' type='pflash'>/usr/share/OVMF/OVMF_CODE_4M.fd</loader>
    <nvram>/var/lib/libvirt/qemu/nvram/sev-es-test_VARS.fd</nvram>
  </os>

  <features>
    <acpi/>
    <apic/>
  </features>

  <cpu mode='host-passthrough'/>

  <launchSecurity type='sev'>
    <policy>0x0004</policy>
  </launchSecurity>

  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>

    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='/hdd/sev-es/sev-es-test.qcow2'/>
      <target dev='vda' bus='virtio'/>
    </disk>

    <disk type='file' device='cdrom'>
      <driver name='qemu' type='raw'/>
      <source file='/hdd/sev-es/ubuntu-24.04.3-live-server-amd64.iso'/>
      <target dev='sda' bus='sata'/>
      <readonly/>
    </disk>

    <serial type='pty'>
      <target port='0'/>
    </serial>

    <console type='pty'>
      <target type='serial' port='0'/>
    </console>
  </devices>
</domain>
XML


sudo virsh start sev-es-test
sudo virsh console sev-es-test

Domain 'sev-es-test' started

Press ESC in 1 seconds to skip startup.nsh or any other key to continue.
Shell> ed to domain 'sev-es-test'
Escape character is ^] (Ctrl + ])