sha3_256_hex(seed+target+login+year).substr(0,20)

seed - 80bit entropy master password
target - service name or domain, target where to use password
login - username or empty string "" if not applicable
year - today year in YYYY format

Make seed using BIP39 or EFF word list [1][2]

Used sha3 [3]

[1] BIP39 https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt
[2] eff word list https://www.eff.org/files/2016/07/18/eff_large_wordlist.txt
[3] https://github.com/emn178/js-sha3
