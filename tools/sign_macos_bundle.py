#!/usr/bin/env python3
"""Sign a PyInstaller macOS app bundle with a stable, minimal strategy."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], quiet: bool = False) -> None:
    if not quiet:
        subprocess.run(cmd, check=True)
        return

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return

    if result.stdout:
        print(result.stdout, file=sys.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)


def _file_type(path: Path) -> str:
    result = subprocess.run(
        ["file", "-b", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _is_macho(path: Path) -> bool:
    return "Mach-O" in _file_type(path)


def _should_skip_file(path: Path) -> bool:
    p = str(path)
    # Bundle-like containers are handled via their contained Mach-O files.
    return ".bundle/" in p or ".xpc/" in p or ".appex/" in p


def _timestamp_arg(timestamp: str) -> str:
    if timestamp == "none":
        return "--timestamp=none"
    return "--timestamp"


def _get_entitlements_file() -> Path | None:
    """Locate entitlements file if it exists."""
    # Check in build directory relative to bundle_root
    entitlements_candidates = [
        Path(__file__).parent.parent / "build" / "mcsas3gui.entitlements",
        Path(__file__).parent.parent / "mcsas3gui.entitlements",
    ]
    for candidate in entitlements_candidates:
        if candidate.is_file():
            return candidate
    return None


def _codesign(
    target: Path,
    identity: str,
    keychain: str | None,
    timestamp: str,
    deep: bool = False,
) -> None:
    cmd = [
        "codesign",
        "--force",
        "--options",
        "runtime",
        _timestamp_arg(timestamp),
        "--sign",
        identity,
    ]

    # Add entitlements file if available (required for proper notarization)
    entitlements = _get_entitlements_file()
    if entitlements:
        cmd.extend(["--entitlements", str(entitlements)])

    if deep:
        cmd.append("--deep")
    if keychain:
        cmd.extend(["--keychain", keychain])
    cmd.append(str(target))
    _run(cmd, quiet=True)


def _load_paths(bundle_root: Path) -> tuple[Path, Path]:
    build_info = bundle_root / "build_info.json"
    payload = json.loads(build_info.read_text(encoding="utf-8"))
    app_path = bundle_root / payload["gui_bundle"]
    helper_path = bundle_root / payload["bundled_histogrammer"]
    if not app_path.is_dir():
        raise RuntimeError(f"Missing app bundle: {app_path}")
    if not helper_path.is_file():
        raise RuntimeError(f"Missing helper executable: {helper_path}")
    return app_path, helper_path


def _ensure_symlink(path: Path, target: str) -> None:
    if path.is_symlink():
        if os.readlink(path) == target:
            return
        path.unlink()
    elif path.exists():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    path.symlink_to(target)


def _normalize_framework(framework_dir: Path) -> None:
    versions_dir = framework_dir / "Versions"
    if not versions_dir.is_dir():
        return

    version_dirs = sorted(
        path for path in versions_dir.iterdir() if path.is_dir() and path.name != "Current"
    )
    if not version_dirs:
        return
    canonical_version = version_dirs[0]

    current = versions_dir / "Current"
    if current.is_symlink():
        current_target = (versions_dir / os.readlink(current)).resolve()
        if not current_target.exists():
            current.unlink()
            current.symlink_to(canonical_version.name)
    elif current.exists():
        if current.is_dir():
            shutil.rmtree(current)
        else:
            current.unlink()
        current.symlink_to(canonical_version.name)
    else:
        current.symlink_to(canonical_version.name)

    framework_name = framework_dir.stem
    version_binary = versions_dir / "Current" / framework_name
    if version_binary.exists():
        _ensure_symlink(
            framework_dir / framework_name,
            f"Versions/Current/{framework_name}",
        )

    version_resources = versions_dir / "Current" / "Resources"
    if version_resources.exists():
        _ensure_symlink(framework_dir / "Resources", "Versions/Current/Resources")

    root_signature = framework_dir / "_CodeSignature"
    if root_signature.exists():
        shutil.rmtree(root_signature)


def _normalize_framework_layouts(app_path: Path) -> None:
    frameworks = sorted(path for path in app_path.rglob("*.framework") if path.is_dir())
    for framework in frameworks:
        _normalize_framework(framework)


def _sign_bundle(bundle_root: Path, identity: str, keychain: str | None, timestamp: str) -> None:
    app_path, helper_path = _load_paths(bundle_root)
    seen_realpaths: set[Path] = set()
    app_executable = app_path / "Contents" / "MacOS" / app_path.stem
    nested_apps = sorted(
        path
        for path in (app_path / "Contents").rglob("*.app")
        if path.is_dir() and path.resolve() != app_path.resolve()
    )

    # 0) Normalize framework wrappers; PyInstaller often materializes wrapper
    # files instead of symlinks, which makes codesign treat them as ambiguous.
    _normalize_framework_layouts(app_path)

    # 1) Sign helper executable first.
    _codesign(helper_path, identity, keychain, timestamp)
    seen_realpaths.add(helper_path.resolve())

    # 2) Sign every unique Mach-O file in Contents/.
    for candidate in sorted((app_path / "Contents").rglob("*")):
        if candidate.is_symlink() or not candidate.is_file() or _should_skip_file(candidate):
            continue
        if candidate == app_executable:
            continue
        if any(nested_app in candidate.parents for nested_app in nested_apps):
            continue
        if not _is_macho(candidate):
            continue
        real_candidate = candidate.resolve()
        if real_candidate in seen_realpaths:
            continue
        _codesign(real_candidate, identity, keychain, timestamp)
        seen_realpaths.add(real_candidate)

    # 3) Sign nested helper app bundles first if present.
    for nested_app in nested_apps:
        _codesign(nested_app, identity, keychain, timestamp, deep=True)

    # 4) Sign top-level app bundle recursively to ensure all contents are verified.
    _codesign(app_path, identity, keychain, timestamp, deep=True)

    # 5) Verify full bundle recursively.
    _run(["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(app_path)])
    _run(["codesign", "--display", "--verbose=4", str(app_path)])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", required=True, type=Path)
    parser.add_argument("--identity", required=True)
    parser.add_argument("--keychain")
    parser.add_argument(
        "--timestamp",
        choices=("auto", "none"),
        default="auto",
        help="Use Apple timestamping, or disable timestamping for local development signing.",
    )
    args = parser.parse_args()

    _sign_bundle(args.bundle_root.resolve(), args.identity, args.keychain, args.timestamp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
