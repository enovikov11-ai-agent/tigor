#!/usr/bin/env bash
#
# RTX PRO 6000 Blackwell software-side backup / inventory collector
#
# Goal:
#   Collect as much useful recovery/debug information as possible without
#   changing GPU firmware, GPU settings, EEPROM contents, clocks, power limits,
#   MIG state, display mode, etc.
#
# Designed for:
#   - NixOS/Linux VM with the RTX PRO 6000 passed through
#   - Linux physical host, ideally with the VM stopped
#
# Default behavior:
#   - Collects NVIDIA, PCI, sysfs, VPD, driver, kernel, and firmware-package info
#   - If nvflash/nvflash64 is installed, only uses query/list/save operations
#   - Attempts to dump the PCI expansion ROM through sysfs
#
# IMPORTANT ABOUT THE PCI ROM STEP:
#   Linux requires writing "1" and then "0" to /sys/.../rom to enable/disable
#   access to the *read-only PCI ROM resource*. This is NOT a firmware write.
#   The script never writes to /sys/.../enable and never invokes any firmware
#   programming/update/configuration command.
#
# To skip even that sysfs ROM gate toggle:
#   ./rtxpro6000_readonly_backup.sh --no-rom
#
# To select a specific GPU:
#   ./rtxpro6000_readonly_backup.sh --gpu-index 0
#   ./rtxpro6000_readonly_backup.sh --bdf 0000:41:00.0
#
# Environment variable equivalents:
#   GPU_INDEX=0
#   GPU_BDF=0000:41:00.0
#
# Recommended:
#   1. Run once inside the passthrough VM.
#   2. Stop the VM completely.
#   3. Run once on the physical host.
#   4. Keep both resulting .tar archives and .sha256 files.
#
# This is a collector, not a flasher.
#

set -o pipefail
umask 077
export LC_ALL=C

GPU_INDEX="${GPU_INDEX:-0}"
GPU_BDF="${GPU_BDF:-}"
WITH_ROM=1

usage() {
    cat <<'EOF'
Usage:
  rtxpro6000_readonly_backup.sh [options]

Options:
  --gpu-index N   NVIDIA GPU index to use with nvidia-smi/nvflash (default: 0)
  --bdf BDF       PCI BDF, e.g. 0000:41:00.0
  --no-rom        Skip PCI expansion-ROM sysfs dump
  -h, --help      Show this help

The script does not intentionally modify GPU firmware or persistent GPU settings.
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --gpu-index)
            shift
            [ "$#" -gt 0 ] || { echo "Missing value for --gpu-index" >&2; exit 2; }
            GPU_INDEX="$1"
            ;;
        --bdf)
            shift
            [ "$#" -gt 0 ] || { echo "Missing value for --bdf" >&2; exit 2; }
            GPU_BDF="$1"
            ;;
        --no-rom|--strict-readonly)
            WITH_ROM=0
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
host="$(hostname 2>/dev/null || echo unknown-host)"
OUT="${PWD}/rtxpro6000-backup-${host}-${timestamp}"
mkdir -p "$OUT"
LOG="$OUT/session.log"

# Tee all normal script output to the terminal and to session.log.
exec > >(tee -a "$LOG") 2>&1

section() {
    printf '\n\n===== %s =====\n' "$*"
}

note() {
    printf '[*] %s\n' "$*"
}

warn() {
    printf '[!] %s\n' "$*" >&2
}

have() {
    command -v "$1" >/dev/null 2>&1
}

# Run a command, teeing combined stdout/stderr to a per-command file.
# A failed probe is recorded but never aborts the whole collection.
run_capture() {
    local file="$1"
    shift

    printf '\n$'
    printf ' %q' "$@"
    printf '\n'

    "$@" 2>&1 | tee "$OUT/$file"
    local rc=${PIPESTATUS[0]}
    printf '[exit=%d]\n' "$rc"
    return 0
}

# Run shell syntax/pipelines when needed.
run_shell_capture() {
    local file="$1"
    shift
    local code="$*"

    printf '\n$ %s\n' "$code"
    bash -o pipefail -c "$code" 2>&1 | tee "$OUT/$file"
    local rc=${PIPESTATUS[0]}
    printf '[exit=%d]\n' "$rc"
    return 0
}

copy_text_if_readable() {
    local src="$1"
    local dst="$2"

    if [ -r "$src" ]; then
        note "Reading $src -> $dst"
        cat "$src" > "$OUT/$dst" 2>>"$LOG" || warn "Could not fully read $src"
    fi
}

copy_binary_if_readable() {
    local src="$1"
    local dst="$2"

    if [ -r "$src" ]; then
        note "Reading binary $src -> $dst"
        cat "$src" > "$OUT/$dst" 2>>"$LOG" || warn "Could not fully read $src"
        if [ -f "$OUT/$dst" ]; then
            stat -c 'size=%s bytes' "$OUT/$dst" 2>/dev/null || true
            sha256sum "$OUT/$dst" 2>/dev/null || true
        fi
    fi
}

section "Safety / environment"

date -u
printf 'output_dir=%s\n' "$OUT"
printf 'uid=%s euid=%s\n' "$(id -u)" "$EUID"
printf 'gpu_index=%s\n' "$GPU_INDEX"
printf 'requested_bdf=%s\n' "${GPU_BDF:-auto}"
printf 'pci_rom_dump=%s\n' "$WITH_ROM"

if [ "$EUID" -ne 0 ]; then
    warn "Not running as root. The script will continue, but some reads may fail."
fi

if have systemd-detect-virt; then
    run_capture virtualization.txt systemd-detect-virt
fi

run_capture uname.txt uname -a

if [ -r /etc/os-release ]; then
    cp /etc/os-release "$OUT/os-release.txt"
    cat "$OUT/os-release.txt"
fi

run_capture id.txt id

if have hostnamectl; then
    run_capture hostnamectl.txt hostnamectl
fi

section "NVIDIA user-space inventory"

if have nvidia-smi; then
    run_capture nvidia-smi-version.txt nvidia-smi --version
    run_capture nvidia-smi-list.txt nvidia-smi -L
    run_capture nvidia-smi-full.txt nvidia-smi -q
    run_capture nvidia-smi-full.xml nvidia-smi -q -x
    run_capture nvidia-smi-full-with-dtd.xml nvidia-smi -q -x --dtd
    run_capture nvidia-smi-help-query-gpu.txt nvidia-smi --help-query-gpu

    # These are queries only. Unsupported fields simply produce a logged error.
    run_capture nvidia-smi-inforom-checksum.txt \
        nvidia-smi --query-gpu=inforom.checksum_validation --format=csv

    run_capture nvidia-smi-gsp-firmware.txt \
        nvidia-smi -q -d GSP_FIRMWARE_VERSION

    run_capture nvidia-smi-ecc.txt \
        nvidia-smi -q -d ECC

    run_capture nvidia-smi-page-retirement.txt \
        nvidia-smi -q -d PAGE_RETIREMENT

    run_capture nvidia-smi-row-remapper.txt \
        nvidia-smi -q -d ROW_REMAPPER

    run_capture nvidia-smi-reset-status.txt \
        nvidia-smi -q -d RESET_STATUS

    run_capture nvidia-smi-topology.txt nvidia-smi topo -m

    # Read-only MIG capability/listing queries. They may be unsupported.
    run_capture nvidia-smi-mig-gpu-instances.txt nvidia-smi mig -lgip
    run_capture nvidia-smi-mig-compute-instances.txt nvidia-smi mig -lcip

    # If BDF was not specified, derive it from the selected NVIDIA GPU.
    if [ -z "$GPU_BDF" ]; then
        smi_bdf="$(
            nvidia-smi \
                --id="$GPU_INDEX" \
                --query-gpu=pci.bus_id \
                --format=csv,noheader 2>/dev/null |
            head -n 1 |
            tr -d '[:space:]'
        )"

        # nvidia-smi commonly prints 00000000:41:00.0 while Linux sysfs uses
        # 0000:41:00.0 for domain zero.
        smi_bdf="$(printf '%s' "$smi_bdf" | sed -E 's/^00000000:/0000:/')"

        if [ -n "$smi_bdf" ]; then
            GPU_BDF="$smi_bdf"
            note "Derived PCI BDF from nvidia-smi: $GPU_BDF"
        fi
    fi
else
    warn "nvidia-smi not found; NVIDIA driver-specific collection will be skipped."
fi

section "NVIDIA procfs"

copy_text_if_readable /proc/driver/nvidia/version nvidia-proc-version.txt
copy_text_if_readable /proc/driver/nvidia/params nvidia-proc-params.txt

if [ -d /proc/driver/nvidia/gpus ]; then
    while IFS= read -r -d '' f; do
        parent="$(basename "$(dirname "$f")")"
        base="$(basename "$f")"
        safe_parent="$(printf '%s' "$parent" | tr ':/' '__')"
        safe_base="$(printf '%s' "$base" | tr ':/' '__')"
        copy_text_if_readable "$f" "proc-nvidia-${safe_parent}-${safe_base}.txt"
    done < <(
        find /proc/driver/nvidia/gpus \
            -mindepth 2 -maxdepth 2 \
            -type f -print0 2>/dev/null
    )
fi

section "Kernel modules / driver packages"

if have lsmod; then
    run_capture lsmod.txt lsmod
fi

for mod in nvidia nvidia_drm nvidia_modeset nvidia_uvm vfio vfio_pci nouveau; do
    if have modinfo && modinfo "$mod" >/dev/null 2>&1; then
        run_capture "modinfo-${mod}.txt" modinfo "$mod"
    fi
done

for p in \
    /run/opengl-driver \
    /run/opengl-driver-32 \
    /run/current-system \
    /lib/firmware
do
    if [ -e "$p" ]; then
        printf '%s -> %s\n' "$p" "$(readlink -f "$p" 2>/dev/null || true)"
    fi
done | tee "$OUT/nixos-driver-paths.txt"

section "GSP / NVIDIA firmware files supplied by the OS"

GSP_LIST="$OUT/gsp-firmware-files.txt"
: > "$GSP_LIST"

for root in \
    /lib/firmware \
    /run/opengl-driver/lib/firmware \
    /run/current-system/sw/lib/firmware
do
    if [ -d "$root" ]; then
        find -L "$root" -type f \
            \( -name 'gsp_*.bin' -o -name 'gsp*.bin' \) \
            -print 2>/dev/null >> "$GSP_LIST"
    fi
done

sort -u -o "$GSP_LIST" "$GSP_LIST"

if [ -s "$GSP_LIST" ]; then
    cat "$GSP_LIST"
    mkdir -p "$OUT/gsp-firmware"

    while IFS= read -r f; do
        [ -r "$f" ] || continue

        # Preserve each file under a collision-resistant name.
        digest="$(printf '%s' "$f" | sha256sum | awk '{print substr($1,1,12)}')"
        base="$(basename "$f")"
        dst="$OUT/gsp-firmware/${digest}-${base}"

        cp -L -- "$f" "$dst" 2>/dev/null || continue
        printf '%s  %s\n' "$(sha256sum "$dst" | awk '{print $1}')" "$f"
    done | tee "$OUT/gsp-firmware-sha256-and-source.txt"
else
    note "No gsp_*.bin files found in standard firmware paths."
fi

section "PCI discovery"

if have lspci; then
    run_capture lspci-all-nn.txt lspci -Dnn
    run_capture lspci-all-nnvvv.txt lspci -Dnnvvv

    if [ -z "$GPU_BDF" ]; then
        GPU_BDF="$(
            lspci -Dnn 2>/dev/null |
            awk '
                BEGIN { IGNORECASE=1 }
                /NVIDIA/ && (/VGA compatible controller/ || /3D controller/) {
                    print $1
                    exit
                }
            '
        )"

        if [ -n "$GPU_BDF" ]; then
            note "Derived first NVIDIA display/3D PCI BDF from lspci: $GPU_BDF"
        fi
    fi
else
    warn "lspci not found; install pciutils for better PCI inventory."
fi

printf '%s\n' "$GPU_BDF" > "$OUT/selected-pci-bdf.txt"

if [ -z "$GPU_BDF" ]; then
    warn "Could not determine a GPU PCI BDF. PCI sysfs collection will be skipped."
else
    DEV="/sys/bus/pci/devices/$GPU_BDF"

    if [ ! -d "$DEV" ]; then
        warn "PCI device path does not exist: $DEV"
    else
        section "Selected GPU PCI device: $GPU_BDF"

        if have lspci; then
            run_capture lspci-selected-nnvvv.txt lspci -s "$GPU_BDF" -nnvvv
            run_capture lspci-selected-nnvvvk.txt lspci -s "$GPU_BDF" -nnvvvk

            # 256-byte traditional config-space text dump.
            run_capture lspci-selected-xxx.txt lspci -s "$GPU_BDF" -xxx

            # Full extended config-space text dump. This is still a read, but
            # some historically broken PCI hardware has disliked exhaustive
            # config-space reads. Modern GPUs normally tolerate it.
            run_capture lspci-selected-xxxx.txt lspci -s "$GPU_BDF" -xxxx
        fi

        # Raw PCI configuration space. Read whatever Linux exposes, up to 4096 B.
        if [ -r "$DEV/config" ]; then
            note "Reading PCI config space -> pci-config.bin"
            dd if="$DEV/config" \
               of="$OUT/pci-config.bin" \
               bs=4096 count=1 status=none 2>>"$LOG" || true
            stat "$OUT/pci-config.bin" 2>/dev/null || true
            sha256sum "$OUT/pci-config.bin" 2>/dev/null || true
        fi

        for attr in \
            vendor \
            device \
            subsystem_vendor \
            subsystem_device \
            revision \
            class \
            irq \
            numa_node \
            resource \
            modalias \
            uevent \
            current_link_speed \
            current_link_width \
            max_link_speed \
            max_link_width \
            reset_method \
            enable
        do
            copy_text_if_readable "$DEV/$attr" "pci-${attr}.txt"
        done

        {
            printf 'device=%s\n' "$(readlink -f "$DEV" 2>/dev/null || true)"
            printf 'driver=%s\n' "$(readlink -f "$DEV/driver" 2>/dev/null || true)"
            printf 'iommu_group=%s\n' "$(readlink -f "$DEV/iommu_group" 2>/dev/null || true)"
            printf 'physical_node=%s\n' "$(readlink -f "$DEV/physical_node" 2>/dev/null || true)"
        } | tee "$OUT/pci-symlinks.txt"

        if [ -d "$DEV/iommu_group/devices" ]; then
            ls -la "$DEV/iommu_group/devices" \
                2>&1 | tee "$OUT/iommu-group-devices.txt"
        fi

        if have udevadm; then
            run_capture udevadm-selected.txt \
                udevadm info --query=all --path="$DEV"
        fi

        # PCI VPD is one of the most interesting board-specific raw-ish blobs
        # available from software. Not every device exposes it.
        if [ -r "$DEV/vpd" ]; then
            copy_binary_if_readable "$DEV/vpd" pci-vpd.bin
            if have strings; then
                run_capture pci-vpd-strings.txt strings -a "$OUT/pci-vpd.bin"
            fi
            if have xxd; then
                run_capture pci-vpd-hexdump.txt xxd "$OUT/pci-vpd.bin"
            elif have hexdump; then
                run_capture pci-vpd-hexdump.txt hexdump -C "$OUT/pci-vpd.bin"
            fi
        else
            note "PCI VPD sysfs file is not exposed/readable for this device."
        fi

        section "PCI expansion ROM"

        if [ "$WITH_ROM" -eq 0 ]; then
            note "Skipped by --no-rom."
        elif [ ! -e "$DEV/rom" ]; then
            note "No PCI ROM sysfs resource exposed at $DEV/rom"
        else
            #
            # Linux keeps ROM access disabled until "1" is written to the
            # sysfs ROM gate. This does NOT write the GPU's flash.
            #
            # For extra conservatism, we only do this if the PCI device's
            # existing "enable" reference count is already nonzero. We never
            # write to $DEV/enable.
            #
            enable_value=""
            if [ -r "$DEV/enable" ]; then
                enable_value="$(cat "$DEV/enable" 2>/dev/null || true)"
            fi

            if ! [[ "$enable_value" =~ ^[0-9]+$ ]] || [ "$enable_value" -le 0 ]; then
                warn "PCI device enable count is not positive (${enable_value:-unknown}); skipping ROM dump."
                warn "The script will NOT enable the PCI device itself."
            elif [ ! -w "$DEV/rom" ]; then
                warn "Cannot toggle PCI ROM read gate at $DEV/rom; skipping."
            else
                note "Temporarily enabling Linux's PCI ROM read gate."
                note "This writes only 1/0 to the sysfs gate, not to GPU firmware."

                rom_gate_open=0

                close_rom_gate() {
                    if [ "$rom_gate_open" -eq 1 ]; then
                        printf 0 > "$DEV/rom" 2>/dev/null || true
                        rom_gate_open=0
                    fi
                }

                trap close_rom_gate EXIT INT TERM HUP

                if printf 1 > "$DEV/rom" 2>>"$LOG"; then
                    rom_gate_open=1

                    if cat "$DEV/rom" > "$OUT/pci-expansion-rom.bin" 2>>"$LOG"; then
                        note "PCI expansion ROM read completed."
                    else
                        warn "PCI expansion ROM read returned an error."
                    fi

                    close_rom_gate
                else
                    warn "Could not enable PCI ROM read gate."
                fi

                trap - EXIT INT TERM HUP

                if [ -f "$OUT/pci-expansion-rom.bin" ]; then
                    stat "$OUT/pci-expansion-rom.bin" 2>/dev/null || true
                    sha256sum "$OUT/pci-expansion-rom.bin" 2>/dev/null || true

                    if have xxd; then
                        xxd -l 128 "$OUT/pci-expansion-rom.bin" \
                            | tee "$OUT/pci-expansion-rom-first-128.txt"
                    elif have hexdump; then
                        hexdump -C -n 128 "$OUT/pci-expansion-rom.bin" \
                            | tee "$OUT/pci-expansion-rom-first-128.txt"
                    fi

                    size="$(stat -c '%s' "$OUT/pci-expansion-rom.bin" 2>/dev/null || echo 0)"
                    if [ "$size" -eq 0 ]; then
                        warn "PCI ROM file is zero bytes; do not treat it as a valid backup."
                    fi
                fi
            fi
        fi
    fi
fi

section "NVFlash read-only/query/save operations"

NVFLASH=""
if have nvflash; then
    NVFLASH="$(command -v nvflash)"
elif have nvflash64; then
    NVFLASH="$(command -v nvflash64)"
fi

if [ -n "$NVFLASH" ]; then
    note "Using NVFlash binary: $NVFLASH"

    run_capture nvflash-version.txt "$NVFLASH" --version
    run_capture nvflash-help.txt "$NVFLASH" --help
    run_capture nvflash-list.txt "$NVFLASH" --list

    # Only use --save if this build advertises it in --help.
    if grep -qi -- '--save' "$OUT/nvflash-help.txt"; then
        note "NVFlash help advertises --save; attempting VBIOS readout only."

        "$NVFLASH" --index="$GPU_INDEX" --save "$OUT/vbios-nvflash.rom" \
            2>&1 | tee "$OUT/nvflash-save.txt"
        nv_rc=${PIPESTATUS[0]}
        printf '[exit=%d]\n' "$nv_rc"

        if [ -f "$OUT/vbios-nvflash.rom" ]; then
            stat "$OUT/vbios-nvflash.rom" 2>/dev/null || true
            sha256sum "$OUT/vbios-nvflash.rom" 2>/dev/null || true

            nv_size="$(stat -c '%s' "$OUT/vbios-nvflash.rom" 2>/dev/null || echo 0)"
            if [ "$nv_size" -eq 0 ]; then
                warn "NVFlash created a zero-byte ROM. Keep the log, but this is not a usable backup."
            else
                if have xxd; then
                    xxd -l 128 "$OUT/vbios-nvflash.rom" \
                        | tee "$OUT/vbios-nvflash-first-128.txt"
                elif have hexdump; then
                    hexdump -C -n 128 "$OUT/vbios-nvflash.rom" \
                        | tee "$OUT/vbios-nvflash-first-128.txt"
                fi
            fi
        fi
    else
        note "This NVFlash build does not advertise --save; not guessing undocumented syntax."
    fi

    # Some builds expose --listpp, which is a listing/read operation.
    if grep -qi -- '--listpp' "$OUT/nvflash-help.txt"; then
        run_capture nvflash-listpp.txt "$NVFLASH" --index="$GPU_INDEX" --listpp
    fi
else
    note "nvflash/nvflash64 not found; VBIOS save via NVFlash skipped."
fi

section "NVIDIA diagnostic bundle"

if have nvidia-bug-report.sh; then
    note "Running NVIDIA's diagnostic collector."
    (
        cd "$OUT" || exit 1
        nvidia-bug-report.sh
    ) 2>&1 | tee "$OUT/nvidia-bug-report-console.txt"
    printf '[exit=%d]\n' "${PIPESTATUS[0]}"
else
    note "nvidia-bug-report.sh not found."
fi

section "fwupd inventory, if installed"

if have fwupdmgr; then
    run_capture fwupdmgr-version.txt fwupdmgr --version
    run_capture fwupdmgr-get-devices.txt fwupdmgr get-devices
    run_capture fwupdmgr-get-history.txt fwupdmgr get-history
else
    note "fwupdmgr not installed."
fi

section "Kernel / boot diagnostics"

if have dmesg; then
    run_capture dmesg-full.txt dmesg
    run_shell_capture dmesg-gpu-filtered.txt \
        "dmesg | grep -Ei 'nvidia|nouveau|vfio|iommu|pcie|pci.*error|aer|gsp|xid' || true"
fi

if have journalctl; then
    run_capture journal-kernel-current-boot.txt journalctl -k -b --no-pager
fi

copy_text_if_readable /proc/cmdline proc-cmdline.txt
copy_text_if_readable /proc/iomem proc-iomem.txt
copy_text_if_readable /proc/interrupts proc-interrupts.txt

section "Cross-check candidate ROM/VBIOS files"

{
    for f in \
        "$OUT/vbios-nvflash.rom" \
        "$OUT/pci-expansion-rom.bin" \
        "$OUT/pci-vpd.bin" \
        "$OUT/pci-config.bin"
    do
        if [ -f "$f" ]; then
            printf '%-32s size=%-10s sha256=%s\n' \
                "$(basename "$f")" \
                "$(stat -c '%s' "$f" 2>/dev/null || echo '?')" \
                "$(sha256sum "$f" 2>/dev/null | awk '{print $1}')"
        fi
    done
} | tee "$OUT/important-binary-files.txt"

section "Manifest"

# Hash everything currently in the collection except the manifest itself.
(
    cd "$OUT" || exit 1
    find . -type f ! -name SHA256SUMS -print0 \
        | sort -z \
        | xargs -0 sha256sum \
        > SHA256SUMS
)

wc -l "$OUT/SHA256SUMS"
sha256sum "$OUT/SHA256SUMS"

section "Archive"

archive="${OUT}.tar"
tar -C "$(dirname "$OUT")" -cf "$archive" "$(basename "$OUT")"

sha256sum "$archive" | tee "${archive}.sha256"

printf '\n'
printf 'Collection directory: %s\n' "$OUT"
printf 'Archive:              %s\n' "$archive"
printf 'Archive checksum:     %s\n' "${archive}.sha256"
printf '\n'

note "Done."
note "Best practice: run this once in the VM and once on the physical host with the VM stopped."
note "A software dump is still not equivalent to a full external-programmer dump of every flash/EEPROM chip."
