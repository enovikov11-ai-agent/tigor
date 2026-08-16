{ config, pkgs, lib, ... }:

let
  enableGui = false;
  enablePrivilegedMode = false;

  enablePodmanStack = true;

  enableAutoUpgrade = false;
  enableNixGc = false;
  enableFirejail = true;
  disableSleep = true;
  enableGnomeExtensions = true;

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
  hardware.nvidia-container-toolkit.enable = true;

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

  environment.etc."nvidia-container-runtime/config.toml" = lib.mkIf enablePodmanStack {
    text = ''
      [nvidia-container-runtime-hook]
      path = "${pkgs.nvidia-container-toolkit.tools}/bin/nvidia-container-runtime-hook"

      [nvidia-ctk]
      path = "${pkgs.nvidia-container-toolkit}/bin/nvidia-ctk"

      [features]
      disable-cuda-compat-lib-hook = true
    '';
  };

  hardware.graphics.enable = true;
  services.xserver.videoDrivers = [ "nvidia" ];
  services.pipewire = lib.mkIf enableGui { enable = true; alsa.enable = true; pulse.enable = true; };

  virtualisation.podman = {
    enable = true;
    dockerCompat = true;
    extraPackages = [ pkgs.podman-compose ];
    extraRuntimes = [ pkgs.runc pkgs.gvisor ];
    defaultNetwork.settings.dns_enabled = true;
  };

  environment.etc."haproxy/haproxy.cfg" = lib.mkIf enablePodmanStack {
    text = ''
      defaults
        mode tcp
        timeout connect 5s
        timeout client 3600s
        timeout server 3600s

      frontend vllm-in
        bind *:8001
        default_backend vllm

      backend vllm
        server p-vllm p-vllm:8000 check

      frontend chat-in
        bind *:8002
        default_backend chat

      backend chat
        server p-chat p-chat:8080 check
    '';
  };

  environment.etc."podman-compose/compose.yaml" = lib.mkIf enablePodmanStack {
    text = ''
      services:
        p-haproxy:
          image: docker.io/library/haproxy:2.9-alpine
          container_name: p-haproxy
          restart: unless-stopped
          volumes:
            - /etc/haproxy/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
          security_opt:
            - no-new-privileges:true
          ports:
            - 0.0.0.0:8001:8001
            - 0.0.0.0:8002:8002

        p-vllm:
          image: docker.io/vllm/vllm-openai:nightly
          container_name: p-vllm
          restart: unless-stopped
          command: /huggingface.co/Qwen/Qwen3.6-27B-FP8 --served-model-name Qwen3.6-27B-FP8 --host 0.0.0.0 --port 8000 --max-model-len 262144 --gpu-memory-utilization 0.95 --kv-cache-dtype fp8 --optimization-level 3 --performance-mode interactivity --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_coder --speculative-config '{"method":"qwen3_next_mtp","num_speculative_tokens":2}'
          devices:
            - nvidia.com/gpu=all
          environment:
            NVIDIA_VISIBLE_DEVICES: all
            NVIDIA_DRIVER_CAPABILITIES: compute,utility
            PYTORCH_ALLOC_CONF: expandable_segments:True
          volumes:
            - /ssd/internet/huggingface.co:/huggingface.co:ro
            - /ssd/private/podman/p-vllm-cache:/root/.cache/vllm
          shm_size: 16g
          security_opt:
            - no-new-privileges:true
          ports:
            - 0.0.0.0:8000:8000
          cpuset: "0-63"

        p-chat:
          image: ghcr.io/open-webui/open-webui:main
          container_name: p-chat
          restart: unless-stopped
          runtime: runsc
          environment:
            OPENAI_API_BASE_URL: http://p-vllm:8000/v1
            OPENAI_API_KEY: none
            WEBUI_AUTH: "false"
            ENABLE_OLLAMA_API: "false"
          volumes:
            - /hdd/private/podman/p-chat:/app/backend/data
          security_opt:
            - no-new-privileges:true
          ports:
            - 0.0.0.0:8080:8080
    '';
  };

  systemd.services."podman-compose" = lib.mkIf enablePodmanStack {
    description = "Podman Compose stack";
    wantedBy = [ "multi-user.target" ];
    wants = [ "network-online.target" ];
    after = [ "network-online.target" ];
    restartTriggers = [ config.environment.etc."podman-compose/compose.yaml".source config.environment.etc."haproxy/haproxy.cfg".source ];
    environment = {
      HOME = "/root";
      PODMAN_COMPOSE_PROVIDER = "${pkgs.podman-compose}/bin/podman-compose";
    };
    path = [ config.virtualisation.podman.package ];
    serviceConfig = {
      Type = "oneshot";
      WorkingDirectory = "/etc/podman-compose";
      ExecStart = "${config.virtualisation.podman.package}/bin/podman compose up -d --remove-orphans";
       ExecReload = "${config.virtualisation.podman.package}/bin/podman compose up -d --remove-orphans";
      RemainAfterExit = true;
      StandardOutput = "journal+console";
      StandardError = "journal+console";
      TimeoutStartSec = 900;
      TimeoutStopSec = 120;
    };
  };

  services.xserver.enable = enableGui;
  services.displayManager = lib.mkIf enableGui {
    gdm.enable = true;
    gdm.wayland = true;
  };
  services.desktopManager.gnome.enable = enableGui;

  environment.gnome.excludePackages = lib.mkIf enableGui (with pkgs; [ gnome-tour gnome-maps gnome-music gnome-weather gnome-contacts gnome-characters gnome-clocks gnome-logs geary epiphany yelp ]);

  programs.dconf = lib.mkIf enableGui {
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
      settings."org/gnome/desktop/background" =
        (lib.optionalAttrs enablePrivilegedMode {
          picture-options = "none";
          primary-color = "#000000";
        })
        // (lib.optionalAttrs (!enablePrivilegedMode) {
          picture-uri = "file:///run/current-system/sw/share/backgrounds/gnome/blobs-l.svg";
          picture-uri-dark = "file:///run/current-system/sw/share/backgrounds/gnome/blobs-l.svg";
        });
      settings."org/gnome/shell" = {
        favorite-apps = [
          "firefox.desktop"
          "org.gnome.Nautilus.desktop"
          "org.gnome.Console.desktop"
          "codium.desktop"
          "blender.desktop"
          "vlc.desktop"
          "org.gnome.SystemMonitor.desktop"
        ];
      } // lib.optionalAttrs enableGnomeExtensions {
        enabled-extensions = [ "dash-to-dock@micxgx.gmail.com" ];
      };
      settings."org/gnome/settings-daemon/plugins/power" = {
        sleep-inactive-ac-type = "none";
        sleep-inactive-battery-type = "nothing";
      };
      settings."org/gnome/shell/extensions/dash-to-dock" = lib.optionalAttrs enableGnomeExtensions {
        dock-fixed = true;
        dock-position = "BOTTOM";
        extend-height = false;
        intellihide = false;
        dash-max-icon-size = lib.gvariant.mkInt32 54;
      };
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
    home = "/ssd/home";
    hashedPassword = mainPassword;
    extraGroups = [ "video" "render" ];
    openssh.authorizedKeys.keys = [ sshKey ];
    subUidRanges = [
      {
        startUid = 100000;
        count = 65536;
      }
    ];
    subGidRanges = [
      {
        startGid = 100000;
        count = 65536;
      }
    ];
  };

  systemd.services."user@".serviceConfig = {
    ProtectKernelLogs = false;
    ProtectClock = true;
    ProtectHostname = false;
    ProtectKernelModules = true;
    RestrictRealtime = true;
    LockPersonality = true;
    SystemCallArchitectures = "native";
    ReadOnlyPaths = [ "-/hdd" ];
    ReadWritePaths = [ "-/ssd" ];
    InaccessiblePaths = [ "-/dev/zfs" "-/ssd/private" "-/hdd/private" ];
  };

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
  in (lib.optionalString enablePrivilegedMode usbAndLuks) + denyAll;

  programs.firejail = lib.mkIf (enableGui && enableFirejail) {
    enable = true;
    wrappedBinaries = {
      firefox = { executable = "${pkgs.firefox}/bin/firefox"; profile = "${pkgs.firejail}/etc/firejail/firefox.profile"; };
      blender = { executable = "${blenderCuda}/bin/blender"; profile = "${pkgs.firejail}/etc/firejail/blender.profile"; };
      vscodium = { executable = "${pkgs.vscodium}/bin/codium"; profile = "${pkgs.firejail}/etc/firejail/vscodium.profile"; };
      vlc = { executable = "${pkgs.vlc}/bin/vlc"; profile = "${pkgs.firejail}/etc/firejail/vlc.profile"; };
    };
  };

  boot.kernel.sysctl = {
    "kernel.yama.ptrace_scope" = 2;
    "kernel.dmesg_restrict" = 1;
    "kernel.kptr_restrict" = 2;
    "net.core.bpf_jit_harden" = 2;
  };

  networking.firewall.allowedTCPPorts = [ 22 8000 8001 8002 8080 ];
  networking.hostId = "06e694f9";
  networking.useDHCP = false;
  networking.bridges.br0.interfaces = [ "eno1" ];
  networking.interfaces.br0.ipv4.addresses = [{ address = "192.168.1.10"; prefixLength = 24; }];
  networking.defaultGateway = "192.168.1.1";
  networking.nameservers = [ "1.1.1.1" "8.8.8.8" ];
  networking.hostName = "box";

  networking.wireguard.interfaces = {
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

  systemd.targets.sleep.enable = lib.mkIf disableSleep false;
  systemd.targets.suspend.enable = lib.mkIf disableSleep false;
  systemd.targets.hibernate.enable = lib.mkIf disableSleep false;
  systemd.targets.hybrid-sleep.enable = lib.mkIf disableSleep false;

  system.autoUpgrade = lib.mkIf enableAutoUpgrade { enable = true; allowReboot = false; dates = "04:00"; };

  environment.systemPackages = with pkgs; [
    vim wget curl openssl htop tmux pciutils usbutils lsof iotop ethtool file tree dig ncdu apfs-fuse python3 smartmontools
    blenderCuda vscodium vlc git python3Packages.huggingface-hub ipmitool
    nvidia-container-toolkit nvidia-container-toolkit.tools
  ] ++ lib.optionals enableGui [ firefox gnomeExtensions.dash-to-dock ];

  nix.settings.experimental-features = [ "nix-command" "flakes" ];
  nix.settings.cores = 64;
  nix.settings.max-jobs = 4;
  nixpkgs.config.allowUnfree = true;
  system.stateVersion = "25.11";

  environment.shellAliases = {
    box = "machinectl shell box@";
    hashdir = "find . -type f -print0 | xargs -0 sha256sum | sed 's|  \./|  ./|' | sort -k2 | sha256sum";
    jf = "journalctl -f -a -u";
  };

  environment.sessionVariables = { NIXOS_OZONE_WL = lib.mkIf enableGui "1"; };

  nix.gc = lib.mkIf enableNixGc { automatic = true; dates = "weekly"; options = "--delete-older-than 14d"; };
  nix.settings.min-free = lib.mkIf enableNixGc 1073741824;
  nix.settings.max-free = lib.mkIf enableNixGc 5368709120;
}
