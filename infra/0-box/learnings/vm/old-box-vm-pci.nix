{ config, pkgs, ... }:

let
  microvm-nix = builtins.fetchTarball "https://github.com/microvm-nix/microvm.nix/archive/main.tar.gz";

in
{
  imports =
    [
      "${microvm-nix}/nixos-modules/host"
    ];

  microvm.vms = pkgs.lib.mkMerge [
  (pkgs.lib.mkIf enableDevVM {
  dev = {
    inherit pkgs;
    config = {
      networking.hostName = "dev";

      microvm = {
        hypervisor = "qemu";
        mem = 2000;
        vcpu = 4;

        interfaces = [{
          type = "bridge";
          id = "vm-dev";
          mac = "02:00:00:00:00:01";
          bridge = "br0";
        }];

        shares = [
          { tag = "ssd"; source = "/ssd"; mountPoint = "/ssd"; proto = "virtiofs"; }
          { tag = "hdd"; source = "/hdd"; mountPoint = "/hdd"; proto = "virtiofs"; }
          { tag = "dev-var"; source = "/ssd/vm/dev-var"; mountPoint = "/var"; proto = "virtiofs"; }
          { tag = "dev-keys"; source = "/ssd/vm/dev-keys"; mountPoint = "/etc/ssh/persistent"; proto = "virtiofs"; }
        ];
      };

      users.mutableUsers = false;
      users.users.root.hashedPassword = "!";
      users.users.root.openssh.authorizedKeys.keys = [
        sshKey
      ];

      services.openssh = {
        enable = true;
        hostKeys = [{
          path = "/etc/ssh/persistent/ssh_host_ed25519_key";
          type = "ed25519";
        }];
      };
      networking.firewall.allowedTCPPorts = [ 22 ];

      systemd.network = {
        enable = true;
        networks."20-lan" = {
          matchConfig.Type = "ether";
          address = [ "192.168.1.11/24" ];
          gateway = [ "192.168.1.1" ];
        };
      };

      system.stateVersion = "25.11";
    };
  };
  })
  ];

}
