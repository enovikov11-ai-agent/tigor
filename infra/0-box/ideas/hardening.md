UKI+squashfs+secure boot repro build

lockdown

kata runtime

/dev/mem
/dev/kmem
ioremap of raw physical memory
MSR poking
kexec of unsigned kernels
loading unsigned kernel modules
hibernation
some BPF / perf / debug interfaces

{
  boot.kernelParams = [
    "lockdown=confidentiality"
    "module.sig_enforce=1"
    "iommu=pt"
  ];

  security.lockKernelModules = true;
}

block

/dev/mem
/dev/port
/dev/cpu/*/msr
flashrom
fwupd
efivarfs writes
SPI controller access
unsigned kernel modules

hardening

{
  boot.blacklistedKernelModules = [
    "msr"
    "mei"
    "mei_me"
  ];

  services.fwupd.enable = false;

  fileSystems."/sys/firmware/efi/efivars" = {
    device = "efivarfs";
    fsType = "efivarfs";
    options = [ "ro" ];
  };

  boot.kernel.sysctl = {
    "kernel.kptr_restrict" = 2;
    "kernel.dmesg_restrict" = 1;
    "kernel.unprivileged_bpf_disabled" = 1;
    "kernel.perf_event_paranoid" = 3;
  };
}

block

/dev/ipmi0
/dev/ipmi/*
ipmi_si
ipmi_devintf
LAN to BMC IP
SMBus/I2C paths
vendor-specific PCI/MMIO interfaces

{
  boot.blacklistedKernelModules = [
    "ipmi_si"
    "ipmi_devintf"
    "ipmi_msghandler"
    "ipmi_ssif"
  ];
}

stop

/dev/ipmi0
/dev/mem
/dev/cpu/*/msr
/sys/firmware/efi/efivars
/dev/i2c-*
/dev/spidev*

Firmware Secure Boot
  -> signed bootloader / systemd-boot
    -> signed UKI
      -> kernel lockdown
        -> signed modules only
          -> read-only root squashfs / dm-verity
            -> SELinux/AppArmor/systemd sandboxing

BIOS flash write-protect
BMC isolated from host
IPMI kernel modules disabled
fwupd disabled or tightly controlled
efivarfs read-only
