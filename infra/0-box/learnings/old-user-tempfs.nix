{ config, pkgs, lib, ... }:

let
  privilegedMode = false;
  boxInternet = !privilegedMode;

  sshKey = "sk-ssh-ed25519@openssh.com AAAAGnNrLXNzaC1lZDI1NTE5QG9wZW5zc2guY29tAAAAIMltMQTMSIcxPbZLNCxkAT/MWRqJo1IFOfH95OoscQbCAAAABHNzaDo= enovikov11@novikov.local";
  mainPassword = "$6$JsF575e4YV0MxwGU$aDy3BMHg/5lvWZoMvsAV0TL/BIcXMu3ps1DnOf3.o.hQ3IqT/sfCwKJHdMaaRy2exNAEUFxpxPbO966DE5cm./";

  blenderCuda = pkgs.blender.override { cudaSupport = true; };
in
{
  imports = [ ./hardware-configuration.nix ];

  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;
  boot.supportedFilesystems = [ "zfs" ];
  boot.initrd.supportedFilesystems = [ "zfs" ];
  boot.zfs.forceImportRoot = false;
  boot.zfs.extraPools = [ "ssd" "hdd" ];
  boot.initrd.network = {
    enable = true;
    ssh = { enable = true; port = 2222; hostKeys = [ "/boot/initrd_ssh_host_ed25519_key" ]; authorizedKeys = [ sshKey ]; };
    postCommands = ''
      cat <<'SCRIPT' > /root/.profile
      cryptsetup-askpass
      zfs load-key ssd/enc
      zfs load-key hdd/enc
      SCRIPT
    '';
  };
  boot.initrd.postDeviceCommands = ''
    zpool import -f ssd
    zpool import -f hdd
    while [ "$(zfs get -H -o value keystatus ssd/enc 2>/dev/null)" != "available" ] || \
          [ "$(zfs get -H -o value keystatus hdd/enc 2>/dev/null)" != "available" ]; do
      sleep 1
    done
  '';
  system.activationScripts.initrdHostKey.text = ''
    if [ ! -f /boot/initrd_ssh_host_ed25519_key ]; then
      ${pkgs.openssh}/bin/ssh-keygen -t ed25519 -f /boot/initrd_ssh_host_ed25519_key -N ""
    fi
  '';

  boot.initrd.availableKernelModules = [ "igb" ];
  boot.kernelParams = [ "nvidia-drm.modeset=1" "modprobe.blacklist=ast" "nohibernate" "ip=192.168.1.10::192.168.1.1:255.255.255.0::eno1:none" ];
  boot.blacklistedKernelModules = [ "ast" ];

  time.timeZone = "Europe/Belgrade";
  i18n.defaultLocale = "en_US.UTF-8";
  
  hardware.nvidia = { modesetting.enable = true; open = true; };
  hardware.graphics.enable = true;
  services.xserver.videoDrivers = [ "nvidia" ];
  services.pipewire = { enable = true; alsa.enable = true; pulse.enable = true; };

  services.xserver.enable = true;
  services.displayManager.gdm.enable = true;
  services.displayManager.gdm.wayland = true;
  services.desktopManager.gnome.enable = true;

  environment.gnome.excludePackages = (with pkgs; [ gnome-tour gnome-maps gnome-music gnome-weather gnome-contacts gnome-characters gnome-clocks gnome-logs geary epiphany yelp ]);

  programs.dconf = {
    enable = true;

    profiles.gdm.databases = [{
      settings."org/gnome/desktop/interface" = { scaling-factor = lib.gvariant.mkUint32 2; };
      settings."org/gnome/mutter" = { experimental-features = [ "scale-monitor-framebuffer" ]; };
      settings."org/gnome/settings-daemon/plugins/power" = {
        sleep-inactive-ac-type = "nothing";
        sleep-inactive-battery-type = "nothing";
      };
    }];

    profiles.user.databases = [{
      settings."org/gnome/mutter" = { experimental-features = [ "scale-monitor-framebuffer" ]; };
      settings."org/gnome/desktop/interface" = { scaling-factor = lib.gvariant.mkUint32 2; };
      settings."org/gnome/desktop/background" = if privilegedMode then {
        picture-options = "none";
        primary-color = "#000000";
      } else {
        picture-uri = "file:///run/current-system/sw/share/backgrounds/gnome/blobs-l.svg";
        picture-uri-dark = "file:///run/current-system/sw/share/backgrounds/gnome/blobs-l.svg";
      };
      settings."org/gnome/shell" = { favorite-apps = [
        "firefox.desktop"
        "org.gnome.Nautilus.desktop"
        "org.gnome.Console.desktop"
        "codium.desktop"
        "blender.desktop"
        "vlc.desktop"
        "org.gnome.SystemMonitor.desktop"
      ]; };
      settings."org/gnome/settings-daemon/plugins/power" = {
        sleep-inactive-ac-type = "nothing";
        sleep-inactive-battery-type = "nothing";
      };
      settings."org/gnome/shell/extensions/dash-to-dock" = {
        dock-fixed = true;
        dock-position = "BOTTOM";
        extend-height = false;
        intellihide = false;
        dash-max-icon-size = lib.gvariant.mkInt32 54;
      };
      settings."org/gnome/shell" = { enabled-extensions = [ "dash-to-dock@micxgx.gmail.com" ]; };
      settings."org/gnome/desktop/session" = { idle-delay = lib.gvariant.mkUint32 21600; };
      settings."org/gnome/gnome-session" = { auto-save-session = false; };
    }];
  };
  
  services.openssh.enable = true;
  services.openssh.settings = { PasswordAuthentication = false; KbdInteractiveAuthentication = false; PermitRootLogin = "prohibit-password"; AllowUsers = [ "root" "box" ]; };

  users.mutableUsers = false;
  users.users.root.hashedPassword = mainPassword;
  users.users.root.openssh.authorizedKeys.keys = [ sshKey ];
  users.users.box = {
    isNormalUser = true;
    uid = 1000;
    home = "/home/box";
    hashedPassword = mainPassword;
    extraGroups = [ "video" "render" ];
    subUidRanges = [{ startUid = 200000; count = 65536; }];
    subGidRanges = [{ startGid = 200000; count = 65536; }];
    openssh.authorizedKeys.keys = [ sshKey ];
  };

  fileSystems."/home/box" = {
    device = "none";
    fsType = "tmpfs";
    options = [ "size=10G" "mode=0700" "uid=1000" "gid=100" ];
  };

  systemd.services.box-home-init = lib.mkIf (!privilegedMode) {
    after = [ "local-fs.target" "zfs.target" ];
    wantedBy = [ "multi-user.target" ];
    before = [ "display-manager.service" ];
    path = with pkgs; [ util-linux coreutils ];
    serviceConfig = { Type = "oneshot"; RemainAfterExit = true; };
    script = let
      dirs = [ "Downloads" "Documents" ".mozilla" ".config/VSCodium" ".vscode-oss" ];
      files = [ ".bash_history" ];
    in ''
      ${lib.concatMapStringsSep "\n" (d: "mkdir -p /home/box/$(dirname ${d}) /ssd/home/${d} && ln -sfn /ssd/home/${d} /home/box/${d}") dirs}
      ${lib.concatMapStringsSep "\n" (f: "touch -a /ssd/home/${f} && ln -sf /ssd/home/${f} /home/box/${f}") files}
      chown -R box:users /home/box /ssd/home
    '';
  };

  systemd.services."user@".serviceConfig = ({
    ProtectKernelLogs = true;
    ProtectClock = true;
    ProtectHostname = true;
    ProtectKernelModules = true;
    RestrictRealtime = true;
    LockPersonality = true;
    SystemCallArchitectures = "native";
    ReadOnlyPaths = [ "-/ssd" "-/hdd" ];
    ReadWritePaths = lib.optionals (!privilegedMode) [ "-/ssd/home" ];
    InaccessiblePaths = [ "-/dev/zfs" ]
      ++ lib.optionals privilegedMode [ "-/ssd/home" ]
      ++ lib.optionals (!privilegedMode) [ "-/ssd/private" "-/hdd/private" ];
  });

  security.polkit.extraConfig = let
    usbAndLuks = ''
      polkit.addRule(function(action, subject) {
        if (subject.user === "box" &&
            action.id.indexOf("org.freedesktop.udisks2.") === 0 &&
            (action.lookup("drive.removable") === "true" ||
             action.lookup("drive.connection-bus") === "usb" ||
             action.lookup("device").indexOf("/dev/mapper/luks-") === 0)) {
          return polkit.Result.YES;
        }
      });
    '';
    denyAll = ''
      polkit.addRule(function(action, subject) {
        if (subject.user === "box") {
          return polkit.Result.NO;
        }
      });
    '';
  in (lib.optionalString privilegedMode usbAndLuks) + denyAll;

  programs.firejail = {
    enable = true;
    wrappedBinaries = {
      firefox = { executable = "${pkgs.firefox}/bin/firefox"; profile = "${pkgs.firejail}/etc/firejail/firefox.profile"; };
      blender = { executable = "${blenderCuda}/bin/blender"; profile = "${pkgs.firejail}/etc/firejail/blender.profile"; };
      vscodium = { executable = "${pkgs.vscodium}/bin/codium"; profile = "${pkgs.firejail}/etc/firejail/vscodium.profile"; };
      vlc = { executable = "${pkgs.vlc}/bin/vlc"; profile = "${pkgs.firejail}/etc/firejail/vlc.profile"; };
    };
  };

  boot.kernel.sysctl = {
    "kernel.yama.ptrace_scope" = 2; # only root can ptrace
    "kernel.dmesg_restrict" = 1;    # no dmesg for unprivileged
    "kernel.kptr_restrict" = 2;     # hide kernel pointers
    "net.core.bpf_jit_harden" = 2;  # harden BPF JIT
  };

  networking.firewall.allowedTCPPorts = [ 22 ];
  networking.firewall.extraCommands = lib.optionalString (!boxInternet) ''
    iptables -A OUTPUT -m owner --uid-owner 1000 -j REJECT
  '';
  networking.firewall.extraStopCommands = lib.optionalString (!boxInternet) ''
    iptables -D OUTPUT -m owner --uid-owner 1000 -j REJECT || true
  '';
  networking.hostId = "06e694f9";
  networking.useDHCP = false;
  networking.bridges.br0.interfaces = [ "eno1" ];
  networking.interfaces.br0.ipv4.addresses = [{ address = "192.168.1.10"; prefixLength = 24; }];
  networking.defaultGateway = "192.168.1.1";
  networking.nameservers = [ "1.1.1.1" "8.8.8.8" ];
  networking.hostName = "box";

  networking.wireguard.interfaces = lib.mkIf boxInternet {
    wg0 = {
      ips = [ "10.69.42.2/24" ];
      privateKeyFile = "/etc/wireguard/private.key";
      generatePrivateKeyFile = true;

      peers = [{
        publicKey = "NHtNDaxbhUQ5y7L3lOqRbUwIPnvtoypVdHpL+FLAEA4=";
        endpoint = "tgr.rs:44222";
        allowedIPs = [ "10.69.42.0/24" ];
        persistentKeepalive = 25;
      }];
    };
  };

  systemd.targets.sleep.enable = false;
  systemd.targets.suspend.enable = false;
  systemd.targets.hibernate.enable = false;
  systemd.targets.hybrid-sleep.enable = false;

  system.autoUpgrade = { enable = true; allowReboot = false; dates = "04:00"; };

  environment.systemPackages = with pkgs; [
    vim wget curl htop tmux pciutils usbutils lsof iotop ethtool file tree dig ncdu apfs-fuse python3 firefox
    blenderCuda vscodium vlc git gnomeExtensions.dash-to-dock python3Packages.huggingface-hub
  ];
  nix.settings.experimental-features = [ "nix-command" "flakes" ];
  nix.settings.cores = 64;
  nix.settings.max-jobs = 4;
  nixpkgs.config.allowUnfree = true;
  system.stateVersion = "25.11";

  environment.shellAliases = {
    box = "machinectl shell box@";
    hashdir = "find . -type f -print0 | xargs -0 sha256sum | sed 's|  \\./|  ./|' | sort -k2 | sha256sum";
  };

  environment.sessionVariables = { NIXOS_OZONE_WL = "1"; };

  nix.gc = { automatic = true; dates = "weekly"; options = "--delete-older-than 14d"; };
  nix.settings.min-free = 1073741824; # 1 GB - trigger GC
  nix.settings.max-free = 5368709120; # 5 GB - stop GC
}
