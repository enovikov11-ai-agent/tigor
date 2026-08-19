sudo -i

umask 077

nix shell \
  nixpkgs#pciutils \
  nixpkgs#binutils \
  nixpkgs#kmod \
  nixpkgs#coreutils \
  nixpkgs#gnugrep

export BDF=0000:41:00.0
export DEV=/sys/bus/pci/devices/$BDF

export OUT=/root/rtxpro6000-preserve-$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$OUT"/{firmware,pci,nvidia,nixos}
cd "$OUT"

cat "$DEV/vendor"
cat "$DEV/device"
cat "$DEV/subsystem_vendor"
cat "$DEV/subsystem_device"

lspci -s "$BDF" -nn

lspci -s "$BDF" -nnvvv > pci/lspci-nnvvv.txt

dd if="$DEV/config" \
   of=pci/config-256.bin \
   bs=256 count=1 status=none

for f in \
  vendor device subsystem_vendor subsystem_device \
  revision class resource enable \
  current_link_speed current_link_width \
  max_link_speed max_link_width \
  reset_method
do
    if [ -r "$DEV/$f" ]; then
        cat "$DEV/$f" > "pci/$f.txt"
    fi
done

readlink -f "$DEV/driver" > pci/driver.txt 2>/dev/null || true
readlink -f "$DEV/iommu_group" > pci/iommu-group.txt 2>/dev/null || true

if [ -r "$DEV/vpd" ]; then
    cat "$DEV/vpd" > pci/vpd.bin
    sha256sum pci/vpd.bin
fi

cat "$DEV/enable"

ENABLE="$(cat "$DEV/enable")"

if ! [[ "$ENABLE" =~ ^[0-9]+$ ]] || [ "$ENABLE" -le 0 ]; then
    echo "STOP: PCI device is not enabled. Ничего не меняем."
    exit 1
fi

cleanup_rom() {
    printf 0 > "$DEV/rom" 2>/dev/null || true
}

trap cleanup_rom EXIT INT TERM HUP

printf 1 > "$DEV/rom"

cat "$DEV/rom" > firmware/vbios-read1.rom
cat "$DEV/rom" > firmware/vbios-read2.rom

cleanup_rom
trap - EXIT INT TERM HUP

ls -lh firmware/vbios-read*.rom

test -s firmware/vbios-read1.rom || {
    echo "ERROR: first ROM dump is empty"
    exit 1
}

test -s firmware/vbios-read2.rom || {
    echo "ERROR: second ROM dump is empty"
    exit 1
}

nvidia-smi -q > nvidia/nvidia-smi-q.txt 2>&1 || true

cat /proc/driver/nvidia/version \
    > nvidia/driver-version.txt 2>/dev/null || true

cat /proc/driver/nvidia/params \
    > nvidia/driver-params.txt 2>/dev/null || true

modinfo nvidia \
    > nvidia/modinfo-nvidia.txt 2>/dev/null || true

modinfo -F firmware nvidia \
    2>/dev/null |
    sort -u \
    > nvidia/firmware-files.txt

cat nvidia/firmware-files.txt

tar -C / -cf nixos/etc-nixos.tar etc/nixos