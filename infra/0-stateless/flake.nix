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

    guestNvidiaModule = { gnome }:
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

        systemd.services.nvidia-ecc = {
          description = "Enable NVIDIA GPU ECC when supported";
          wantedBy = [ "multi-user.target" ];
          after = [ "nvidia-persistenced.service" ];
          wants = [ "nvidia-persistenced.service" ];
          serviceConfig = {
            Type = "oneshot";
            RemainAfterExit = true;
            ExecStart = pkgs.writeShellScript "enable-nvidia-ecc" ''
              current="$(${nvidiaSmi} --query-gpu=ecc.mode.current --format=csv,noheader 2>&1)" || {
                echo "NVIDIA ECC status unavailable: $current"
                exit 0
              }
              if ${pkgs.gnugrep}/bin/grep -qv '^Enabled$' <<< "$current"; then
                ${nvidiaSmi} --ecc-config=1 || \
                  echo "NVIDIA ECC is not configurable on this GPU in its current mode"
              fi
            '';
          };
        };

        systemd.services."nvidia-power-limit" = {
          description = "Set NVIDIA GPU stable profile";
          wantedBy = [ "multi-user.target" ];
          after = [ "network-online.target" ];
          wants = [ "network-online.target" ];
          path = [ config.boot.kernelPackages.nvidia_x11 ];
          serviceConfig = {
            Type = "oneshot";
            RemainAfterExit = true;
            ExecStart = "${pkgs.bash}/bin/bash -c 'nvidia-smi -pm 1 && nvidia-smi -pl 450 && nvidia-smi --lock-gpu-clocks=300,2400'";
          };
        };
      };

    guestContainersModule = { pkgs, ... }: {
      virtualisation.podman = { enable = true; extraRuntimes = [ pkgs.gvisor ]; };
      environment.systemPackages = with pkgs; [ podman podman-compose gvisor ];
    };

    guestNvidiaContainerToolkitModule = { lib, pkgs, ... }: {
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

    commonModule = { tools }:
      { lib, pkgs, ... }: {
        time.timeZone = "Europe/Belgrade";
        i18n.defaultLocale = "en_US.UTF-8";

        nixpkgs.config.allowUnfreePredicate = pkg: lib.hasPrefix "nvidia-" (lib.getName pkg);
        nix.settings.experimental-features = [ "nix-command" "flakes" ];

        networking.firewall.enable = true;

        services.openssh = {
          enable = true;
          generateHostKeys = true;
          settings = {
            AuthenticationMethods = "publickey";
            PasswordAuthentication = false;
            KbdInteractiveAuthentication = false;
            PermitEmptyPasswords = false;
            X11Forwarding = false;
          };
        };

        users.mutableUsers = false;
        system.stateVersion = "26.05";

        environment.etc."nixos/flake.nix".source = ./flake.nix;

        environment.systemPackages =
          (with pkgs; [ curl git htop python3 tmux vim tree wireguard-tools jq ])
          ++ lib.optionals tools (with pkgs; [ pciutils usbutils dmidecode ethtool ]);
      };

    stateless = { gnome, extras, tools, virtualization, sudo, password, scalingFactor ? 1 }:
      lib.nixosSystem {
        inherit system;

        modules =
          [ (commonModule { inherit tools; }) ]
          ++ lib.optional gnome (gnomeModule { inherit extras scalingFactor; includeVMManager = virtualization; })
          ++ [
          ({ config, lib, pkgs, modulesPath, ... }: {

          nix.settings.max-jobs = 4;
          nix.settings.cores = 32;

          services.openssh.settings = { PermitRootLogin = "prohibit-password"; AllowUsers = [ "root" "nixos" ]; };

          security.sudo = { enable = sudo; }
            // lib.optionalAttrs sudo { wheelNeedsPassword = false; };

          users.users = {
            root = { hashedPassword = password; openssh.authorizedKeys.keys = [ sshKey ]; };

            nixos = {
              isNormalUser = true;
              hashedPassword = password;
              extraGroups = lib.optionals sudo [ "wheel" ]
                ++ lib.optionals virtualization [ "kvm" "libvirtd" ]
                ++ lib.optionals gnome [ "video" "render" ];
              openssh.authorizedKeys.keys = [ sshKey ];
            };
          };
          users.groups.kvm.members = lib.optionals virtualization [ "qemu-libvirtd" ];

          services.udev.extraRules = lib.optionalString virtualization ''
            SUBSYSTEM=="misc", KERNEL=="sev", GROUP="kvm", MODE="0660"
          '';

          imports = [ (modulesPath + "/installer/netboot/netboot.nix") (modulesPath + "/profiles/minimal.nix") ];

          networking.hostName = "stateless-${revision}";
          networking.hostId = "06e694f9";
          networking.nftables.enable = true;
          networking.networkmanager.enable = false;

          boot.supportedFilesystems = [ "zfs" ];

          # NVIDIA GeForce GT 710
          boot.initrd.kernelModules =
            lib.optionals virtualization [ "vfio_pci" "vfio" "vfio_iommu_type1" ]
            ++ lib.optionals gnome [ "nouveau" ];
          boot.kernelModules = lib.optionals virtualization [ "kvm-amd" ];
          boot.kernelParams = [ "nohibernate" "modprobe.blacklist=ast" "transparent_hugepage=madvise" ]
            ++ lib.optionals virtualization [
              "kvm_amd.sev=1"
              "kvm_amd.sev_es=1"
              "amd_iommu=on"
              "iommu=pt"
              "iommu.strict=1"
              # 41:00.0 RTX PRO 6000 and 41:00.1 HDMI audio.
              "vfio-pci.ids=10de:2bb1,10de:22e8"
            ];
          boot.blacklistedKernelModules = [ "ast" ];

          systemd.tmpfiles.rules = [ "w /sys/kernel/mm/transparent_hugepage/defrag - - - - defer" ];

          boot.uki.name = "BOOTX64";
          boot.uki.version = null;
          boot.uki.settings.UKI.Initrd = lib.mkForce "${config.system.build.netbootRamdisk}/initrd";

          boot.zfs.forceImportRoot = false;

          services.xserver.videoDrivers = lib.mkIf gnome [ "nouveau" ];

          programs.virt-manager.enable = virtualization;

          virtualisation.libvirtd = lib.mkIf virtualization {
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

          systemd.services.virt-secret-init-encryption = lib.mkIf virtualization {
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
            ++ lib.optionals virtualization (with pkgs; [
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
        ];
      };

    vm = { gnome, extras, tools, nvidia, containers, sudo, password, scalingFactor ? 1 }:
      let
        imageTags =
          lib.optionals gnome [ "gui" ]
          ++ lib.optionals containers [ "pod" ]
          ++ lib.optionals nvidia [ "nv" ];
        imageBaseName =
          "vm"
          + lib.optionalString (imageTags != [ ])
            "-${lib.concatStringsSep "-" imageTags}"
          + "-${revision}";
      in
      lib.nixosSystem {
        inherit system;

        modules =
          [
            (commonModule { inherit tools; })
            "${nixpkgs}/nixos/modules/profiles/qemu-guest.nix"
          ]
          ++ lib.optional gnome (gnomeModule {
            inherit extras scalingFactor;
          })
          ++ lib.optional nvidia (guestNvidiaModule { inherit gnome; })
          ++ lib.optional containers guestContainersModule
          ++ lib.optional (containers && nvidia) guestNvidiaContainerToolkitModule
          ++ [

          ({ config, lib, modulesPath, pkgs, ... }: {
          imports = [ (modulesPath + "/installer/netboot/netboot.nix") ];

          networking.hostName = imageBaseName;

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

          services.openssh = {
            openFirewall = true;
            settings = {
              PermitRootLogin = "prohibit-password";
              AllowUsers = [ "root" "nixos" ];
            };
          };

          security.sudo = { enable = sudo; }
            // lib.optionalAttrs sudo { wheelNeedsPassword = false; };

          users.users = {
            root = {
              hashedPassword = password;
              openssh.authorizedKeys.keys = [ sshKey ];
            };

            nixos = {
              isNormalUser = true;
              extraGroups =
                lib.optionals sudo [ "wheel" ]
                ++ lib.optionals (gnome || nvidia) [ "video" "render" ];
              hashedPassword = password;
              openssh.authorizedKeys.keys = [ sshKey ];
            };
          };
          })
        ];
      };
  in
  {
    nixosConfigurations = {
      stateless = stateless {
        gnome = true;
        extras = false;
        tools = true;
        virtualization = true;
        sudo = true;
        password = mainPassword;
        scalingFactor = 2;
      };
      vm = vm {
        gnome = false;
        extras = false;
        tools = true;
        nvidia = true;
        containers = true;
        sudo = true;
        password = "";
      };
    };

    packages.${system} = {
      default = self.nixosConfigurations.stateless.config.system.build.uki;
      vm = self.nixosConfigurations.vm.config.system.build.uki;
    };
  };
}
