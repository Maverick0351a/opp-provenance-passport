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
1. Bump version with `python scripts/bump_version.py <patch|minor|major>`.
2. Update `CHANGELOG.md` (Unreleased section -> new version section).
3. Create tag: `git tag opp-py-vX.Y.Z && git push --tags`.
4. CI publishes to PyPI (ensure `PYPI_API_TOKEN` secret configured).

## Changelog
Maintained manually (Keep a Changelog style) and validated in CI. Automated regeneration template via `git-cliff` (config at `cliff.toml`).

## Tests
Run Python tests: `pytest -q packages/opp_py/tests`.

## Code of Conduct
Be respectful. No harassment, personal attacks, or spam.

## License Contributions
By contributing you agree your work is licensed under Apache-2.0.
