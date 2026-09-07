#!/usr/bin/env python3
"""Prepare a clinical image for the deck.

Standing policy agreed with the instructor: any image that matches the brief in
IMAGES.md gets processed and wired in without asking again. Every image goes
through all four steps below — the crop is not optional, it is what removes
identifying context (faces, jewellery, room background) and any corner marking.

    python3 src/prep_image.py raw.jpg case-01-inflammatory \
        --crop 0.20,0.14,0.63,0.88

Steps:
  1. crop      keep only the lesion and enough surrounding skin to read it
  2. strip     re-encode pixels only, so EXIF (GPS, timestamp, device) is gone
  3. resize    1100px wide, matching the existing img/ assets
  4. compress  step quality down until the file is under the size budget
"""
import argparse
import io
import os
import sys

from PIL import Image

WIDTH = 1100
MAX_BYTES = 60 * 1024
OUT_DIR = 'img'


def parse_crop(text):
    parts = [float(v) for v in text.split(',')]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError('crop needs 4 values: left,top,right,bottom')
    left, top, right, bottom = parts
    if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
        raise argparse.ArgumentTypeError('crop values must be fractions with left<right and top<bottom')
    return left, top, right, bottom


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('source')
    ap.add_argument('name', help='output basename, no extension (e.g. case-01-inflammatory)')
    ap.add_argument('--crop', type=parse_crop, required=True,
                    help='fractions of the original: left,top,right,bottom')
    args = ap.parse_args()

    im = Image.open(args.source)
    orig_w, orig_h = im.size
    orig_bytes = os.path.getsize(args.source)

    left, top, right, bottom = args.crop
    box = (int(left * orig_w), int(top * orig_h), int(right * orig_w), int(bottom * orig_h))
    im = im.crop(box)

    # Re-encode through raw pixel data: this is what actually drops EXIF,
    # rather than trusting the encoder to omit it.
    im = Image.frombytes('RGB', im.size, im.convert('RGB').tobytes())

    if im.width > WIDTH:
        im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)

    for quality in range(82, 39, -3):
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=quality, optimize=True, progressive=True)
        if buf.tell() <= MAX_BYTES:
            break
    else:
        print('warning: could not reach the size budget; keeping quality 40', file=sys.stderr)

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, args.name + '.jpg')
    with open(out, 'wb') as fh:
        fh.write(buf.getvalue())

    check = Image.open(out)
    print('%s\n  in   %dx%d  %.0f KB\n  out  %dx%d  %.0f KB  q%d\n  exif %s'
          % (out, orig_w, orig_h, orig_bytes / 1024,
             check.width, check.height, os.path.getsize(out) / 1024, quality,
             'present — INVESTIGATE' if check.getexif() else 'none'))


if __name__ == '__main__':
    main()
