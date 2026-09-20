from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "custom_components" / "occupancy_duration" / "manifest.json"
PYPROJECT_PATH = ROOT / "pyproject.toml"
SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")
PYPROJECT_VERSION_RE = re.compile(r'(?m)^(version\s*=\s*")([^"]+)(")$')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize release version across repository metadata files.",
    )
    parser.add_argument("version", help="Semantic version, with or without a leading v.")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Persist the version changes instead of only printing the planned updates.",
    )
    return parser.parse_args()


def normalize_version(raw_version: str) -> str:
    match = SEMVER_RE.fullmatch(raw_version.strip())
    if not match:
        raise ValueError(
            "Release version must be semantic versioning like 0.1.0 or v0.1.0.",
        )
    major, minor, patch = match.group(1), match.group(2), match.group(3)
    return f"{major}.{minor}.{patch}"


def update_manifest(version: str, write: bool) -> tuple[str, str]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    current = str(manifest["version"])
    manifest["version"] = version
    if write:
        MANIFEST_PATH.write_text(f"{json.dumps(manifest, indent=2)}\n", encoding="utf-8")
    return current, version


def update_pyproject(version: str, write: bool) -> tuple[str, str]:
    content = PYPROJECT_PATH.read_text(encoding="utf-8")
    match = PYPROJECT_VERSION_RE.search(content)
    if match is None:
        raise ValueError("Could not locate [project].version in pyproject.toml.")
    current = match.group(2)
    updated = PYPROJECT_VERSION_RE.sub(rf'\g<1>{version}\g<3>', content, count=1)
    if write:
        PYPROJECT_PATH.write_text(updated, encoding="utf-8")
    return current, version


def main() -> int:
    args = parse_args()
    version = normalize_version(args.version)
    manifest_before, manifest_after = update_manifest(version, args.write)
    pyproject_before, pyproject_after = update_pyproject(version, args.write)

    mode = "updated" if args.write else "would update"
    print(f"manifest.json: {manifest_before} -> {manifest_after} ({mode})")
    print(f"pyproject.toml: {pyproject_before} -> {pyproject_after} ({mode})")
    print(f"release tag: v{version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())