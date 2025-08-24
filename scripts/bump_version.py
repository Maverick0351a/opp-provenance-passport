#!/usr/bin/env python
"""Simple semantic version bumper for packages/opp_py/pyproject.toml

Usage:
  python scripts/bump_version.py patch   # increments 0.1.1 -> 0.1.2
  python scripts/bump_version.py minor   # increments 0.1.1 -> 0.2.0
  python scripts/bump_version.py major   # increments 0.1.1 -> 1.0.0
Optionally pass an explicit version:
  python scripts/bump_version.py set 0.1.5
"""
from __future__ import annotations
import pathlib, re, sys

PYPROJECT = pathlib.Path('packages/opp_py/pyproject.toml')

def read_version(text: str) -> str:
    m = re.search(r'^version = "([0-9]+\.[0-9]+\.[0-9]+)"', text, re.MULTILINE)
    if not m:
        raise SystemExit('Could not find version in pyproject.toml')
    return m.group(1)

def write_version(text: str, new: str) -> str:
    return re.sub(r'^version = "([0-9]+\.[0-9]+\.[0-9]+)"', f'version = "{new}"', text, flags=re.MULTILINE)

def bump(ver: str, part: str) -> str:
    major, minor, patch = map(int, ver.split('.'))
    if part == 'patch':
        patch += 1
    elif part == 'minor':
        minor += 1; patch = 0
    elif part == 'major':
        major += 1; minor = 0; patch = 0
    else:
        raise SystemExit('Unknown part (expected patch|minor|major)')
    return f"{major}.{minor}.{patch}"

def main(argv: list[str]):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    mode = argv[1]
    text = PYPROJECT.read_text(encoding='utf-8')
    current = read_version(text)
    if mode == 'set':
        if len(argv) != 3:
            raise SystemExit('Usage: bump_version.py set <version>')
        new_version = argv[2]
        if not re.match(r'^[0-9]+\.[0-9]+\.[0-9]+$', new_version):
            raise SystemExit('Version must be semantic (X.Y.Z)')
    else:
        new_version = bump(current, mode)
    if new_version == current:
        print('Version unchanged')
        return
    PYPROJECT.write_text(write_version(text, new_version), encoding='utf-8')
    print(f"Bumped version: {current} -> {new_version}")

if __name__ == '__main__':
    main(sys.argv)
