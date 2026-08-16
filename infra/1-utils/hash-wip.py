#!/usr/bin/env python3

import os
import hashlib
import argparse


def sha256_file(path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def walk_and_hash(root, output_file):
    with open(output_file, "w", encoding="utf-8") as out:
        for dirpath, dirnames, filenames in os.walk(root):
            for name in filenames:
                full_path = os.path.join(dirpath, name)
                try:
                    size = os.path.getsize(full_path)
                    digest = sha256_file(full_path)
                    out.write(f"{full_path}\t{size}\t{digest}\n")
                except Exception as e:
                    # Don’t die on weird files (permissions, broken symlinks, etc.)
                    out.write(f"{full_path}\tERROR\t{e}\n")

