#!/usr/bin/env python3

import argparse
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET


BASE = """
<domain type="kvm">
  <name/>
  <memory unit="GiB"/>
  <vcpu/>
  <os firmware="efi"><type arch="x86_64" machine="pc-q35-10.2">hvm</type><boot dev="hd"/></os>
  <features><acpi/><apic/><ioapic driver="kvm"/><smm state="off"/><vmport state="off"/></features>
  <cpu mode="host-passthrough" check="none" migratable="off"/>
  <clock offset="utc"/>
  <devices>
    <emulator>/run/libvirt/nix-emulators/qemu-system-x86_64</emulator>
    <disk type="file" device="disk"><driver name="qemu" type="qcow2" iommu="on"/><source/><target dev="vda" bus="virtio"/></disk>
    <audio id="1" type="none"/>
    <watchdog model="itco" action="reset"/>
    <memballoon model="none"/>
    <rng model="virtio"><driver iommu="on"/><backend model="random">/dev/urandom</backend></rng>
  </devices>
</domain>
"""

SEC = """
<sec>
  <memoryBacking><locked/></memoryBacking>
  <on_reboot>destroy</on_reboot>
  <launchSecurity type="sev"><policy>0x000f</policy><cbitpos>47</cbitpos><reducedPhysBits>1</reducedPhysBits></launchSecurity>
</sec>
"""

NET = """<interface type="user"><source/><model type="virtio"/><driver iommu="on"/><rom enabled="no"/><backend type="passt"/></interface>"""

UI = """
<ui>
  <input type="mouse" bus="ps2"/>
  <input type="keyboard" bus="ps2"/>
  <graphics type="spice" autoport="yes"><listen type="address"/><image compression="off"/><gl enable="no"/></graphics>
  <video><model type="virtio" heads="1" primary="yes"><acceleration accel3d="no"/></model></video>
</ui>
"""

GPU = """
<gpu>
  <hostdev mode="subsystem" type="pci" managed="yes">
    <source><address domain="0x0000" bus="0x41" slot="0x00" function="0x0"/></source>
  </hostdev>
  <hostdev mode="subsystem" type="pci" managed="yes">
    <source><address domain="0x0000" bus="0x41" slot="0x00" function="0x1"/></source>
  </hostdev>
</gpu>
"""


def generate_xml(cpu, ram, disk, net=None, ui=False, gpu=False, sec=False, name=None):
    name = name or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    root = ET.fromstring(BASE)
    devices = root.find("devices")

    root.find("name").text = name
    root.find("memory").text = str(ram)
    root.find("vcpu").text = str(cpu)
    root.find("devices/disk/source").set("file", disk)

    for dev in net or []:
        interface = ET.fromstring(NET)
        interface.find("source").set("dev", dev)
        devices.append(interface)

    if ui:
        devices.extend(list(ET.fromstring(UI)))

    if gpu:
        devices.extend(list(ET.fromstring(GPU)))

    if sec:
        os = root.find("os")
        os.insert(list(os).index(os.find("boot")), ET.Element("loader", stateless="yes"))
        memory_backing, on_reboot, launch_security = list(ET.fromstring(SEC))
        root.insert(list(root).index(root.find("memory")) + 1, memory_backing)
        root.insert(list(root).index(devices), on_reboot)
        root.append(launch_security)
        root.find("devices/watchdog").set("action", "shutdown")

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cpu", type=int, required=True)
    p.add_argument("--ram", type=int, required=True)
    p.add_argument("--disk", required=True)
    p.add_argument("--net", action="append")
    p.add_argument("--ui", action="store_true")
    p.add_argument("--gpu", action="store_true")
    p.add_argument("--sec", action="store_true", help="enable AMD SEV-ES")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    xml = generate_xml(
        args.cpu, args.ram, args.disk, args.net, args.ui, args.gpu, args.sec, name
    )
    path = Path(tempfile.gettempdir()) / f"{name}.xml"
    path.write_text(xml, encoding="utf-8")
    print(path)

    if not args.dry_run:
        subprocess.run(["virsh", "define", str(path)], check=True)


if __name__ == "__main__":
    main()
