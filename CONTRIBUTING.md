# Contributing

1. Open an issue that describes the bug or the feature.
2. Create a short-lived branch from `main`: `feature/<short-name>`, `fix/<short-name>`, `ci/<short-name>` or `docs/<short-name>`.
3. Keep commits small. Messages follow Conventional Commits in the imperative, for example `feat: add HQIC criterion` (types: `feat`, `fix`, `ci`, `docs`, `test`, `chore`).
4. Run `ruff check .`, `ruff format --check .` and `pytest --cov` before pushing.
5. Open a pull request that links the issue (`Closes #N`). CI must be green before merging.
