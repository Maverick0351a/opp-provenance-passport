"""Example: Embed a bundle CID into an image using the optional C2PA bridge.

Usage:
  export BUNDLE_CID=sha256:abc123...
  python examples/c2pa_embed.py input.png output.c2pa.png

Install optional deps first:
  pip install c2pa Pillow
"""
from __future__ import annotations
import os, sys
from opp.c2pa import embed_bundle_cid

def main():
    if len(sys.argv) < 2:
        print("Usage: python examples/c2pa_embed.py <image_in> [image_out]")
        sys.exit(1)
    image_in = sys.argv[1]
    image_out = sys.argv[2] if len(sys.argv) > 2 else None
    bundle_cid = os.getenv("BUNDLE_CID") or "sha256:demo123"
    try:
        out = embed_bundle_cid(image_in, bundle_cid, image_out)
        print(f"Embedded bundle CID {bundle_cid} into {out}")
    except RuntimeError as e:
        print(f"Optional dependency missing: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
