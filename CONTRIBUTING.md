# Contributing

Thanks for your interest in improving ODIN Provenance Passport.

## Commit Messages (Conventional Commits)

Use the following types:

- feat: user-facing feature
- fix: bug fix
- docs: documentation only
- chore: build/system/tooling changes
- refactor: code change w/o behavior change
- perf: performance improvement
- test: add or update tests
- ci: CI configuration changes
- build: packaging or dependency changes

Format:

  <type>(optional scope): <short summary>

Examples:

  feat(decorator): add outputs CID support
  fix(exporter): handle missing signature headers gracefully

Body and footer (optional) follow standard Conventional Commits spec. Breaking changes include a ! after type/scope or a BREAKING CHANGE: footer.

## Versioning
Semantic Versioning (MAJOR.MINOR.PATCH). The package version lives in `packages/opp_py/pyproject.toml`.

## Release Flow
Automated helpers now reduce manual steps:

1. Bump version locally (optional) with `python scripts/bump_version.py <patch|minor|major>` OR let the tag workflow sync it.
2. Ensure `CHANGELOG.md` Unreleased section has your entries (Conventional Commit labels help auto‑categorize).
3. Create a tag: `git tag opp-py-vX.Y.Z && git push --tags`.
4. Workflows triggered by the tag will:
  - Sync `pyproject.toml` version if mismatched.
  - Generate/update structured changelog section via `git-cliff`.
  - Draft / update a GitHub Release (release-drafter) — finalize manually if desired.
  - Publish to PyPI (`publish-opp-py`) assuming secrets configured.

If you prefer full automation, skip manual bump; the tag-derived version is authoritative.

## Changelog
Primarily managed in `CHANGELOG.md` (Keep a Changelog). On tag push, `git-cliff` injects the new version section if absent. Conventional Commit types + PR labels ensure correct categorization.

PRs must include at least one category label: `feat|fix|docs|chore|refactor|perf|test|ci|build` (enforced by CI). This feeds release notes & changelog grouping.

## Tests
Run Python tests: `pytest -q packages/opp_py/tests`.

## Code of Conduct
Be respectful. No harassment, personal attacks, or spam.

## License Contributions
By contributing you agree your work is licensed under Apache-2.0.
