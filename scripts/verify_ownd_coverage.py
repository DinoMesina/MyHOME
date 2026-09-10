#!/usr/bin/env python3
"""Strict 100% Test Coverage Enforcer for ownd.

Ensures that all modules within custom_components/myhome/ownd maintain
100.0% line coverage (zero missing lines). Any new or modified module
in ownd that falls below 100% coverage will cause CI to fail.
"""
import os
import sys
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWND_DIR = os.path.join(REPO_ROOT, "custom_components", "myhome", "ownd")
COVERAGE_XML = os.path.join(REPO_ROOT, "coverage.xml")

# Modules excluded from 100% enforcement (e.g. standalone interactive CLI)
EXCLUDED_MODULES = {
    "__main__.py",
}


def verify_ownd_coverage(xml_path: str = COVERAGE_XML) -> int:
    """Validate that every ownd file has 100% test coverage in coverage.xml."""
    if not os.path.exists(xml_path):
        print(f"[ERROR] Coverage report '{xml_path}' not found. Run pytest with --cov-report=xml first.")
        return 1

    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Map normalized relative filenames to (line_rate, uncovered_lines)
    coverage_data = {}
    for pkg in root.findall(".//package"):
        for cls in pkg.findall(".//class"):
            fn = cls.attrib.get("filename", "").replace("\\", "/")
            rate = float(cls.attrib.get("line-rate", 0)) * 100.0
            lines = cls.findall(".//line")
            uncovered = [l.attrib.get("number") for l in lines if l.attrib.get("hits") == "0"]
            coverage_data[fn] = (rate, uncovered)

    # Discover all Python source files in ownd directory on disk
    disk_files = []
    for root_dir, _, files in os.walk(OWND_DIR):
        for f in files:
            if f.endswith(".py") and f not in EXCLUDED_MODULES:
                full_path = os.path.join(root_dir, f)
                rel_path = os.path.relpath(full_path, REPO_ROOT).replace("\\", "/")
                disk_files.append(rel_path)

    if not os.path.exists(OWND_DIR) or not disk_files:
        print(
            f"[INFO] No vendored ownd directory found at '{OWND_DIR}' "
            "(running with external OWNd package). Skipping vendored coverage check."
        )
        return 0

    print(f"[CHECK] Verifying strict 100% test coverage for {len(disk_files)} module(s) in ownd...")
    errors = []
    for rel in sorted(disk_files):
        if rel not in coverage_data:
            errors.append(f"[FAIL] {rel}: Missing from coverage report (module is untested or omitted)")
            continue

        rate, uncovered = coverage_data[rel]
        if rate < 100.0:
            errors.append(
                f"[FAIL] {rel}: {rate:.1f}% coverage (Missing lines: {', '.join(uncovered)})"
            )
        else:
            print(f"  [OK] {rel}: 100.0% coverage (0 uncovered lines)")

    if errors:
        print("\n" + "=" * 70)
        print("OWND 100% COVERAGE ENFORCEMENT FAILED:")
        print("=" * 70)
        for err in errors:
            print(f"  {err}")
        print("\nAll modules in 'custom_components/myhome/ownd/' must maintain 100% coverage.")
        print("Please add unit tests covering the missing lines above before merging.")
        print("=" * 70)
        return 1

    print(f"\n[SUCCESS] All {len(disk_files)} ownd module(s) strictly meet 100.0% test coverage!")
    return 0


if __name__ == "__main__":
    coverage_file = sys.argv[1] if len(sys.argv) > 1 else COVERAGE_XML
    sys.exit(verify_ownd_coverage(coverage_file))
