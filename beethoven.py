#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path

MB = 1024*1024
CR3_start  = b'\x00\x00\x00\x18ftypcrx'
CR3_marker = b'CanonCR3'

def CR3_headers(file, total_size, buff_size=8*MB):
    n = len(CR3_start)
    k = len(CR3_marker)
    while True:
        pos = file.tell()
        progress = 100 * pos / total_size
        print(f"🍖 {pos:,d}B of {total_size:,d}B ({progress:0.2f}%)", end='')
        print('\r', end='')
        buf = file.read(buff_size)
        if not buf:
            break

        idx = buf.find(CR3_start)
        if idx < 0:
            file.seek(pos + buff_size - 2*n)
            continue

        file.seek(pos + idx + 64)
        marker = file.read(len(CR3_marker))
        if marker != CR3_marker:
            file.seek(pos + idx + n)
            continue

        yield(pos + idx)
        file.seek(pos + idx + n)

def CR3_chunks(file, endianess="big"):
    assert file.seekable()
    while True:
        pos  = file.tell()
        tmp = file.read(4)
        if not tmp: # eof
            break

        name = file.read(4)
        tmp = int.from_bytes(tmp, endianess)
        if tmp == 1:
            tmp  = file.read(8)
            size = int.from_bytes(tmp, endianess)
        else:
            size = tmp

        yield(pos, name, size)
        file.seek(pos + size)

def CR3_size(cr3, endianess="big"):
    total_size = 0
    last_chunk = bytes('mdat', encoding='utf-8')
    for index, (offset, name, size) in enumerate(CR3_chunks(cr3, endianess)):
        if index == 0 and name != b'ftyp':
            break
        total_size += size
        if name == last_chunk:
            break
    return total_size

class Beethoven:
    def __init__(self, args):
        self.args = args
        self.input_size = args.drive.stat().st_size
        self.file_id = 0

    def go_boy(self):
        path = self.args.drive
        print(f'Go Beethoven! Find me some 🦴 in {path}')
        count = 0

        with path.open('rb') as dump, path.open('rb') as cr3:
            for offset in CR3_headers(dump, self.input_size):
                cr3.seek(offset)
                size = CR3_size(cr3)
                print(f"Found 🦴 (size: {size})", end='')
                if size > 0:
                    self.restore(cr3, offset, size)
                    count += 1
                else:
                    print("not a 🦴")
        if count:
            print(f"\nRestored {count} 🦴")
        else:
            print("No 🦴 found")

    def restore(self, cr3, offset, size):
        cr3.seek(offset)
        file_name = f'{self.file_id}.cr3'
        path = self.args.output / file_name
        self.file_id += 1

        bufsize = 8*MB
        print(f" → Saving {file_name}, size {size:,d} B")
        with path.open('wb') as out:
            while size > 0:
                k = min(bufsize, size)
                buf = cr3.read(k)
                out.write(buf)
                size -= k

def parse_args():
    p = argparse.ArgumentParser(description="🐶 Configuring Beethoven...")

    p.add_argument('-i', '--drive',
                   type=Path,
                   required=True,
                   help="drive or dump",
                   metavar="PATH")
    p.add_argument('-o', '--output',
                   type=Path,
                   default='recovered',
                   help="output directory",
                   metavar="DIR")

    args = p.parse_args()
    if not args.drive.exists():
        p.error(f"{args.input} does not exist")

    if not args.output.is_dir():
        p.error(f"{args.outdir} is not a directory or not exists")
    return args

if __name__ == '__main__':
    args = parse_args()
    beethoven = Beethoven(args)
    beethoven.go_boy()
