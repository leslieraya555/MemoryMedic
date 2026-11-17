"""Non-destructively add environment overrides needed by isolated E2E.

Runs only against the current repo's known FastAPI and Vite source patterns.
Does not alter or overwrite any existing tests or GitHub Actions workflows.
Backs up changed files under artifacts/e2e-backups/ (already gitignored).
Re-running is safe; unexpected source changes abort with a clear error.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT / "artifacts" / "e2e-backups"


def patch(relative: str, transformations: list[tuple[str, str, int]]) -> None:
    path = ROOT / relative
    original = path.read_text(encoding="utf-8")
    updated = original
    for old, new, required in transformations:
        if new in updated:
            continue
        count = updated.count(old)
        if count != required:
            raise SystemExit(
                f"ABORT: Unexpected source in {relative}. Expected {required} occurrences "
                f"of {old!r}, found {count}. No changes written to this file."
            )
        updated = updated.replace(old, new)

    if updated != original:
        backup = BACKUP / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            backup.write_text(original, encoding="utf-8")
        path.write_text(updated, encoding="utf-8")
        print(f"Updated {relative} (original backed up to {backup.relative_to(ROOT)})")
    else:
        print(f"Already configured: {relative}")


def main() -> None:
    patch("backend/app/metrics.py", [
        ("import csv\nimport math", "import csv\nimport os\nimport math", 1),
        ('DATA_ROOT = PROJECT_ROOT / "data"',
         'DATA_ROOT = Path(os.environ.get("MEMORYMEDIC_DATA_ROOT", str(PROJECT_ROOT / "data")))', 1),
    ])
    patch("backend/app/predictions.py", [
        ("from functools import lru_cache\nimport math", "from functools import lru_cache\nimport math\nimport os", 1),
        ('MODEL_ROOT = PROJECT_ROOT / "artifacts" / "ml"',
         'MODEL_ROOT = Path(os.environ.get("MEMORYMEDIC_MODEL_ROOT", str(PROJECT_ROOT / "artifacts" / "ml")))', 1),
    ])
    patch("frontend/vite.config.js", [
        ("import react from '@vitejs/plugin-react'\n",
         "import react from '@vitejs/plugin-react'\n\nconst backendTarget = process.env.MEMORYMEDIC_API_ORIGIN || 'http://127.0.0.1:8001'\n", 1),
        ("target: 'http://127.0.0.1:8001',", "target: backendTarget,", 2),
    ])
    print("Ready. The original API defaults remain 8001 and existing tests are untouched.")


if __name__ == "__main__":
    main()
