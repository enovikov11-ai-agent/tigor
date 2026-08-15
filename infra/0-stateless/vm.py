#!/usr/bin/env python3

import argparse
from copy import deepcopy
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

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
    <interface type="user"><source/><model type="virtio"/><driver iommu="on"/><rom enabled="no"/><backend type="passt"/><portForward proto="tcp"><range/></portForward></interface>
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


def generate_xml(
    cpu,
    ram,
    kernel=None,
    disk=None,
    net=None,
    ui=False,
    gpu=False,
    sec=False,
    name=None,
    ro=None,
    rw=None,
    ssh=None,
):
    if sec and (ro or rw):
        raise ValueError("--sec cannot be combined with --ro or --rw")
    if (kernel is None) == (disk is None):
        raise ValueError("exactly one of --kernel or --disk is required")

    name = name or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    root = ET.fromstring(ROOT)
    devices = root.find("devices")

    root.find("name").text = name
    root.find("memory").text = str(ram)
    root.find("vcpu").text = str(cpu)
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
    if net is not None:
        interface.find("source").set("dev", net)
    port_forward = interface.find("portForward")
    if net is not None and ssh is not None:
        port_forward.find("range").attrib.update(start=str(ssh), to="22")
    else:
        interface.remove(port_forward)

    filesystem_template = devices.find("filesystem")
    devices.remove(filesystem_template)
    filesystems = [(path, True) for path in ro or []] + [(path, False) for path in rw or []]
    for path, readonly in filesystems:
        filesystem = deepcopy(filesystem_template)
        filesystem.find("source").set("dir", path)
        filesystem.find("target").set("dir", path)
        if not readonly:
            filesystem.remove(filesystem.find("readonly"))
        devices.append(filesystem)

    if not ui:
        for tag in ("input", "graphics", "video"):
            for item in devices.findall(tag):
                devices.remove(item)

    if not gpu:
        for item in devices.findall("hostdev"):
            devices.remove(item)

    if sec:
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
        if not filesystems:
            root.remove(memory_backing)

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cpu", type=int, required=True)
    p.add_argument("--ram", type=int, required=True)
    p.add_argument("--kernel", help="direct-boot UKI containing the complete system")
    p.add_argument("--disk", help="QCOW2 boot disk attached as vda")
    p.add_argument("--name", help="libvirt domain name (default: current timestamp)")
    p.add_argument("--net", metavar="DEV", help="host interface used by passt")
    p.add_argument("--ssh", metavar="PORT", help="forward host TCP PORT to guest port 22 when --net is used")
    p.add_argument("--ro", action="append", metavar="DIR", help="share DIR read-only")
    p.add_argument("--rw", action="append", metavar="DIR", help="share DIR read-write")
    p.add_argument("--ui", action="store_true")
    p.add_argument("--gpu", action="store_true")
    p.add_argument("--sec", action="store_true", help="enable AMD SEV-ES")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    generated_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    name = args.name or generated_name
    xml = generate_xml(
        args.cpu,
        args.ram,
        args.kernel,
        disk=args.disk,
        net=args.net,
        ui=args.ui,
        gpu=args.gpu,
        sec=args.sec,
        name=name,
        ro=args.ro,
        rw=args.rw,
        ssh=args.ssh,
    )
    path = Path(tempfile.gettempdir()) / f"{generated_name}.xml"
    path.write_text(xml, encoding="utf-8")
    print(path)

    if not args.dry_run:
        subprocess.run(["virsh", "define", str(path)], check=True)


if __name__ == "__main__":
    main()
