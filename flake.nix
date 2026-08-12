{
  description = "Stateless NixOS VM host and QCOW2 guest images";

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
    enableHostVirtualization = true; # QEMU, libvirt, virt-manager and passthrough
    hostScalingFactor = 2;
    enableGuestGui = true;
    enableGuestScaling = true;
    enableGuestNvidia = true; # Set true when passing the RTX PRO 6000 through
    enableGuestContainers = true;
    guestScalingFactor = 2;
    guestDiskSize =
      if enableGuestContainers then 32768
      else if enableGuestGui || enableGuestNvidia then 16384
      else 8192;
    guestImageTags =
      lib.optionals enableGuestGui [ "gui" ]
      ++ lib.optionals (enableGuestGui && enableGuestScaling) [ "scl" ]
      ++ lib.optionals enableGuestContainers [ "pod" ]
      ++ lib.optionals enableGuestNvidia [ "nv" ];
    guestImageBaseName =
      "vm"
      + lib.optionalString (guestImageTags != [ ])
        "-${lib.concatStringsSep "-" guestImageTags}";

    commonPackages = pkgs: with pkgs; [
      curl
      git
      htop
      tmux
      vim
      tree
      wireguard-tools
    ];

    hostPackages = pkgs: with pkgs; [
      zfs
    ];

    gnomePackages = pkgs: with pkgs; [
      nautilus
      gnome-console
    ];

    extraPackages = pkgs: with pkgs; [
      vscodium
    ];

    toolPackages = pkgs: with pkgs; [
      pciutils
      usbutils
      dmidecode
      smartmontools
      nvme-cli
      ethtool
      lm_sensors
      hdparm
    ];

    hostOnlyToolPackages = pkgs: with pkgs; [
      ipmitool
      efibootmgr
    ];

    # Clearly define packages needed even if it is duplication with other parts of config
    vmHostPackages = pkgs: with pkgs; [
      qemu_kvm
      libvirt
      virt-manager
      passt
      virtiofsd
    ];

    guestContainerPackages = pkgs: with pkgs; [
      podman
      podman-compose
      gvisor # Provides runsc.
    ];

    gnomeModule = { scalingFactor, includeVMManager ? false }:
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

        services.pipewire = {
          enable = true;
          alsa.enable = true;
          pulse.enable = true;
        };

        programs.gnome-disks.enable = true;
        programs.firefox.enable = enableExtras;

        environment.systemPackages =
          gnomePackages pkgs
          ++ lib.optionals enableExtras (extraPackages pkgs);

        environment.sessionVariables = lib.optionalAttrs enableExtras {
          NIXOS_OZONE_WL = "1";
        };

        xdg.mime.defaultApplications = {
          "inode/directory" = [ "org.gnome.Nautilus.desktop" ];
        };

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

    guestNvidiaModule = { ... }: {
      hardware.graphics.enable = true;
      services.xserver.videoDrivers = [ "nvidia" ];
      hardware.nvidia = {
        branch = "production";
        modesetting.enable = true;
        open = true;
        nvidiaSettings = enableGuestGui;
      };
    };

    guestContainersModule = { pkgs, ... }: {
      virtualisation.podman = {
        enable = true;
        extraRuntimes = [ pkgs.gvisor ];
      };
      environment.systemPackages = guestContainerPackages pkgs;
    };

    commonModule = { pkgs, ... }: {
      time.timeZone = "Europe/Belgrade";
      i18n.defaultLocale = "en_US.UTF-8";

      nixpkgs.config.allowUnfree = true;
      nix.settings.experimental-features = [
        "nix-command"
        "flakes"
      ];

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

      environment.systemPackages = commonPackages pkgs;
    };

    stateless = lib.nixosSystem {
      inherit system;

      modules =
        [ commonModule ]
        ++ lib.optional enableGnome (gnomeModule {
          scalingFactor = hostScalingFactor;
          includeVMManager = enableHostVirtualization;
        })
        ++ [
        ({ config, lib, pkgs, modulesPath, ... }: {
          # Four concurrent builds, each sized for one quarter of the
          # EPYC 7702P's 128 logical CPUs.
          nix.settings.max-jobs = 4;
          nix.settings.cores = 32;

          services.openssh.settings = {
            PermitRootLogin = "prohibit-password";
            AllowUsers = [ "root" "box" ];
          };

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
                ++ lib.optionals enableHostVirtualization [ "kvm" "libvirtd" ]
                ++ lib.optionals enableGnome [ "video" "render" ];
              openssh.authorizedKeys.keys = [ sshKey ];
            };
          };

          imports = [
            (modulesPath + "/installer/netboot/netboot.nix")
            (modulesPath + "/profiles/minimal.nix")
          ];

          networking.hostName = "stateless-r3";
          networking.hostId = "06e694f9";
          networking.nftables.enable = true;
          networking.networkmanager.enable = false;

          boot.supportedFilesystems = [ "zfs" ];

          boot.initrd.kernelModules =
            lib.optionals enableHostVirtualization [
              "vfio_pci"
              "vfio"
              "vfio_iommu_type1"
            ]
            ++ lib.optionals enableGnome [
              # The NVIDIA GeForce GT 710 is Kepler and must use Nouveau.
              # VFIO modules precede it so the RTX PRO IDs are claimed first.
              "nouveau"
            ];
          boot.kernelModules = lib.optionals enableHostVirtualization [ "kvm-amd" ];
          boot.kernelParams =
            [
              "nohibernate"
              "modprobe.blacklist=ast"
            ]
            ++ lib.optionals enableHostVirtualization [
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

          services.xserver.videoDrivers = lib.mkIf enableGnome [ "nouveau" ];

          programs.virt-manager.enable = enableHostVirtualization;

          virtualisation.libvirtd = lib.mkIf enableHostVirtualization {
            enable = true;
            onBoot = "ignore";
            onShutdown = "shutdown";
            firewallBackend = "nftables";
            qemu = {
              package = pkgs.qemu_kvm;
              vhostUserPackages = [ pkgs.virtiofsd ];
            };
          };

          # Make libvirt 12.x's secret bootstrap self-contained on this stateless host.
          systemd.services.virt-secret-init-encryption = lib.mkIf enableHostVirtualization {
            serviceConfig = {
              StateDirectory = "libvirt/secrets";
              StateDirectoryMode = "0700";
              # The empty entry clears libvirt's package-provided ExecStart.
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
            hostPackages pkgs
            ++ lib.optionals enableTools (
              toolPackages pkgs ++ hostOnlyToolPackages pkgs
            )
            ++ lib.optionals enableHostVirtualization (vmHostPackages pkgs);

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

    vm = lib.nixosSystem {
      inherit system;

      modules =
        [
          commonModule
          "${nixpkgs}/nixos/modules/profiles/qemu-guest.nix"
        ]
        ++ lib.optional enableGuestGui (gnomeModule {
          scalingFactor = if enableGuestScaling then guestScalingFactor else 1;
        })
        ++ lib.optional enableGuestNvidia guestNvidiaModule
        ++ lib.optional enableGuestContainers guestContainersModule
        ++ [

        ({ config, lib, modulesPath, pkgs, ... }: {
          networking.hostName = "vm-r3";
          networking.useDHCP = false;
          networking.useNetworkd = true;
          systemd.network = {
            enable = true;
            networks."10-dhcp" = {
              matchConfig.Name = "en* eth*";
              networkConfig = {
                DHCP = "yes";
                IPv6AcceptRA = true;
              };
            };
          };

          boot.loader.grub = {
            enable = true;
            devices = [ "/dev/vda" ];
            efiSupport = true;
            efiInstallAsRemovable = true;
          };
          boot.loader.efi.canTouchEfiVariables = false;
          boot.loader.timeout = 1;

          fileSystems."/" = {
            device = "/dev/disk/by-label/nixos";
            fsType = "ext4";
            autoResize = true;
          };
          fileSystems."/boot" = {
            device = "/dev/disk/by-label/ESP";
            fsType = "vfat";
            options = [ "umask=0077" ];
          };

          services.qemuGuest.enable = true;
          services.spice-vdagentd.enable = enableGuestGui;
          services.displayManager.autoLogin = lib.mkIf enableGuestGui {
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

          users.users = {
            root = {
              hashedPassword = "";
              openssh.authorizedKeys.keys = [ sshKey ];
            };

            nixos = {
              isNormalUser = true;
              extraGroups =
                [ "wheel" ]
                ++ lib.optionals (enableGuestGui || enableGuestNvidia) [ "video" "render" ];
              hashedPassword = "";
              openssh.authorizedKeys.keys = [ sshKey ];
            };
          };
          security.sudo.wheelNeedsPassword = false;

          environment.systemPackages = lib.optionals enableTools (toolPackages pkgs);

          environment.etc."nixos/flake.nix".source = ./flake.nix;

          system.build.qcow2 = builtins.import (modulesPath + "/../lib/make-disk-image.nix") {
            inherit config lib pkgs;
            name = "${guestImageBaseName}-image";
            baseName = guestImageBaseName;
            format = "qcow2";
            diskSize = guestDiskSize;
            partitionTableType = "hybrid";
            copyChannel = false;
          };
        })
      ];
    };
  in
  {
    nixosConfigurations = {
      inherit stateless vm;
    };

    packages.${system} = {
      default = stateless.config.system.build.uki;
      host = stateless.config.system.build.uki;
      vm = vm.config.system.build.qcow2;
    };
  };
}
