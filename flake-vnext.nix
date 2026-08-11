{
  inputs = {
    # 2026-08-10 https://github.com/NixOS/nixpkgs/commits/nixos-26.05/
    nixpkgs.url = "github:NixOS/nixpkgs/fcb8fcd6bf2d0adecae5bd491afaaaf8311b758d";
  };

  outputs = { nixpkgs, ... }:
  let
    # Public password hash is a tradeoff between usability and security, underlying is high entropy
    sshKey = "sk-ssh-ed25519@openssh.com AAAAGnNrLXNzaC1lZDI1NTE5QG9wZW5zc2guY29tAAAAIMltMQTMSIcxPbZLNCxkAT/MWRqJo1IFOfH95OoscQbCAAAABHNzaDo= enovikov11@novikov.local";
    mainPassword = "$6$JsF575e4YV0MxwGU$aDy3BMHg/5lvWZoMvsAV0TL/BIcXMu3ps1DnOf3.o.hQ3IqT/sfCwKJHdMaaRy2exNAEUFxpxPbO966DE5cm./";

    lib = nixpkgs.lib;
    system = "x86_64-linux";

    enableGnome = true;
    enableExtras = true; # Firefox and VSCodium
    enableTools = true;  # Hardware inspection and maintenance
    enableVMs = true;    # QEMU, libvirt, virt-manager and passthrough

    stateless = lib.nixosSystem {
      inherit system;

      modules = [
        ({ config, lib, pkgs, modulesPath, ... }: {
          time.timeZone = "Europe/Belgrade";
          i18n.defaultLocale = "en_US.UTF-8";

          nixpkgs.config.allowUnfree = true;

          nix.settings = {
            experimental-features = [
              "nix-command"
              "flakes"
            ];

            # Four concurrent builds, each sized for one quarter of the EPYC 7702P's 128 logical CPUs.
            max-jobs = 4;
            cores = 32;
          };

          networking.firewall.enable = true;

          services.openssh = {
            enable = true;
            generateHostKeys = true;

            settings = {
              PasswordAuthentication = false;
              KbdInteractiveAuthentication = false;
              PermitRootLogin = "prohibit-password";
              X11Forwarding = false;
              AllowUsers = [ "root" "box" ];
            };
          };

          users.mutableUsers = false;
          users.users = {
            root = {
              hashedPassword = mainPassword;
              openssh.authorizedKeys.keys = [ sshKey ];
            };

            box = {
              isNormalUser = true;
              hashedPassword = mainPassword;
              extraGroups =
                [ "wheel" ]
                ++ lib.optionals enableVMs [ "kvm" "libvirtd" ]
                ++ lib.optionals enableGnome [ "video" "render" ];
              openssh.authorizedKeys.keys = [ sshKey ];
            };
          };

          system.stateVersion = "26.05";

          imports = [
            (modulesPath + "/installer/netboot/netboot.nix")
            (modulesPath + "/profiles/minimal.nix")
          ];

          networking.hostName = "stateless";
          networking.hostId = "06e694f9";
          networking.nftables.enable = true;
          networking.networkmanager.enable = false;

          boot.supportedFilesystems = [ "zfs" ];

          boot.initrd.kernelModules =
            lib.optionals enableVMs [
              "vfio_pci"
              "vfio"
              "vfio_iommu_type1"
            ]
            ++ lib.optionals enableGnome [
              # The NVIDIA GeForce GT 710 is Kepler and must use Nouveau.
              # VFIO modules precede it so the RTX PRO IDs are claimed first.
              "nouveau"
            ];
          boot.kernelModules = lib.optionals enableVMs [ "kvm-amd" ];
          boot.kernelParams =
            [
              "nohibernate"
              "modprobe.blacklist=ast"
            ]
            ++ lib.optionals enableVMs [
              "amd_iommu=on"
              "iommu=pt"
              "iommu.strict=1"
              # 41:00.0 RTX PRO 6000 and 41:00.1 HDMI audio.
              "vfio-pci.ids=10de:2bb1,10de:22e8"
            ];
          boot.blacklistedKernelModules = [ "ast" ];

          boot.uki.name = "BOOTX64";
          boot.uki.version = null;
          boot.uki.settings.UKI.Initrd = lib.mkForce "${config.system.build.netbootRamdisk}/initrd";

          boot.zfs.forceImportRoot = false;

          hardware.graphics.enable = enableGnome;

          services.xserver = lib.mkIf enableGnome {
            enable = true;
            videoDrivers = [ "nouveau" ];
          };
          services.displayManager.gdm.enable = enableGnome;
          services.desktopManager.gnome.enable = enableGnome;

          environment.gnome.excludePackages = lib.optionals enableGnome (with pkgs; [
              gnome-backgrounds
              gnome-bluetooth
              gnome-color-manager
              gnome-tour
              gnome-user-docs
              gnome-menus
              orca
            ]);

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
          services.gnome = lib.mkIf enableGnome {
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

          services.pipewire = {
            enable = enableGnome;
            alsa.enable = enableGnome;
            pulse.enable = enableGnome;
          };

          programs.gnome-disks.enable = enableGnome;
          programs.virt-manager.enable = enableVMs;
          programs.firefox.enable = enableGnome && enableExtras;

          environment.sessionVariables = lib.optionalAttrs (enableGnome && enableExtras) {
            NIXOS_OZONE_WL = "1";
          };

          xdg.mime.defaultApplications = lib.optionalAttrs enableGnome {
            "inode/directory" = [ "org.gnome.Nautilus.desktop" ];
          };
          programs.dconf.profiles = lib.mkIf enableGnome {
            gdm.databases = [{
              settings = {
                "org/gnome/desktop/interface".scaling-factor = lib.gvariant.mkUint32 2;
                "org/gnome/settings-daemon/plugins/power" = {
                  sleep-inactive-ac-type = "nothing";
                  sleep-inactive-battery-type = "nothing";
                };
              };
            }];

            user.databases = [{
              settings = {
                "org/gnome/desktop/interface".scaling-factor = lib.gvariant.mkUint32 2;
                "org/gnome/desktop/session".idle-delay = lib.gvariant.mkUint32 0;
                "org/gnome/settings-daemon/plugins/power" = {
                  sleep-inactive-ac-type = "nothing";
                  sleep-inactive-battery-type = "nothing";
                };
                "org/gnome/shell".favorite-apps = [
                  "org.gnome.Nautilus.desktop"
                  "org.gnome.Console.desktop"
                  "org.gnome.DiskUtility.desktop"
                ] ++ lib.optionals enableVMs [ "virt-manager.desktop" ];
              };
            }];
          };

          virtualisation.libvirtd = lib.mkIf enableVMs {
            enable = true;
            onBoot = "ignore";
            onShutdown = "shutdown";
            firewallBackend = "nftables";
            qemu = {
              package = pkgs.qemu_kvm;
              vhostUserPackages = [ pkgs.virtiofsd ];
            };
          };

          environment.systemPackages =
            (with pkgs; [
              vim
              curl
              htop
              tmux
              zfs
            ])
            ++ lib.optionals enableGnome (with pkgs; [
              nautilus
              gnome-console
            ])
            ++ lib.optionals (enableGnome && enableExtras) (with pkgs; [
              vscodium
            ])
            ++ lib.optionals enableTools (with pkgs; [
              pciutils
              usbutils
              dmidecode
              smartmontools
              nvme-cli
              ethtool
              lm_sensors
              hdparm
              ipmitool
              efibootmgr
            ])
            ++ lib.optionals enableVMs (with pkgs; [
              qemu_kvm
              libvirt
              virt-manager
              passt
              virtiofsd
            ]);

          environment.shellAliases = {
            mnt = "zpool import -a && zfs load-key -a && zfs mount -a";
          } // lib.optionalAttrs enableVMs {
            vmpersist = "mount --bind /sdd/vm/qemu /var/lib/libvirt/qemu && mount --bind /sdd/vm/images /var/lib/libvirt/images";
          };

          systemd.services.libvirtd.path = lib.optionals enableVMs [ pkgs.passt ];

          systemd.targets.sleep.enable = false;
          systemd.targets.suspend.enable = false;
          systemd.targets.hibernate.enable = false;
          systemd.targets.hybrid-sleep.enable = false;
        })
      ];
    };
  in
  {
    nixosConfigurations = {
      inherit stateless;
    };

    packages.${system} = {
      default = stateless.config.system.build.uki;
    };
  };
}
