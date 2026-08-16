{ config, pkgs, ... }:

{
  imports = [
    ./hardware-configuration.nix
  ];

  boot.loader.grub.enable = true;
  boot.loader.grub.device = "/dev/sda";
  boot.loader.grub.useOSProber = true;

  networking.hostName = "tgr";
  networking.networkmanager.enable = false;
  networking.useDHCP = false;
  networking.interfaces.ens18.ipv4.addresses = [
    {
      address = "167.86.90.24";
      prefixLength = 24;
    }
  ];
  networking.defaultGateway = "167.86.90.1";
  networking.nameservers = [ "1.1.1.1" "8.8.8.8" ];

  time.timeZone = "Europe/Belgrade";
  i18n.defaultLocale = "en_US.UTF-8";

  nixpkgs.config.allowUnfree = true;

  virtualisation.docker.enable = true;

  environment.systemPackages = with pkgs; [
    vim wget curl htop git tmux
    docker-compose
  ];

  services.openssh.enable = true;
  services.openssh.settings = {
    PasswordAuthentication = false;
    KbdInteractiveAuthentication = false;
    PermitRootLogin = "prohibit-password";
    AllowUsers = [ "root" ];
  };

  users.mutableUsers = false;
  users.users.root.hashedPassword = "!";
  users.users.root.openssh.authorizedKeys.keys = [
    "sk-ssh-ed25519@openssh.com AAAAGnNrLXNzaC1lZDI1NTE5QG9wZW5zc2guY29tAAAAIMltMQTMSIcxPbZLNCxkAT/MWRqJo1IFOfH95OoscQbCAAAABHNzaDo= enovikov11@novikov.local"
  ];

  networking.firewall.allowedTCPPorts = [ 22 80 443 ];
  networking.firewall.allowedUDPPorts = [ 44222 ];

  boot.kernel.sysctl."net.ipv4.ip_forward" = 1;

  networking.wireguard.interfaces.wg0 = {
    ips = [ "10.69.42.1/24" ];
    listenPort = 44222;
    privateKeyFile = "/etc/wireguard/private.key";
    generatePrivateKeyFile = true;

    peers = [
      { # box
        publicKey = "R5W2JP6GH5CkMshow2cOt+O9AulyO3pzj11+OJQo8ik=";
        allowedIPs = [ "10.69.42.2/32" ];
      }
      { # mac
        publicKey = "NK6P5Zi8SKPLWPWhYOs7JvxFXZgkddDEtTn3/1zPmE4=";
        allowedIPs = [ "10.69.42.3/32" ];
      }
      { # iphone
        publicKey = "AHvWfW4TI2NrIsKd2pPjxZtR1/ERrLW7dC34kK4j7TM=";
        allowedIPs = [ "10.69.42.4/32" ];
      }
    ];
  };

  system.stateVersion = "25.11";
}