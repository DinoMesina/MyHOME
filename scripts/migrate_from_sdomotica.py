#!/usr/bin/env python3
"""SDomotica to MyHOME Frictionless Migration Tool.

This utility automates the migration from SDomotica to the native MyHOME
(OpenWebNet) Home Assistant integration.

Modes:
  1. YAML Generation (--generate-yaml):
     Scans Home Assistant's entity registry for legacy SDomotica entities
     (sdomoticabticino*, audio_zone_*) and generates a ready-to-use myhome.yaml
     pre-keyed to preserve exact entity IDs, friendly names, and room areas.

  2. In-Place Registry Migration (--migrate-registry):
     Safely creates a timestamped backup of core.entity_registry and updates
     orphaned SDomotica entries in-place to platform 'myhome' with native
     unique_ids. This eliminates entity_id renaming (_2 suffix), preserves
     historical statistics, and retains all room/area assignments.

Usage examples:
  python scripts/migrate_from_sdomotica.py --config-dir /config --generate-yaml myhome.yaml
  python scripts/migrate_from_sdomotica.py --config-dir /config --migrate-registry --gateway-mac 00:03:50:20:00:01
  python scripts/migrate_from_sdomotica.py --config-dir ~/.homeassistant --dry-run
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
_LOGGER = logging.getLogger("migrate_sdomotica")

# Regex patterns for matching SDomotica and audio entities
SDOMOTICA_ENTITY_RE = re.compile(
    r"^(?P<domain>light|cover|switch|sensor|binary_sensor)\.sdomoticabticino(?P<address>[0-9a-zA-Z_#]+)$",
    re.IGNORECASE,
)
AUDIO_ZONE_ENTITY_RE = re.compile(
    r"^(?P<domain>media_player)\.audio_zone_(?P<zone>[0-9]+)$",
    re.IGNORECASE,
)


class SDomoticaEntity:
    """Represents a discovered SDomotica entity to be migrated."""

    def __init__(
        self,
        domain: str,
        entity_id: str,
        address: str,
        original_unique_id: str,
        name: str | None = None,
        area_id: str | None = None,
        icon: str | None = None,
        raw_entry: dict[str, Any] | None = None,
    ) -> None:
        self.domain = domain.lower()
        self.entity_id = entity_id
        self.address = address
        self.original_unique_id = original_unique_id
        self.name = name or entity_id.split(".")[-1]
        self.area_id = area_id
        self.icon = icon
        self.raw_entry = raw_entry or {}

        # Parse WHERE and optional BUS Interface (e.g. "18#4#02")
        self.where: str = address
        self.interface: str | None = None
        if "#4#" in address:
            parts = address.split("#4#")
            self.where = parts[0]
            self.interface = parts[1]
        elif "#" in address:
            parts = address.split("#")
            self.where = parts[0]
            if len(parts) > 1 and parts[1]:
                self.interface = parts[1]

        # Determine OpenWebNet WHO subsystem
        if self.domain == "light":
            self.who = "1"
        elif self.domain == "switch":
            self.who = "1"
        elif self.domain == "cover":
            self.who = "2"
        elif self.domain == "media_player":
            self.who = "16"
        else:
            self.who = "1"

    @property
    def object_id(self) -> str:
        """Return the object_id portion of the entity_id."""
        return self.entity_id.split(".", 1)[-1]

    def compute_myhome_unique_id(self, gateway_mac: str) -> str:
        """Compute the native unique_id format expected by MyHOME."""
        mac = gateway_mac.lower().replace("-", ":")
        if self.domain == "media_player":
            clean_dev_id = self.address
        elif self.interface:
            clean_dev_id = f"{self.where}#4#{self.interface}"
        else:
            clean_dev_id = self.where
        return f"{mac}-{self.who}-{clean_dev_id}"


def find_entity_registry(config_dir: str | Path) -> Path | None:
    """Find the core.entity_registry file in config directory or fallback paths."""
    candidates = [
        Path(config_dir) / ".storage" / "core.entity_registry",
        Path(config_dir) / "core.entity_registry",
        Path(config_dir) / "storage" / "core.entity_registry",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def find_gateway_mac_from_config(config_dir: str | Path) -> str | None:
    """Attempt to detect existing MyHOME gateway MAC from core.config_entries."""
    entries_file = Path(config_dir) / ".storage" / "core.config_entries"
    if not entries_file.is_file():
        return None
    try:
        with open(entries_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        for entry in data.get("data", {}).get("entries", []):
            if entry.get("domain") == "myhome":
                mac = entry.get("data", {}).get("mac") or entry.get("unique_id")
                if mac:
                    return str(mac)
    except Exception as err:
        _LOGGER.debug("Could not read config entries for gateway MAC: %s", err)
    return None


def extract_sdomotica_entities(registry_data: dict[str, Any]) -> list[SDomoticaEntity]:
    """Parse entities from core.entity_registry matching SDomotica conventions."""
    entities: list[SDomoticaEntity] = []
    data = registry_data.get("data", {})
    raw_entities = data.get("entities", [])

    for item in raw_entities:
        entity_id = item.get("entity_id", "")
        unique_id = str(item.get("unique_id", ""))
        platform = str(item.get("platform", "")).lower()

        # Check SDomotica patterns
        sdomotica_match = SDOMOTICA_ENTITY_RE.match(entity_id)
        audio_match = AUDIO_ZONE_ENTITY_RE.match(entity_id)

        if sdomotica_match:
            domain = sdomotica_match.group("domain")
            address = sdomotica_match.group("address")
        elif audio_match:
            domain = audio_match.group("domain")
            address = audio_match.group("zone")
        elif "sdomotica" in unique_id.lower() or platform == "sdomotica":
            domain = entity_id.split(".", 1)[0]
            # Try to extract address from entity_id or unique_id
            digits = "".join(filter(str.isdigit, entity_id.split(".")[-1]))
            address = digits or entity_id.split(".")[-1]
        else:
            continue

        name = item.get("name") or item.get("original_name") or entity_id.split(".")[-1]
        area_id = item.get("area_id")
        icon = item.get("icon") or item.get("original_icon")

        entities.append(
            SDomoticaEntity(
                domain=domain,
                entity_id=entity_id,
                address=address,
                original_unique_id=unique_id,
                name=name,
                area_id=area_id,
                icon=icon,
                raw_entry=item,
            )
        )

    return entities


def generate_myhome_yaml(
    entities: list[SDomoticaEntity],
    gateway_mac: str,
    gateway_host: str = "192.168.1.50",
    gateway_port: int = 20000,
) -> str:
    """Generate a formatted myhome.yaml content preserving entity keys and addresses."""
    lines: list[str] = [
        "# ═════════════════════════════════════════════════════════════════",
        "# MyHOME Configuration Generated from SDomotica Migration Tool",
        f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "# Preserves exact entity IDs for zero-touch Lovelace & automation compatibility",
        "# ═════════════════════════════════════════════════════════════════",
        "",
        "myhome:",
        f"  mac: \"{gateway_mac}\"",
        f"  host: \"{gateway_host}\"",
        f"  port: {gateway_port}",
        "",
    ]

    # Group entities by domain
    by_domain: dict[str, list[SDomoticaEntity]] = {}
    for ent in entities:
        by_domain.setdefault(ent.domain, []).append(ent)

    domain_order = ["light", "cover", "switch", "media_player", "binary_sensor", "sensor"]
    for domain in domain_order:
        domain_entities = by_domain.get(domain, [])
        if not domain_entities:
            continue

        lines.append(f"  # ── {domain.upper()} ({len(domain_entities)} devices) ──────────────────────")
        lines.append(f"  {domain}:")

        for ent in domain_entities:
            lines.append(f"    {ent.object_id}:")
            if domain == "media_player":
                lines.append(f"      zone: \"{ent.address}\"")
            else:
                lines.append(f"      where: \"{ent.where}\"")
                if ent.interface:
                    lines.append(f"      interface: \"{ent.interface}\"")

            lines.append(f"      name: \"{ent.name}\"")
            if ent.area_id:
                lines.append(f"      # area: {ent.area_id}")
            if ent.icon:
                lines.append(f"      icon: \"{ent.icon}\"")
            if domain == "cover":
                lines.append("      advanced: false")

        lines.append("")

    return "\n".join(lines)


def migrate_registry_in_place(
    registry_path: Path,
    entities: list[SDomoticaEntity],
    gateway_mac: str,
    dry_run: bool = False,
) -> tuple[int, Path | None]:
    """Safely migrate orphaned SDomotica entries in core.entity_registry in-place."""
    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_entities = data.get("data", {}).get("entities", [])
    entity_map = {e.entity_id: e for e in entities}
    updated_count = 0

    for item in raw_entities:
        eid = item.get("entity_id")
        if eid in entity_map:
            ent = entity_map[eid]
            new_unique_id = ent.compute_myhome_unique_id(gateway_mac)
            item["platform"] = "myhome"
            item["unique_id"] = new_unique_id
            updated_count += 1

    if dry_run or updated_count == 0:
        return updated_count, None

    # Create timestamped backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = registry_path.parent / f"{registry_path.name}.backup_sdomotica_{timestamp}"
    shutil.copy2(registry_path, backup_path)
    _LOGGER.info("Created safety backup of registry at: %s", backup_path)

    # Write atomically
    temp_path = registry_path.parent / f"{registry_path.name}.tmp_{timestamp}"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    shutil.move(str(temp_path), str(registry_path))

    return updated_count, backup_path


def main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="SDomotica to MyHOME Frictionless Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config-dir",
        default=".",
        help="Home Assistant configuration directory containing .storage (default: current directory)",
    )
    parser.add_argument(
        "--gateway-mac",
        default=None,
        help="MAC address of the MyHOME gateway (e.g. 00:03:50:20:00:01)",
    )
    parser.add_argument(
        "--generate-yaml",
        metavar="OUTPUT_FILE",
        default=None,
        help="Generate a myhome.yaml configuration file and save to the specified path",
    )
    parser.add_argument(
        "--migrate-registry",
        action="store_true",
        help="Perform safe in-place migration of core.entity_registry (HA should be stopped)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying any files",
    )

    args = parser.parse_args(argv)

    config_path = Path(args.config_dir).resolve()
    registry_path = find_entity_registry(config_path)

    if not registry_path:
        _LOGGER.error(
            "Could not find core.entity_registry in '%s'. Please specify the Home Assistant configuration directory with --config-dir.",
            config_path,
        )
        return 1

    _LOGGER.info("Found Home Assistant entity registry at: %s", registry_path)

    with open(registry_path, "r", encoding="utf-8") as f:
        registry_data = json.load(f)

    entities = extract_sdomotica_entities(registry_data)
    _LOGGER.info("Identified %d SDomotica entities eligible for migration.", len(entities))

    if not entities:
        _LOGGER.warning("No legacy SDomotica entities found in registry. Nothing to migrate.")
        return 0

    # Summary table
    by_domain: dict[str, int] = {}
    for e in entities:
        by_domain[e.domain] = by_domain.get(e.domain, 0) + 1

    print("\n--- Discovered SDomotica Entities ---")
    for domain, count in sorted(by_domain.items()):
        print(f"  • {domain:<15}: {count:>3} devices")
    print("-------------------------------------\n")

    gateway_mac = (
        args.gateway_mac
        or find_gateway_mac_from_config(config_path)
        or "00:03:50:20:00:01"
    )
    _LOGGER.info("Target MyHOME Gateway MAC: %s", gateway_mac)

    # 1. YAML Generation Mode
    if args.generate_yaml:
        yaml_content = generate_myhome_yaml(entities, gateway_mac)
        out_file = Path(args.generate_yaml)
        if args.dry_run:
            _LOGGER.info("[DRY RUN] Generated YAML content would be written to %s (%d bytes)", out_file, len(yaml_content))
            print("\n" + yaml_content[:800] + "\n... [truncated] ...\n")
        else:
            out_file.write_text(yaml_content, encoding="utf-8")
            _LOGGER.info("Successfully generated MyHOME configuration at: %s", out_file.resolve())

    # 2. In-Place Entity Registry Migration Mode
    if args.migrate_registry:
        if args.dry_run:
            _LOGGER.info("[DRY RUN] Would migrate %d entities in %s to platform 'myhome'.", len(entities), registry_path)
        else:
            updated, backup = migrate_registry_in_place(registry_path, entities, gateway_mac)
            _LOGGER.info(
                "Successfully migrated %d entities in %s to platform 'myhome'!",
                updated,
                registry_path,
            )
            if backup:
                _LOGGER.info("Registry backup saved to: %s", backup)

    if not args.generate_yaml and not args.migrate_registry and not args.dry_run:
        print("To proceed with migration, use one of:")
        print("  --generate-yaml myhome.yaml      (Outputs pre-mapped configuration)")
        print("  --migrate-registry               (In-place seamless registry adoption)")
        print("  --dry-run                        (Simulate migration actions)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
