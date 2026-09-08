#!/usr/bin/env python3
"""Update README.md coverage table and coverage.svg from coverage.xml.

Maintains live, automated documentation of test coverage across all components.
Called locally and by the GitHub Actions test-coverage workflow.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COVERAGE_XML = os.path.join(REPO_ROOT, "coverage.xml")
README_MD = os.path.join(REPO_ROOT, "README.md")
COVERAGE_SVG = os.path.join(REPO_ROOT, "coverage.svg")

START_MARKER = "<!-- START_COVERAGE_TABLE -->"
END_MARKER = "<!-- END_COVERAGE_TABLE -->"

COMPONENT_NOTES = {
    "custom_components/myhome/validate.py": "Device & gateway schemas, custom WHERE validators, sensor injections",
    "custom_components/myhome/gateway_profile.py": "Hardware models (`MH200`, `F454`, etc.) and queue pacing limits",
    "custom_components/myhome/const.py": "Protocol commands, dimensions, and integration constants",
    "custom_components/myhome/decoder_pool.py": "Thread-safe streaming proxy audio pool",
    "custom_components/myhome/myhome_device.py": "Home Assistant device registry schema compliance",
    "custom_components/myhome/sensor.py": "Power meters, energy counters, and pulse sensors",
    "custom_components/myhome/climate.py": "Heating, cooling, 4-pipe systems, and thermostat controls",
    "custom_components/myhome/gateway.py": "Hardware handler, lockout prevention, token-bucket queue",
    "custom_components/myhome/media_player.py": "F441/F441M sound system zones, dynamic proxy, gain-staging",
    "custom_components/myhome/ownd/connection.py": "Hardened TCP stream, fail-closed auth, watchdog loop",
    "custom_components/myhome/bus_monitor.py": "In-band 500-frame circular ring buffer tap (0 extra sockets)",
    "custom_components/myhome/device_trigger.py": "Stateless CEN/CEN+ scenario device automation triggers",
    "custom_components/myhome/diagnostics.py": "Config entry diagnostics with sensitive data redaction",
    "custom_components/myhome/core/transport/serial.py": "Async Serial/USB transport for Legrand 3578 / OpenZigBee",
    "custom_components/myhome/core/transport/tcp.py": "Modular TCP/IP socket transport with framed stream parsing",
    "custom_components/myhome/core/transport/base.py": "Abstract transport layer defining OWN lifecycle contract",
    "custom_components/myhome/light.py": "Relays, auto-dimmer detection, and brightness transitions",
    "custom_components/myhome/ownd/discovery.py": "SSDP & UPnP gateway detection and descriptor parsing",
    "custom_components/myhome/ownd/message.py": "OpenWebNet frame parsers, encoders, and dimension decoders",
    "custom_components/myhome/config_flow.py": "Step handlers, user entry, reauth, and options flow",
    "custom_components/myhome/button.py": "Scenario buttons and bus diagnostic pings",
    "custom_components/myhome/binary_sensor.py": "Magnetic contacts, door/window sensors, motion sensors",
    "custom_components/myhome/cover.py": "Motorized shutters, blinds, roll-ups with state tracking",
    "custom_components/myhome/__init__.py": "Setup lifecycle and zero-friction entity migration",
    "custom_components/myhome/switch.py": "Relay actuators, auxiliary switches, socket controllers",
}


def update_readme_and_svg():
    if not os.path.exists(COVERAGE_XML):
        print(f"Error: {COVERAGE_XML} not found. Run pytest with --cov-report=xml first.")
        sys.exit(1)

    tree = ET.parse(COVERAGE_XML)
    root = tree.getroot()
    total_rate = float(root.attrib.get("line-rate", 0)) * 100
    rate_round = round(total_rate)

    # ── 1. Generate updated coverage.svg ─────────────────────────────────────
    color = "#4c1" if rate_round >= 80 else ("#dfb317" if rate_round >= 60 else "#e05d44")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="98" height="20"><linearGradient id="b" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient><mask id="a"><rect width="98" height="20" rx="3" fill="#fff"/></mask><g mask="url(#a)"><path fill="#555" d="M0 0h61v20H0z"/><path fill="{color}" d="M61 0h37v20H61z"/><path fill="url(#b)" d="M0 0h98v20H0z"/></g><g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11"><text x="30.5" y="15" fill="#010101" fill-opacity=".3">coverage</text><text x="30.5" y="14">coverage</text><text x="79.5" y="15" fill="#010101" fill-opacity=".3">{rate_round}%</text><text x="79.5" y="14">{rate_round}%</text></g></svg>'''
    with open(COVERAGE_SVG, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Updated {COVERAGE_SVG} -> {rate_round}% ({color})")

    # ── 2. Collect per-component coverage ────────────────────────────────────
    file_rates = {}
    for p in root.findall(".//package"):
        for c in p.findall(".//class"):
            fn = c.attrib.get("filename", "").replace("\\", "/")
            # Filter out non-code or trivial init
            if fn in ("custom_components/myhome/ownd/__main__.py", "custom_components/myhome/ownd/__init__.py", "custom_components/myhome/core/__init__.py", "custom_components/myhome/core/transport/__init__.py"):
                continue
            cr = float(c.attrib.get("line-rate", 0)) * 100
            file_rates[fn] = cr

    # Sort files: 100% files first (by note order), then descending coverage
    def sort_key(item):
        fn, rate = item
        # Priority order: by coverage rate descending, then filename
        return (-round(rate, 1), fn)

    sorted_files = sorted(file_rates.items(), key=sort_key)

    # ── 3. Build Markdown table ──────────────────────────────────────────────
    table_lines = [
        "| Component / Module | Coverage | Notes |",
        "|---|:---:|---|",
    ]

    for fn, rate in sorted_files:
        display_name = fn.replace("custom_components/myhome/", "")
        notes = COMPONENT_NOTES.get(fn, "Core integration component")
        rate_str = f"**{round(rate)}%**" if round(rate) >= 90 else f"{round(rate)}%"
        table_lines.append(f"| [`{display_name}`]({fn}) | {rate_str} | {notes} |")

    new_table_block = "\n".join(table_lines)

    # ── 4. Update README.md ──────────────────────────────────────────────────
    if not os.path.exists(README_MD):
        print(f"Error: {README_MD} not found.")
        sys.exit(1)

    with open(README_MD, "r", encoding="utf-8") as f:
        content = f.read()

    # If markers exist, replace between them
    if START_MARKER in content and END_MARKER in content:
        pattern = re.compile(
            rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
            re.DOTALL,
        )
        replacement = f"{START_MARKER}\n\n{new_table_block}\n\n{END_MARKER}"
        content = pattern.sub(replacement, content)
    else:
        # Replace existing static table
        table_pattern = re.compile(
            r"\| Component / Module \| Coverage \| Notes \|.*?(?=\n\n> \*\*Live Test Execution\*\*)",
            re.DOTALL,
        )
        content = table_pattern.sub(
            f"{START_MARKER}\n\n{new_table_block}\n\n{END_MARKER}",
            content,
        )

    # Update summary test count mention
    content = re.sub(
        r"The integration maintains over \d+ automated tests",
        f"The integration maintains over 660 automated tests ({rate_round}% line coverage)",
        content,
    )
    content = re.sub(
        r"Over \d+ automated unit tests",
        f"Over 660 automated unit tests ({rate_round}% line coverage)",
        content,
    )
    content = re.sub(
        r"\*\*`test-coverage`\*\*: \d+\+? automated unit tests",
        f"**`test-coverage`**: 662 automated unit tests",
        content,
    )

    with open(README_MD, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Updated {README_MD} coverage table successfully ({len(sorted_files)} components, total {rate_round}%).")


if __name__ == "__main__":
    update_readme_and_svg()
