{
  description = "Stateless NixOS host and diskless UKI guest images";

  inputs = {
    # 2026-08-10 https://github.com/NixOS/nixpkgs/commits/nixos-26.05/
    nixpkgs.url = "github:NixOS/nixpkgs/fcb8fcd6bf2d0adecae5bd491afaaaf8311b758d";
  };

  outputs = { self, nixpkgs, ... }:
  let
    # For release candidates use r5-rc1 format
    revision = "r8-rc2";

    # Public password hash is a tradeoff between usability and security, underlying is high entropy
    sshKey = "sk-ssh-ed25519@openssh.com AAAAGnNrLXNzaC1lZDI1NTE5QG9wZW5zc2guY29tAAAAIMltMQTMSIcxPbZLNCxkAT/MWRqJo1IFOfH95OoscQbCAAAABHNzaDo= enovikov11@novikov.local";
    mainPassword = "$6$JsF575e4YV0MxwGU$aDy3BMHg/5lvWZoMvsAV0TL/BIcXMu3ps1DnOf3.o.hQ3IqT/sfCwKJHdMaaRy2exNAEUFxpxPbO966DE5cm./";

    lib = nixpkgs.lib;
    system = "x86_64-linux";

    gnomeModule = { scalingFactor, extras, includeVMManager ? false }:
      { lib, pkgs, ... }: {
        hardware.graphics.enable = true;

        services.xserver.enable = true;
        services.displayManager.gdm.enable = true;
        services.desktopManager.gnome.enable = true;

        environment.gnome.excludePackages = with pkgs; [
          gnome-backgrounds
          gnome-bluetooth
          gnome-color-manager
          gnome-tour
          gnome-user-docs
          gnome-menus
          orca
        ];

        hardware.bluetooth.enable = false;
        services.hardware.bolt.enable = false;
        i18n.inputMethod.enable = false;
        services.avahi.enable = false;
        services.colord.enable = false;
        services.dleyna.enable = false;
        services.geoclue2.enable = false;
        services.power-profiles-daemon.enable = false;
        services.orca.enable = false;
        services.upower.enable = lib.mkForce false;
        services.gnome = {
          core-apps.enable = false;
          evolution-data-server.enable = lib.mkForce false;
          gcr-ssh-agent.enable = false;
          gnome-browser-connector.enable = false;
          gnome-initial-setup.enable = false;
          gnome-keyring.enable = false;
          gnome-online-accounts.enable = false;
          gnome-remote-desktop.enable = false;
          gnome-user-share.enable = false;
          localsearch.enable = false;
          rygel.enable = false;
          tinysparql.enable = false;
        };

        services.pipewire = { enable = true; alsa.enable = true; pulse.enable = true; };

        programs.gnome-disks.enable = true;
        programs.firefox.enable = extras;

        environment.systemPackages = (with pkgs; [ nautilus gnome-console ])
          ++ lib.optionals extras (with pkgs; [ vscodium ]);

        environment.sessionVariables = lib.optionalAttrs extras { NIXOS_OZONE_WL = "1"; };

        xdg.mime.defaultApplications = { "inode/directory" = [ "org.gnome.Nautilus.desktop" ]; };

        programs.dconf.profiles = {
          gdm.databases = [{
            settings = {
              "org/gnome/desktop/interface".scaling-factor = lib.gvariant.mkUint32 scalingFactor;
              "org/gnome/settings-daemon/plugins/power" = {
                sleep-inactive-ac-type = "nothing";
                sleep-inactive-battery-type = "nothing";
              };
            };
          }];

          user.databases = [{
            settings = {
              "org/gnome/desktop/interface".scaling-factor = lib.gvariant.mkUint32 scalingFactor;
              "org/gnome/desktop/session".idle-delay = lib.gvariant.mkUint32 0;
              "org/gnome/settings-daemon/plugins/housekeeping".donation-reminder-enabled = false;
              "org/gnome/settings-daemon/plugins/power" = {
                sleep-inactive-ac-type = "nothing";
                sleep-inactive-battery-type = "nothing";
              };
              "org/gnome/shell".favorite-apps = [
                "org.gnome.Nautilus.desktop"
                "org.gnome.Console.desktop"
                "org.gnome.DiskUtility.desktop"
              ] ++ lib.optionals includeVMManager [ "virt-manager.desktop" ];
            };
          }];
        };
      };

    nvidiaModule = { gnome }:
      { config, lib, pkgs, ... }:
      let
        nvidiaSmi = lib.getExe' config.hardware.nvidia.package "nvidia-smi";
      in
      {
        hardware.graphics.enable = true;
        services.xserver.videoDrivers = [ "nvidia" ];
        hardware.nvidia = {
          branch = "production";
          modesetting.enable = gnome;
          open = true;
          nvidiaSettings = gnome;
          nvidiaPersistenced = true;
        };

        systemd.services.nvidia-profile = {
          description = "Configure NVIDIA GPU ECC and power profile";
          wantedBy = [ "multi-user.target" ];
          after = [ "nvidia-persistenced.service" ];
          wants = [ "nvidia-persistenced.service" ];
          serviceConfig = {
            Type = "oneshot"; RemainAfterExit = true; Restart = "on-failure"; RestartSec = "2s";
          };
          script = ''
            current="$(${nvidiaSmi} --query-gpu=ecc.mode.current --format=csv,noheader 2>&1)" || {
              echo "NVIDIA ECC status unavailable: $current"
              current=
            }
            if [[ -n "$current" ]] &&
               ${pkgs.gnugrep}/bin/grep -qv '^Enabled$' <<< "$current"; then
              ${nvidiaSmi} --ecc-config=1 ||
                echo "NVIDIA ECC is not configurable on this GPU in its current mode"
            fi
            ${nvidiaSmi} -pm 1 &&
              ${nvidiaSmi} -pl 450 &&
              ${nvidiaSmi} --lock-gpu-clocks=300,2400
          '';
        };

      };

    containersModule = { pkgs, ... }: {
      virtualisation.podman = { enable = true; extraRuntimes = [ pkgs.gvisor ]; };
      environment.systemPackages = with pkgs; [ podman podman-compose gvisor ];
    };

    nvidiaContainerToolkitModule = { lib, pkgs, ... }: {
      hardware.nvidia-container-toolkit.enable = true;

      environment.etc."nvidia-container-runtime/config.toml".text = ''
        [nvidia-container-runtime-hook]
        path = "${pkgs.nvidia-container-toolkit.tools}/bin/nvidia-container-runtime-hook"

        [nvidia-ctk]
        path = "${pkgs.nvidia-container-toolkit}/bin/nvidia-ctk"

        [features]
        disable-cuda-compat-lib-hook = true
      '';
    };

    stateless = { vm ? false, gnome ? false, extras ? false, tools ? false, nvidia ? false,
      containers ? false, hypervisor ? false, vfio ? false, sudo ? false, password ? "",
      scalingFactor ? 1 }:
      let
    commonModule = { vm, tools, gnome, nvidia, hypervisor, vfio, sudo, password, imageBaseName }:
      { lib, pkgs, ... }: {
        assertions = [{
          assertion = !vfio || (!vm && hypervisor);
          message = "vfio requires a physical hypervisor host";
        }];

        time.timeZone = "Europe/Belgrade";
        i18n.defaultLocale = "en_US.UTF-8";

        nixpkgs.config.allowUnfreePredicate = pkg: lib.hasPrefix "nvidia-" (lib.getName pkg);
        nix.settings.experimental-features = [ "nix-command" "flakes" ];

        networking.hostName = imageBaseName;
        networking.firewall.enable = true;

        services.openssh = {
          enable = true;
          generateHostKeys = true;
          openFirewall = true;
          settings = {
            AuthenticationMethods = "publickey";
            PasswordAuthentication = false;
            KbdInteractiveAuthentication = false;
            PermitEmptyPasswords = false;
            X11Forwarding = false;
            PermitRootLogin = "prohibit-password";
            AllowUsers = [ "root" "nixos" ];
          };
        };

        security.sudo = { enable = sudo; }
          // lib.optionalAttrs sudo { wheelNeedsPassword = false; };

        users.mutableUsers = false;
        users.users = {
          root = { hashedPassword = password; openssh.authorizedKeys.keys = [ sshKey ]; };

          nixos = {
            isNormalUser = true;
            hashedPassword = password;
            extraGroups = lib.optionals sudo [ "wheel" ]
              ++ lib.optionals hypervisor [ "kvm" "libvirtd" ]
              ++ lib.optionals (gnome || nvidia) [ "video" "render" ];
            openssh.authorizedKeys.keys = [ sshKey ];
          };
        };
        users.groups.kvm.members = lib.optionals hypervisor [ "qemu-libvirtd" ];

        system.stateVersion = "26.05";

        environment.etc."nixos/flake.nix".source = ./flake.nix;

        environment.systemPackages =
          (with pkgs; [ curl git htop python3 tmux vim tree wireguard-tools jq ])
          ++ lib.optionals tools (with pkgs; [ pciutils usbutils dmidecode ethtool ]);
      };

    vmModule = { vm, imageBaseName, gnome }:
          ({ config, lib, modulesPath, pkgs, ... }: lib.mkIf vm {
          imports = [ (modulesPath + "/installer/netboot/netboot.nix") ];

          boot.kernelModules = [ "virtiofs" ];
          boot.uki.name = imageBaseName;
          boot.uki.version = null;
          boot.uki.settings.UKI.Initrd = lib.mkForce "${config.system.build.netbootRamdisk}/initrd";

          services.qemuGuest.enable = true;
          services.spice-vdagentd.enable = gnome;
          systemd.services.mount-virtiofs-shares = {
            description = "Mount virtiofs path shares";
            wantedBy = [ "multi-user.target" ];
            after = [ "systemd-modules-load.service" ];
            serviceConfig.Type = "oneshot";
            path = with pkgs; [ coreutils util-linux ];
            script = ''
              shopt -s nullglob
              for tagFile in /sys/fs/virtiofs/*/tag; do
                IFS= read -r path < "$tagFile"
                mkdir -p -- "$path"
                mount -t virtiofs -- "$path" "$path"
              done
            '';
          };
          services.displayManager.autoLogin = lib.mkIf gnome {
            enable = true;
            user = "nixos";
          };

          });

        imageTags =
          lib.optionals gnome [ "gui" ]
          ++ lib.optionals containers [ "pod" ]
          ++ lib.optionals nvidia [ "nv" ];
        imageBaseName =
          (if vm then "vm" else "stateless")
          + lib.optionalString (imageTags != [ ])
            "-${lib.concatStringsSep "-" imageTags}"
          + "-${revision}";
        efiName = imageBaseName + lib.optionalString (!vm) "-BOOTX64";
      in
      lib.nixosSystem {
        inherit system;

        modules =
          [ (commonModule {
              inherit vm tools gnome nvidia hypervisor vfio sudo password imageBaseName;
            }) ]
          ++ lib.optional vm "${nixpkgs}/nixos/modules/profiles/qemu-guest.nix"
          ++ lib.optional gnome (gnomeModule { inherit extras scalingFactor; includeVMManager = hypervisor; })
          ++ lib.optional nvidia (nvidiaModule { inherit gnome; })
          ++ lib.optional containers containersModule
          ++ lib.optional (containers && nvidia) nvidiaContainerToolkitModule
          ++ [
          ({ config, lib, pkgs, modulesPath, ... }: lib.mkIf (!vm) {

          nix.settings.max-jobs = 4;
          nix.settings.cores = 32;

          services.udev.extraRules = lib.optionalString hypervisor ''
            SUBSYSTEM=="misc", KERNEL=="sev", GROUP="kvm", MODE="0660"
          '';

          imports = [ (modulesPath + "/installer/netboot/netboot.nix") (modulesPath + "/profiles/minimal.nix") ];

          networking.hostId = "06e694f9";
          networking.nftables.enable = true;
          networking.networkmanager.enable = false;

          boot.supportedFilesystems = [ "zfs" ];

          # NVIDIA GeForce GT 710
          boot.initrd.kernelModules =
            lib.optionals vfio [ "vfio_pci" "vfio" "vfio_iommu_type1" ]
            ++ lib.optionals (gnome && !nvidia) [ "nouveau" ];
          boot.kernelModules = lib.optionals hypervisor [ "kvm-amd" ];
          boot.kernelParams = [ "nohibernate" "modprobe.blacklist=ast" "transparent_hugepage=madvise" ]
            ++ lib.optionals hypervisor [
              "kvm_amd.sev=1"
              "kvm_amd.sev_es=1"
              "amd_iommu=on"
              "iommu=pt"
              "iommu.strict=1"
            ]
            ++ lib.optionals vfio [
              # 41:00.0 RTX PRO 6000 and 41:00.1 HDMI audio.
              "vfio-pci.ids=10de:2bb1,10de:22e8"
            ];
          boot.blacklistedKernelModules = [ "ast" ];

          systemd.tmpfiles.rules = [ "w /sys/kernel/mm/transparent_hugepage/defrag - - - - defer" ];

          boot.uki.name = efiName;
          boot.uki.version = null;
          boot.uki.settings.UKI.Initrd = lib.mkForce "${config.system.build.netbootRamdisk}/initrd";

          boot.zfs.forceImportRoot = false;

          services.xserver.videoDrivers = lib.mkIf (gnome && !nvidia) [ "nouveau" ];

          programs.virt-manager.enable = hypervisor;

          virtualisation.libvirtd = lib.mkIf hypervisor {
            enable = true;
            onBoot = "ignore";
            onShutdown = "shutdown";
            firewallBackend = "nftables";
            qemu = {
              package = pkgs.qemu_kvm;

              runAsRoot = false;

              verbatimConfig = ''
                namespaces = []
                seccomp_sandbox = 1
                spice_auto_unix_socket = 1
                vnc_auto_unix_socket = 1
              '';

              vhostUserPackages = [ pkgs.virtiofsd ];
            };
          };

          systemd.services.virt-secret-init-encryption = lib.mkIf hypervisor {
            serviceConfig = {
              StateDirectory = "libvirt/secrets";
              StateDirectoryMode = "0700";
              ExecStart = lib.mkForce [
                ""
                (pkgs.writeShellScript "virt-secret-init-encryption" ''
                  umask 0077
                  ${pkgs.coreutils}/bin/chmod 0700 /var/lib/libvirt/secrets
                  ${pkgs.coreutils}/bin/dd if=/dev/random status=none bs=32 count=1 | \
                    ${pkgs.systemd}/bin/systemd-creds encrypt --with-key=tpm2-absent \
                      --name=secrets-encryption-key \
                      - /var/lib/libvirt/secrets/secrets-encryption-key
                '')
              ];
            };
          };

          environment.systemPackages =
            (with pkgs; [ zfs ])
            ++ lib.optionals tools (with pkgs; [
              smartmontools
              nvme-cli
              lm_sensors
              hdparm
              ipmitool
              efibootmgr
            ])
            ++ lib.optionals hypervisor (with pkgs; [
              qemu_kvm
              libvirt
              openssl
              virt-manager
              passt
              virtiofsd
            ]);

          environment.shellAliases = {
            mnt = "zpool import -a && zfs load-key -a && zfs mount -a";
          };

          systemd.targets.sleep.enable = false;
          systemd.targets.suspend.enable = false;
          systemd.targets.hibernate.enable = false;
          systemd.targets.hybrid-sleep.enable = false;
          })
            (vmModule { inherit vm imageBaseName gnome; })
        ];
      };
  in
  {
    nixosConfigurations = {
      host = stateless {
        gnome = true;
        tools = true;
        hypervisor = true;
        vfio = true;
        sudo = true;
        password = mainPassword;
        scalingFactor = 2;
      };
      vm = stateless {
        vm = true;
        tools = true;
        nvidia = true;
        containers = true;
        sudo = true;
      };
    };

    packages.${system} = {
      host = self.nixosConfigurations.host.config.system.build.uki;
      vm = self.nixosConfigurations.vm.config.system.build.uki;
    };
  };
}
