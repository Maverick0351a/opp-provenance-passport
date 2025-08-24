# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Code coverage gate (>=70%) and Codecov badge integration.
- Extensive CLI, graph, decorator, and shim test suite (coverage ~90%).
- Optional dependency extras group `c2pa` (installs `c2pa` and `Pillow`).
- Exported `py.typed` marker for type checkers.

## [0.1.1] - 2025-08-23
### Added
- Automated PyPI publish workflow (`publish-opp-py`).
- PyPI badge in README.
- Version bump helper script `scripts/bump_version.py`.
### Changed
- Packaging metadata SPDX license string.

## [0.1.0] - 2025-08-23
### Added
- Initial public release: Python SDK (`opp-py`), exporter API, explorer UI, policy & passport features, JS preview.

[Unreleased]: https://github.com/Maverick0351a/opp-provenance-passport/compare/opp-py-v0.1.1...HEAD
[0.1.1]: https://github.com/Maverick0351a/opp-provenance-passport/compare/opp-py-v0.1.0...opp-py-v0.1.1
[0.1.0]: https://github.com/Maverick0351a/opp-provenance-passport/tree/opp-py-v0.1.0
