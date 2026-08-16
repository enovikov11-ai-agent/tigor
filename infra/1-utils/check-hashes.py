# find /mnt/data/bak/comet.bak/ -type f -exec sha256sum {} + > /mnt/data/comet-bak-hashes

def read(file):
    result = {}

    with open(file) as f:
        for line in f:
            paks = line.strip().split("  ")
            result[paks[0]] = paks[1]
    
    return result

bak = read("comet-bak-hashes")
prod = read("comet-prod-hashes")

print(len(bak), len(prod))

print("\n".join([f"{k} {v}" for k, v in bak.items() if k not in prod and not v.endswith(".part")]))
