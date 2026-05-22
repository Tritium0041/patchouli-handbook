# Release Process

This package is published from GitHub Actions with PyPI Trusted Publishing.

## One-time PyPI setup

Create the project on PyPI, or create a pending publisher if the project does
not exist yet, and add a trusted publisher with these values:

- PyPI project name: `patchouli-handbook`
- Owner: `Tritium0041`
- Repository name: `patchouli-handbook`
- Workflow filename: `ci.yml`
- Environment name: `pypi`

Trusted Publishing lets GitHub Actions publish through OpenID Connect, so no
long-lived PyPI API token needs to be stored in GitHub secrets.

Pending publishers do not reserve the package name before the first publish.
The name `patchouli-handbook` should still be checked immediately before the
first release.

## Cutting a release

1. Update `version` in `pyproject.toml`.
2. Commit and push the change to `main`.
3. Create and push a matching version tag:

   ```sh
   git tag v0.1.0
   git push origin v0.1.0
   ```

The `CI` workflow runs tests, builds the source distribution and wheel, checks
the artifacts, and publishes to PyPI when the pushed ref is a `v*` tag.
