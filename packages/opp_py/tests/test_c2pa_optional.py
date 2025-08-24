"""Smoke test that c2pa.embed_bundle_cid raises a clear RuntimeError when deps absent."""

from __future__ import annotations

import pathlib
import tempfile

import pytest
from opp.c2pa import embed_bundle_cid


def test_c2pa_optional_missing(monkeypatch):
    # Create a tiny dummy file to pass existence check
    with tempfile.TemporaryDirectory() as td:
        img = pathlib.Path(td)/'img.png'
        img.write_bytes(b'not-really-an-image')
        with pytest.raises(RuntimeError):
            embed_bundle_cid(str(img), 'sha256:deadbeef')
