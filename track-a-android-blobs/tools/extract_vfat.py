#!/usr/bin/env python3
"""extract_vfat.py — extract a whole vfat image (e.g., modem.img) via pyfatfs.

Usage: python3 extract_vfat.py <image.img> <local/dest>
"""
import os
import sys
from pyfatfs.PyFatFS import PyFatFS


def main():
    image, dest = sys.argv[1], sys.argv[2]
    fs = PyFatFS(image)
    os.makedirs(dest, exist_ok=True)
    count = 0
    for path, _dirs, files in fs.walk("/"):
        local = os.path.join(dest, path.lstrip("/"))
        os.makedirs(local, exist_ok=True)
        for fentry in files:
            fn = getattr(fentry, "name", str(fentry))
            src = f"{path.rstrip('/')}/{fn}"
            with fs.openbin(src) as fh, open(os.path.join(local, fn), "wb") as out:
                while True:
                    chunk = fh.read(1 << 20)
                    if not chunk:
                        break
                    out.write(chunk)
            count += 1
    print(f"extracted {count} files → {dest}")


if __name__ == "__main__":
    main()
