#!/usr/bin/env python3
"""
Packaging script for MyHOME Home Assistant Integration.
Creates a HACS-compliant `myhome.zip` release asset containing the contents of
`custom_components/myhome/` at the root of the archive.
"""

import json
import os
import re
import sys
import zipfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMPONENT_DIR = os.path.join(REPO_ROOT, "custom_components", "myhome")
MANIFEST_PATH = os.path.join(COMPONENT_DIR, "manifest.json")
CONST_PATH = os.path.join(COMPONENT_DIR, "const.py")
OUTPUT_ZIP = os.path.join(REPO_ROOT, "myhome.zip")

EXCLUDE_PATTERNS = [
    r"__pycache__",
    r"\.pyc$",
    r"\.pyo$",
    r"\.pytest_cache",
    r"\.DS_Store",
    r"\.coverage",
]


def check_versions():
    """Verify version consistency across manifest.json and const.py."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    manifest_version = manifest.get("version")

    with open(CONST_PATH, "r", encoding="utf-8") as f:
        const_content = f.read()
    match = re.search(r'INTEGRATION_VERSION\s*=\s*["\']([^"\']+)["\']', const_content)
    const_version = match.group(1) if match else None

    print(f"[CHECK] manifest.json version: {manifest_version}")
    print(f"[CHECK] const.py version:       {const_version}")

    if manifest_version != const_version:
        print(f"[ERROR] Version mismatch: {manifest_version} != {const_version}", file=sys.stderr)
        sys.exit(1)

    return manifest_version


def should_exclude(rel_path):
    """Check if file should be excluded from release package."""
    norm_path = rel_path.replace("\\", "/")
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, norm_path):
            return True
    return False


def build_zip(version):
    """Build the HACS-compliant myhome.zip package."""
    print(f"\n[BUILD] Packaging myhome.zip for version {version}...")
    if os.path.exists(OUTPUT_ZIP):
        os.remove(OUTPUT_ZIP)

    file_count = 0
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, files in os.walk(COMPONENT_DIR):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if not should_exclude(d)]
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, COMPONENT_DIR)
                if should_exclude(rel_path):
                    continue
                # Store using forward slashes for zip compatibility
                arcname = rel_path.replace("\\", "/")
                zf.write(abs_path, arcname)
                file_count += 1

    zip_size = os.path.getsize(OUTPUT_ZIP)
    print(f"[SUCCESS] Created {OUTPUT_ZIP}")
    print(f"          Total packaged files: {file_count}")
    print(f"          Archive size:         {zip_size:,} bytes ({zip_size / 1024:.1f} KB)")


def verify_zip():
    """Verify integrity and structure of generated zip."""
    with zipfile.ZipFile(OUTPUT_ZIP, "r") as zf:
        namelist = zf.namelist()
        if "manifest.json" not in namelist:
            print("[ERROR] manifest.json is not in the root of the zip archive!", file=sys.stderr)
            sys.exit(1)
        if "__init__.py" not in namelist:
            print("[ERROR] __init__.py is not in the root of the zip archive!", file=sys.stderr)
            sys.exit(1)
        print("[VERIFY] Archive structure verified successfully. HACS compliant.")


if __name__ == "__main__":
    ver = check_versions()
    build_zip(ver)
    verify_zip()
