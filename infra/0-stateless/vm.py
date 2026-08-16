#!/usr/bin/env python3

import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from copy import deepcopy
from datetime import datetime
from pathlib import Path

CONFIG_JSON = r"""
{
  "cpu": 64,
  "ram": 128,
  "kernel": "/ssd/vm/r8-rc3-vm-nvda-pods-su-BOOTX64.efi",
  "name": null,
  "ui": true,
  "gpu": true,
  "security": false,
  "mounts": [
    {
      "src": "/ssd/internet",
      "dst": "/ssd/internet",
      "readonly": true
    },
    {
      "src": "/ssd/vm/containers",
      "dst": "/var/lib/containers",
      "readonly": false
    }
  ],
  "net": {
    "dev": "wg-hermes",
    "forwards": [
      {
        "proto": "tcp",
        "host": 2222,
        "guest": 22
      }
    ]
  },
  "define": true
}
"""

ROOT = """
<domain type="kvm">
  <name/>
  <memory unit="GiB"/>
  <memoryBacking><locked/><source type="memfd"/><access mode="shared"/></memoryBacking>
  <vcpu/>
  <os firmware="efi">
    <type arch="x86_64" machine="pc-q35-10.2">hvm</type>
    <loader readonly="yes" type="pflash" stateless="yes" format="raw">/run/libvirt/nix-ovmf/edk2-x86_64-code.fd</loader>
    <boot dev="hd"/>
    <kernel/>
  </os>
  <features><acpi/><apic/><ioapic driver="kvm"/><smm state="off"/><vmport state="off"/></features>
  <cpu mode="host-passthrough" check="none" migratable="off"/>
  <clock offset="utc"/>
  <devices>
    <emulator>/run/libvirt/nix-emulators/qemu-system-x86_64</emulator>
    <disk type="file" device="disk"><driver name="qemu" type="qcow2" iommu="on"/><source/><target dev="vda" bus="virtio"/></disk>
    <interface type="user"><source/><model type="virtio"/><driver iommu="on"/><rom enabled="no"/><backend type="passt"/></interface>
    <filesystem type="mount"><driver type="virtiofs"/><source/><target/><readonly/></filesystem>
    <input type="mouse" bus="ps2"/>
    <input type="keyboard" bus="ps2"/>
    <graphics type="spice" autoport="yes"><listen type="address"/><image compression="off"/><gl enable="no"/></graphics>
    <video><model type="virtio" heads="1" primary="yes"><acceleration accel3d="no"/></model></video>
    <hostdev mode="subsystem" type="pci" managed="yes">
      <source><address domain="0x0000" bus="0x41" slot="0x00" function="0x0"/></source>
    </hostdev>
    <hostdev mode="subsystem" type="pci" managed="yes">
      <source><address domain="0x0000" bus="0x41" slot="0x00" function="0x1"/></source>
    </hostdev>
    <audio id="1" type="none"/>
    <watchdog model="itco" action="reset"/>
    <memballoon model="none"/>
    <rng model="virtio"><driver iommu="on"/><backend model="random">/dev/urandom</backend></rng>
  </devices>
  <launchSecurity type="sev"><policy>0x000f</policy><cbitpos>47</cbitpos><reducedPhysBits>1</reducedPhysBits></launchSecurity>
</domain>
"""


def generate_xml(config):
    kernel = config.get("kernel")
    disk = config.get("disk")
    mounts = config.get("mounts", [])
    net = config.get("net")
    security = config.get("security", False)

    if security and mounts:
        raise ValueError("security cannot be combined with mounts")
    if (kernel is None) == (disk is None):
        raise ValueError("exactly one of kernel or disk is required")

    name = config.get("name") or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    root = ET.fromstring(ROOT)
    devices = root.find("devices")

    root.find("name").text = name
    root.find("memory").text = str(config["ram"])
    root.find("vcpu").text = str(config["cpu"])
    kernel_element = root.find("os/kernel")
    if kernel is not None:
        kernel_element.text = kernel
        root.find("os").remove(root.find("os/boot"))
    else:
        root.find("os").remove(kernel_element)

    disk_element = devices.find("disk")
    if disk is not None:
        disk_element.find("source").set("file", disk)
    else:
        devices.remove(disk_element)

    interface = devices.find("interface")
    source = interface.find("source")
    if net is None:
        interface.remove(source)
    else:
        if net.get("dev") is not None:
            source.set("dev", net["dev"])
        else:
            interface.remove(source)

        for forwarding in net.get("forwards", []):
            proto = forwarding.get("proto", "tcp")
            if proto not in ("tcp", "udp"):
                raise ValueError(f"unsupported forwarding protocol: {proto}")

            port_forward = ET.SubElement(interface, "portForward", proto=proto)
            for attribute in ("address", "dev"):
                if forwarding.get(attribute) is not None:
                    port_forward.set(attribute, str(forwarding[attribute]))

            host_port = int(forwarding["host"])
            guest_port = int(forwarding.get("guest", host_port))
            if not (1 <= host_port <= 65535 and 1 <= guest_port <= 65535):
                raise ValueError("forwarded ports must be between 1 and 65535")

            attributes = {"start": str(host_port)}
            if guest_port != host_port:
                attributes["to"] = str(guest_port)
            ET.SubElement(port_forward, "range", attributes)

    filesystem_template = devices.find("filesystem")
    devices.remove(filesystem_template)
    for mount in mounts:
        filesystem = deepcopy(filesystem_template)
        filesystem.find("source").set("dir", mount["src"])
        filesystem.find("target").set("dir", mount["dst"])
        if not mount.get("readonly", True):
            filesystem.remove(filesystem.find("readonly"))
        devices.append(filesystem)

    if not config.get("ui", False):
        for tag in ("input", "graphics", "video"):
            for item in devices.findall(tag):
                devices.remove(item)

    if not config.get("gpu", False):
        for item in devices.findall("hostdev"):
            devices.remove(item)

    if security:
        os = root.find("os")
        os.attrib.pop("firmware")
        memory_backing = root.find("memoryBacking")
        memory_backing.remove(memory_backing.find("source"))
        memory_backing.remove(memory_backing.find("access"))
    else:
        root.find("os").remove(root.find("os/loader"))
        root.remove(root.find("launchSecurity"))
        memory_backing = root.find("memoryBacking")
        memory_backing.remove(memory_backing.find("locked"))
        if not mounts:
            root.remove(memory_backing)

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def main():
    config = json.loads(CONFIG_JSON)
    generated_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    xml = generate_xml(config)
    path = Path(tempfile.gettempdir()) / f"{generated_name}.xml"
    path.write_text(xml, encoding="utf-8")
    print(path)

    if config.get("define", True):
        subprocess.run(["virsh", "define", str(path)], check=True)


if __name__ == "__main__":
    main()
