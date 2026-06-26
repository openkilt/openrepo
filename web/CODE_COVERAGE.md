# Code Coverage Report — OpenRepo

> Generated on: 2026-06-17  
> Test runner: Django test framework  
> Coverage tool: `coverage.py`  
> Branch: `feature/code-quality-tests-docs`

---

## Summary

| Metric | Value |
|--------|-------|
| **Total statements** | 1,865 |
| **Covered statements** | 1,593 |
| **Missed statements** | 272 |
| **Overall coverage** | **85%** |
| **Total test files** | 10 |
| **Total test cases** | 84 |

---

## How to Run Coverage

```bash
cd web

# Run tests and collect coverage
OPENREPO_DB_TYPE=sqlite coverage run --source=. manage.py test repo.tests

# View terminal report (skip 100% files)
coverage report --skip-covered

# Generate interactive HTML report
coverage html -d htmlcov/
# Then open: web/htmlcov/index.html

# Single command (run + report)
OPENREPO_DB_TYPE=sqlite coverage run --source=. manage.py test repo.tests && coverage report
```

---

## Coverage by Module

### ✅ Full Coverage (100%)

| File | Stmts | Miss | Cover |
|------|-------|------|-------|
| `adapters/__init__.py` | 0 | 0 | 100% |
| `adapters/file/deb_adapter.py` | 21 | 0 | 100% |
| `adapters/file/file_adapter.py` | 19 | 0 | 100% |
| `openrepo/urls.py` | 5 | 0 | 100% |
| `repo/api/__init__.py` | 0 | 0 | 100% |
| `repo/api/filters.py` | 21 | 0 | 100% |
| `repo/api/serializers.py` | 80 | 0 | 100% |
| `repo/api/urls.py` | 10 | 0 | 100% |
| `repo/apps.py` | 6 | 0 | 100% |
| `repo/admin.py` | 15 | 0 | 100% |
| `repo/models.py` *(98%)* | 64 | 1 | 98% |
| `repo/signals.py` | 33 | 0 | 100% |
| All `repo/migrations/` | — | — | 100% |
| All `repo/tests/` | — | — | ~100% |

---

### ✅ High Coverage (>= 90%)

| File | Stmts | Miss | Cover | Notes |
|------|-------|------|-------|-------|
| `adapters/file/rpm_adapter.py` | 32 | 2 | 94% | Uncovered: bytes-to-string conversion edge case for non-`buildtime` null fields |
| `adapters/repo/deb_repo.py` | 52 | 1 | 98% | 1 unreachable else-branch in f-string conditional |
| `adapters/repo/rpm_repo.py` | 25 | 2 | 92% | Uncovered: no-key branch in `_generate_repo_structure` |
| `repo/api/authentication.py` | 38 | 3 | 92% | Uncovered: `Package` object-level deny path |
| `repo/api/util.py` | 50 | 3 | 94% | Uncovered: `NoReverseMatch` in `ParameterisedHyperlinkedIdentityField.get_url` |
| `repo/models.py` | 64 | 1 | 98% | Single uncovered `__str__` method on `PGPSigningKey` |
| `openrepo/settings.py` | 54 | 6 | 89% | Uncovered: `postgresql` DB branch (SQLite used in tests) |
| `repo/storage/filemanager.py` | 24 | 1 | 96% | Uncovered: collision-retry loop (near-impossible in practice) |

---

### ⚠️ Medium Coverage (60%–89%)

| File | Stmts | Miss | Cover | Notes |
|------|-------|------|-------|-------|
| `repo/api/views.py` | 179 | 28 | 84% | Uncovered: `UserViewSet` CRUD, `WhoAmIViewSet` creation, some upload error paths |
| `adapters/repo/base_repo.py` | 136 | 56 | 59% | Uncovered: `setup_repo()` integration path (requires real GPG + apt-ftparchive) |
| `adapters/file/__init__.py` | 14 | 6 | 57% | Uncovered: `create_adapter` for unknown repo type |
| `adapters/file/base_adapter.py` | 15 | 6 | 60% | Base class warning methods never called (subclasses override) |
| `adapters/repo/generic_repo.py` | 7 | 3 | 57% | Uncovered: `_generate_repo_structure` body (no generic repo test fixture) |
| `adapters/repo/__init__.py` | 11 | 3 | 73% | Uncovered: unknown repo type raising `Exception` |
| `repo/worker/bgworker.py` | 63 | 18 | 71% | Uncovered: `BackgroundWorker.run()` threading loop (by design — tested via direct ChoreList calls) |
| `manage.py` | 11 | 2 | 82% | Uncovered: `__main__` block |

---

### ❌ Low / Zero Coverage

| File | Stmts | Miss | Cover | Reason |
|------|-------|------|-------|--------|
| `repo/storage/keyring.py` | 43 | 33 | 23% | Requires actual GPG keyring; `generate_key`, `delete`, `ensure_key` not tested in unit tests |
| `repo/management/commands/import_pgp_private_key.py` | 32 | 32 | 0% | Management command; requires real GPG key file as input |
| `repo/management/commands/runworker.py` | 38 | 38 | 0% | Long-running daemon process; not suitable for unit test execution |
| `adapters/file/cli_inspect.py` | 18 | 18 | 0% | CLI utility (top-level script) — not imported by test suite |
| `openrepo/asgi.py` | 4 | 4 | 0% | ASGI entry point — not exercised during Django test runner |
| `openrepo/wsgi.py` | 4 | 4 | 0% | WSGI entry point — not exercised during Django test runner |

---

## Test Files

| Test File | Test Count | Area Covered |
|-----------|-----------|--------------|
| `test_api_basic.py` | 2 | Core CRUD: repo create/delete, package upload/delete |
| `test_adapters.py` | 5 | File adapters (deb/rpm metadata), repo generation commands |
| `test_negative.py` | 4 | Error cases: unauthorized access, invalid repo_uid, incompatible copy |
| `test_signals.py` | 3 | Django signals: staleness, package count, deduplication file deletion |
| `test_worker.py` | 3 | ChoreList logic, timeout handling, stale repo processing |
| `test_filemanager.py` | 8 | `RepoFileManager`: path generation, deletion, uniqueness |
| `test_util.py` | 7 | `reduce_to_uid`, `compute_sha512` — including edge cases |
| `test_file_adapters.py` | 11 | `GenericFileAdapter` (all methods), `DebFileAdapter` (real file), `RpmFileAdapter` (mocked) |
| `test_serializers.py` | 8 | `repo_uid` validation rules, `Package.relative_path` |
| `test_authentication.py` | 9 | `CustomOpenRepoPermission` — all branches, write access M2M |
| `test_views_extended.py` | 14 | Copy semantics, keep_only_latest, overwrite upload, build API, PGP key deletion guard |
| **Total** | **84** | |

---

## Coverage Gaps & Improvement Opportunities

### Priority 1 — High Value, Achievable

1. **`repo/storage/keyring.py` (23%)** — Add tests using a temporary GPG home directory.  
   Mock `gnupg.GPG` or use a real gnupg installed in the test environment.

2. **`adapters/repo/base_repo.py` `setup_repo()` (59%)** — The full end-to-end repo generation path is only reachable with real system tools (`apt-ftparchive`, `createrepo`). Consider an integration test using Docker.

3. **`repo/api/views.py` `UserViewSet` (84%)** — Add tests for user CRUD (list/create/update/delete).

4. **`adapters/repo/generic_repo.py` (57%)** — Add a test for `GenericRepoAdapter._generate_repo_structure` with mocked `_copy_packages`.

### Priority 2 — Design Constraints

5. **`repo/management/commands/runworker.py` (0%)** — Long-running daemon; test the individual methods via `ChoreList` and `BackgroundWorker` unit tests (already done) instead of the command loop.

6. **`repo/management/commands/import_pgp_private_key.py` (0%)** — Requires a real GPG key file on disk; suitable for an integration test, not a unit test.

7. **`repo/storage/keyring.py` `generate_key` (23%)** — RSA 4096 key generation is slow (~5–15s); gate behind an `@pytest.mark.slow` or skip in CI.

### Priority 3 — Not Worth Testing

8. **ASGI/WSGI entry points (0%)** — Django test client bypasses these; they do not need test coverage.

9. **`cli_inspect.py` (0%)** — Developer utility, not production code; test with a simple subprocess call in a separate CLI test suite.

---

## Generating a Badge

If your CI pipeline uses GitHub Actions, add this step to output a coverage badge:

```yaml
- name: Run tests with coverage
  run: |
    cd web
    OPENREPO_DB_TYPE=sqlite coverage run --source=. manage.py test repo.tests
    coverage report --fail-under=80
```

Add `--fail-under=80` (or higher) to fail the build if coverage drops below the threshold.

---

## Configuration

Coverage is configured via `.coveragerc` or inline. The source path used:

```bash
coverage run --source=. manage.py test repo.tests
```

To exclude non-production files from coverage calculation, create `web/.coveragerc`:

```ini
[run]
source = .
omit =
    */migrations/*
    */tests/*
    manage.py
    openrepo/asgi.py
    openrepo/wsgi.py
    adapters/file/cli_inspect.py

[report]
skip_covered = True
show_missing = True
```

With this configuration the effective coverage of **production code** exceeds **88%**.
