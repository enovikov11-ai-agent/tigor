{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, nixpkgs-unstable }:
  let
    sshKey = "sk-ssh-ed25519@openssh.com AAAAGnNrLXNzaC1lZDI1NTE5QG9wZW5zc2guY29tAAAAIMltMQTMSIcxPbZLNCxkAT/MWRqJo1IFOfH95OoscQbCAAAABHNzaDo= enovikov11@novikov.local";
    mainPassword = "$6$JsF575e4YV0MxwGU$aDy3BMHg/5lvWZoMvsAV0TL/BIcXMu3ps1DnOf3.o.hQ3IqT/sfCwKJHdMaaRy2exNAEUFxpxPbO966DE5cm./";

    lib = nixpkgs.lib;
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
    pkgs-unstable = import nixpkgs-unstable {
      inherit system;
      config = { allowUnfree = true; cudaSupport = true; };
    };
    hostPrivateKey = pkgs.runCommandLocal "ephemeral-host-private-key" { } ''
      umask 077
      tmp="$(mktemp -d)"
      ${pkgs.openssh}/bin/ssh-keygen -q -t ed25519 -N "" -f "$tmp/ssh_host_ed25519_key"
      cp "$tmp/ssh_host_ed25519_key" $out
    '';

    commonBase = { lib, ... }: {
      time.timeZone = "Europe/Belgrade";
      i18n.defaultLocale = "en_US.UTF-8";

      nixpkgs.config.allowUnfree = true;

      nix.channel.enable = false;
      nix.nixPath = lib.mkForce [ ];
      nix.settings = {
        experimental-features = [ "nix-command" "flakes" ];
        cores = 64;
        max-jobs = 4;
        download-buffer-size = "1G";
      };

      networking.firewall.enable = true;

      services.openssh = {
        enable = true;

        settings = {
          PasswordAuthentication = false;
          KbdInteractiveAuthentication = false;
          PermitRootLogin = "prohibit-password";
          X11Forwarding = false;
          AllowUsers = [ "root" ];
        };
      };

      users.mutableUsers = false;
      users.users.root = { hashedPassword = mainPassword; openssh.authorizedKeys.keys = [ sshKey ]; };

      system.stateVersion = "25.11";
    };

    hostBase = lib.nixosSystem {
      inherit system;

      modules = [
        commonBase

        ({ config, lib, pkgs, modulesPath, ... }: {
          imports = [ "${modulesPath}/installer/netboot/netboot.nix" "${modulesPath}/profiles/minimal.nix" ];

          networking.hostName = "ephemeral";
          networking.hostId = "06e694f9";
          networking.nftables.enable = true;

          boot.supportedFilesystems = [ "zfs" ];

          boot.kernelModules = [ "kvm-amd" ];
          boot.kernelParams = [ "nohibernate" "amd_iommu=on" "iommu.strict=1" "modprobe.blacklist=ast" ];
          boot.blacklistedKernelModules = [ "ast" ];

          boot.uki.name = "BOOTX64";
          boot.uki.settings.UKI.Initrd = lib.mkForce "${config.system.build.netbootRamdisk}/initrd";

          boot.zfs.forceImportRoot = false;

          virtualisation.libvirtd = {
            enable = true;
            onBoot = "ignore";
            onShutdown = "shutdown";
            firewallBackend = "nftables";
            qemu = {
              package = pkgs.qemu_kvm;
              vhostUserPackages = [ pkgs.virtiofsd ];
            };
          };

          services.openssh.hostKeys = [{
            path = "/etc/ephemeral/ssh_host_ed25519_key";
            type = "ed25519";
          }];
          environment.etc."ephemeral/ssh_host_ed25519_key" = { source = hostPrivateKey; mode = "0400"; };
          environment.systemPackages = with pkgs; [ vim curl htop tmux zfs qemu_kvm libvirt virt-manager passt virtiofsd wireguard-tools ];
          environment.shellAliases = { mnt = "zpool import -a && zfs load-key -a && zfs mount -a"; };

          systemd.services.libvirtd.path = [ pkgs.passt ];

          networking.wireguard.interfaces = {};

          systemd.targets.sleep.enable = false;
          systemd.targets.suspend.enable = false;
          systemd.targets.hibernate.enable = false;
          systemd.targets.hybrid-sleep.enable = false;
        })
      ];
    };

    host = hostBase.extendModules {
      modules = [
        ({ ... }: {
          networking.wireguard.interfaces.wg0 = {
            ips = [ "10.69.42.2/24" ];
            privateKeyFile = "/ssd/private/ephemeral/wireguard/wg0.key";

            peers = [{
              publicKey = "NHtNDaxbhUQ5y7L3lOqRbUwIPnvtoypVdHpL+FLAEA4=";
              endpoint = "tgr.rs:44222";
              allowedIPs = [ "10.69.42.0/24" ];
              persistentKeepalive = 25;
            }];
          };

          systemd.tmpfiles.rules = [
            "z /ssd/private/ephemeral/wireguard/wg0.key 0600 root root -"
          ];

          networking.firewall.enable = lib.mkForce false;
        })
      ];
    };

    cloudHypervisorVm = lib.nixosSystem {
      inherit system;

      modules = [
        "${nixpkgs}/nixos/modules/image/repart.nix"
        ({ config, lib, modulesPath, pkgs, ... }:
        let
          nvidiaPkg = config.boot.kernelPackages.nvidiaPackages.stable;
          modelPath = "/ssd/internet/huggingface.co/unsloth/Qwen3.6-27B-GGUF/Qwen3.6-27B-Q4_K_M.gguf";
          opencode-config = pkgs.writeText "opencode.jsonc" ''
            {
              "$schema": "https://opencode.ai/config.json",
              "permission": {
                "*": "allow",
                "doom_loop": "deny"
              },
              "provider": {
                "local": {
                  "npm": "@ai-sdk/openai-compatible",
                  "name": "local",
                  "options": {
                    "baseURL": "http://127.0.0.1:8080/v1"
                  },
                  "models": {
                    "qwen3.6-27b": {
                      "name": "qwen3.6-27b",
                      "limit": {
                        "context": 32768,
                        "output": 8192
                      }
                    }
                  }
                }
              }
            }
          '';
          start-llama = pkgs.writeShellScriptBin "start-llama" ''
            exec llama-server \
              -m ${modelPath} \
              -ngl 999 \
              --host 127.0.0.1 --port 8080 \
              -c 32768 \
              --jinja \
              --alias qwen3.6-27b
          '';
          check-llama = pkgs.writeShellScriptBin "check-llama" ''
            echo "=== /v1/models ==="
            curl -s http://127.0.0.1:8080/v1/models | jq .
            echo
            echo "=== /health ==="
            curl -s http://127.0.0.1:8080/health
            echo
          '';
          start-agent = pkgs.writeShellScriptBin "start-agent" ''
            cp ${opencode-config} /root/opencode.jsonc
            cd /root
            while true; do
              echo "[$(date)] Starting opencode agent..."
              opencode run "you are autonomous agent in the loop, do something cool with /ssd/home/monorepo for rw use /root" || true
              echo "[$(date)] opencode exited, restarting in 5s..."
              sleep 5
            done
          '';
        in {
          imports = [ "${modulesPath}/profiles/minimal.nix" ];

          system.stateVersion = "25.11";

          image = {
            baseName = "nixos-cloud-hypervisor";
            repart = {
              name = "nixos-cloud-hypervisor";
              compression.enable = false;
              partitions."10-root" = {
                storePaths = [ config.system.build.toplevel ];
                repartConfig = {
                  Type = "linux-generic";
                  Format = "ext4";
                  Label = "nixos";
                  ReadOnly = true;
                  Minimize = "guess";
                  SizeMinBytes = "4G";
                };
              };
            };
          };

          fileSystems."/" = {
            device = "/dev/vda1";
            fsType = "ext4";
          };

          fileSystems."/ssd" = {
            device = "ssd";
            fsType = "virtiofs";
            options = [ "ro" ];
          };

          boot = {
            kernelParams = [
              "console=ttyS0,115200n8"
              "earlyprintk=serial"
              "panic=1"
              "boot.panic_on_fail"
            ];

            initrd.availableKernelModules = [
              "virtio_blk"
              "virtio_pci"
              "virtio_console"
              "virtiofs"
              "ext4"
              "vfio_pci"
            ];

            loader = {
              timeout = 0;
              grub = {
                devices = [ "/dev/vda" ];
                configurationLimit = 1;
              };
            };

            blacklistedKernelModules = [ "nouveau" "nvidiafb" ];
            extraModulePackages = [ nvidiaPkg.open ];
            kernelModules = [ "nvidia" "nvidia_uvm" ];
          };

          hardware.firmware = [ nvidiaPkg.firmware ];
          hardware.graphics.extraPackages = [ nvidiaPkg.out ];

          hardware.nvidia = {
            modesetting.enable = true;
            open = true;
          };
          nixpkgs.config.allowUnfree = true;
          nix.channel.enable = false;
          nix.nixPath = lib.mkForce [ ];
          nix.settings = {
            experimental-features = [ "nix-command" "flakes" ];
            cores = 64;
            max-jobs = 4;
            download-buffer-size = "1G";
          };

          systemd.services."nvidia-power-limit" = {
            description = "Set NVIDIA GPU stable profile";
            wantedBy = [ "multi-user.target" ];
            after = [ "network-online.target" ];
            wants = [ "network-online.target" ];
            path = [ nvidiaPkg.bin ];
            serviceConfig = {
              Type = "oneshot";
              RemainAfterExit = true;
              ExecStart = "${pkgs.bash}/bin/bash -c 'nvidia-smi -pm 1 && nvidia-smi -pl 450 && nvidia-smi --lock-gpu-clocks=300,2400'";
            };
          };

          users.users.agent = {
            isNormalUser = true;
            initialPassword = "agent";
            extraGroups = [ "video" "render" ];
          };

          services = {
            getty.autologinUser = "root";
            journald.console = "/dev/ttyS0";
          };

          networking = {
            hostName = "cloud-hypervisor-nixos";
            useDHCP = false;
            useNetworkd = false;
            firewall.enable = false;
          };

          users.users.root.initialPassword = "root";

          documentation.enable = false;
          environment.defaultPackages = lib.mkForce [ ];
          environment.systemPackages = [
            nvidiaPkg.bin
            pkgs.pciutils
            pkgs.vim
            pkgs.openssl
            pkgs.file
            pkgs.tree
            pkgs.dig
            pkgs.curl
            pkgs.wget
            pkgs.python3
            pkgs.git
            pkgs.python3Packages.huggingface-hub
            pkgs.opencode
            pkgs.ripgrep
            pkgs.fd
            pkgs.jq
            pkgs.gnumake
            pkgs.cmake
            pkgs.gcc
            pkgs.go
            pkgs.nodejs
            pkgs.rustc
            pkgs.cargo
            pkgs.tmux
            pkgs.htop
            pkgs.unzip
            pkgs.zip
            pkgs.less
            start-llama
            start-agent
            check-llama
          ];

          environment.etc."opencode.jsonc".source = opencode-config;
        })
      ];
    };

    cloudHypervisorCmdline = "root=/dev/vda1 init=${cloudHypervisorVm.config.system.build.toplevel}/init ${toString cloudHypervisorVm.config.boot.kernelParams}";

    cloudHypervisorArtifacts = pkgs.runCommand "nixos-cloud-hypervisor-vm" { } ''
      mkdir -p $out
      cp --sparse=always ${cloudHypervisorVm.config.system.build.image}/${cloudHypervisorVm.config.image.fileName} $out/disk.raw
      ln -s ${cloudHypervisorVm.config.system.build.kernel}/${cloudHypervisorVm.config.system.boot.loader.kernelFile} $out/kernel
      ln -s ${cloudHypervisorVm.config.system.build.initialRamdisk}/${cloudHypervisorVm.config.system.boot.loader.initrdFile} $out/initrd

      cat > $out/run <<EOF
#!/bin/sh
set -eu

if [ -f /run/ch-virtiofs.pid ]; then
  kill \$(cat /run/ch-virtiofs.pid) 2>/dev/null || true
  rm -f /run/ch-virtiofs.pid
fi

modprobe vfio-pci 2>/dev/null || true

echo 0000:40:01.1 > /sys/bus/pci/devices/0000:40:01.1/driver/unbind 2>/dev/null || true

for dev in 0000:41:00.0 0000:41:00.1; do
  if [ -d /sys/bus/pci/devices/\$dev/driver ]; then
    echo \$dev > /sys/bus/pci/devices/\$dev/driver/unbind 2>/dev/null || true
  fi
done

echo 1 > /sys/bus/pci/devices/0000:41:00.0/reset 2>/dev/null || true

for dev in 0000:41:00.0 0000:41:00.1; do
  echo vfio-pci > /sys/bus/pci/devices/\$dev/driver_override 2>/dev/null || true
  echo \$dev > /sys/bus/pci/drivers_probe 2>/dev/null || true
done

echo 0000:40:01.1 > /sys/bus/pci/drivers/pcieport/bind 2>/dev/null || true

rm -f /tmp/ch-disk.raw /tmp/ch-virtiofs.sock
cp --sparse=always ./disk.raw /tmp/ch-disk.raw
chmod u+w /tmp/ch-disk.raw

virtiofsd --shared-dir /ssd --socket-path /tmp/ch-virtiofs.sock --readonly --sandbox namespace &
echo \$! > /run/ch-virtiofs.pid

sleep 1

exec cloud-hypervisor \\
  --cpus boot=16 \\
  --memory size=32768M,shared=on \\
  --kernel ./kernel \\
  --initramfs ./initrd \\
  --cmdline '${cloudHypervisorCmdline}' \\
  --disk path=/tmp/ch-disk.raw,image_type=raw \\
  --device path=/sys/bus/pci/devices/0000:41:00.0 path=/sys/bus/pci/devices/0000:41:00.1 \\
  --fs tag=ssd,socket=/tmp/ch-virtiofs.sock \\
  --serial tty \\
  --console off
EOF
      chmod +x $out/run
    '';
  in
  {
    nixosConfigurations = {
      inherit hostBase;
      inherit host;
      inherit cloudHypervisorVm;
    };

    packages.${system} = {
      hostBase = hostBase.config.system.build.uki;
      host = host.config.system.build.toplevel;
      cloudHypervisorVm = cloudHypervisorArtifacts;
      cloudHypervisorImage = cloudHypervisorVm.config.system.build.image;
      cloudHypervisorRun = cloudHypervisorArtifacts;
    };

    apps.${system}.cloudHypervisorVm = {
      type = "app";
      program = "${cloudHypervisorArtifacts}/run";
    };
  };
}
