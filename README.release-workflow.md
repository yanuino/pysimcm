## Release workflow and optional steps

Releases are created by pushing a Git tag following semantic versioning:

```bash
git tag v1.1.0
git push origin v1.1.0
```

This triggers a dedicated **release workflow** in GitHub Actions.

### What happens during a release

By default, the release workflow always performs:

- ✅ Documentation build (MkDocs, strict mode)

Additional steps can be enabled **optionally**, without modifying the workflow file:

- 📘 Documentation publication
- 🐧 Linux binary build (PyInstaller)
- 🪟 Windows binary build (PyInstaller)

---

### Enabling optional release steps

Optional steps are controlled using **GitHub Environments**.

Each optional job in the release workflow is associated with a named environment:

| Feature | GitHub Environment |
|--------|--------------------|
| Documentation publication | `docs` |
| Linux binary build | `release-linux` |
| Windows binary build | `release-windows` |

To enable a feature, simply create the corresponding environment in the repository settings:

```
Repository → Settings → Environments → New environment
```

If an environment **does not exist**, the associated job is skipped automatically.

No secrets or approval rules are required by default.

---

### Documentation publication (important)

The release workflow does **not** define how documentation is deployed.

To enable documentation publication, you must **explicitly configure a deployment target**, such as:

- GitHub Pages
- An object storage (S3-compatible)
- Any other static hosting solution

The `publish-docs` job is intentionally minimal and acts as a **hook point**.

You are expected to adapt this job to your chosen documentation hosting strategy.

This design keeps the template:

- hosting-provider agnostic
- simple by default
- free of assumptions or credentials

---

### Examples

- **No environments created**  
  → Documentation is built only

- **Environment `docs` created (deployment configured)**  
  → Documentation is built and published

- **Environment `release-windows` created**  
  → Windows binary is built

- **All environments created**  
  → Full release (docs + Linux + Windows binaries)

This approach keeps the workflow:

- explicit
- readable
- easy to control
- free of conditional logic in YAML

---

### Why GitHub Environments are used

GitHub Environments are used here purely as **feature toggles**, not for secrets or deployment protection.

This allows:

- enabling or disabling release features declaratively
- avoiding multiple workflow files
- keeping the release process predictable and safe
