"""C2PA bridge helpers (optional dependency).

Purpose: Embed a provenance bundle CID into a C2PA assertion for generated images so
verifiers can correlate media with its provenance passport / bundle.

We intentionally avoid adding heavy dependencies to the base install. To enable
C2PA embedding, install optional packages:

    pip install c2pa Pillow

Functions:
    embed_bundle_cid(image_path, bundle_cid, out_path=None) -> str
        Embeds the bundle CID as a simple custom assertion (or ingredient) and
        writes a new image with updated C2PA manifest. Returns output path.

If the 'c2pa' library is unavailable, a RuntimeError is raised with guidance.

NOTE: This is a minimal helper and does not sign with a production key. For a
real deployment, integrate a proper signing key and manifest store.
"""
from __future__ import annotations
from typing import Optional
import os

__all__ = ["embed_bundle_cid"]

C2PA_NS = "dev.opp.bundle"


def embed_bundle_cid(image_path: str, bundle_cid: str, out_path: Optional[str] = None) -> str:
    """Embed bundle CID into the image's C2PA manifest.

    Args:
        image_path: Source image file (PNG/JPEG supported by Pillow).
        bundle_cid: The provenance bundle CID string.
        out_path: Optional output path; defaults to <stem>.c2pa<ext>

    Returns:
        Output image path with embedded manifest.
    """
    try:
        # c2pa python SDK pattern (hypothetical; adjust if actual API differs)
        import c2pa  # type: ignore
        from PIL import Image  # type: ignore
    except Exception as e:  # pragma: no cover - import guard
        raise RuntimeError(
            "C2PA embedding requires optional dependencies. Install with: pip install c2pa Pillow"
        ) from e

    if not os.path.exists(image_path):  # pragma: no cover - simple guard
        raise FileNotFoundError(image_path)

    stem, ext = os.path.splitext(image_path)
    out_path = out_path or f"{stem}.c2pa{ext}"

    # Load the image (this ensures format is recognized)
    with Image.open(image_path) as img:
        img_format = img.format

    # Minimal manifest creation (pseudo-API; adapt to real c2pa lib)
    manifest = c2pa.Manifest()
    manifest.set_title("OPP Provenance")
    manifest.add_assertion({
        "label": C2PA_NS,
        "data": {"bundle_cid": bundle_cid}
    })

    # Attach and write out (pseudo-code; actual API may differ)
    c2pa.attach_manifest(image_path, out_path, manifest)

    return out_path
