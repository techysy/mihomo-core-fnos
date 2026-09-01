#!/usr/bin/env python3
"""生成 fnpack 需要的应用图标 ICON.PNG（深蓝底 + 白色 M）。

fnpack 打包要求根目录存在 ICON.PNG；仓库不提交图标（gitignore 排除），
打包时由本脚本生成。用法：python3 scripts/gen_icon.py [输出路径]
"""
import os
import struct
import sys
import zlib


def chunk(t, d):
    c = t + d
    return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)


def main():
    out_dir = "."
    if len(sys.argv) > 1:
        out_dir = sys.argv[1]
    w = h = 256
    bg = (16, 20, 40)   # 深蓝底
    fg = (255, 255, 255)  # 白色 M
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # 每行前 filter byte
        for x in range(w):
            px = bg
            if 60 < x < 200 and 80 < y < 176:
                if x < 80 or x > 176:  # 左右竖线
                    px = fg
                if abs((x - 128) - (y - 128) * 0.8) < 14 or abs((x - 128) + (y - 128) * 0.8) < 14:
                    px = fg  # 中间 V
            raw += bytes(px + (255,))
    idat = zlib.compress(bytes(raw), 9)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", idat)
    png += chunk(b"IEND", b"")
    # fnpack 要求根目录同时存在 ICON.PNG 和 ICON_256.PNG
    for name in ("ICON.PNG", "ICON_256.PNG"):
        path = os.path.join(out_dir, name)
        with open(path, "wb") as f:
            f.write(png)
        print("生成", path, len(png), "bytes")


if __name__ == "__main__":
    main()
