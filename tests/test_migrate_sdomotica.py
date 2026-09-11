"""Unit tests for the SDomotica to MyHOME migration tool."""
import json

import pytest

from scripts.migrate_from_sdomotica import (
    SDomoticaEntity,
    extract_sdomotica_entities,
    find_entity_registry,
    find_gateway_mac_from_config,
    generate_myhome_yaml,
    main,
    migrate_registry_in_place,
)


@pytest.fixture
def mock_registry_data():
    """Return a mock core.entity_registry dictionary."""
    return {
        "version": 1,
        "minor_version": 1,
        "key": "core.entity_registry",
        "data": {
            "entities": [
                {
                    "area_id": "keuken",
                    "config_entry_id": "sdomotica_entry",
                    "device_id": "dev_1",
                    "entity_id": "light.sdomoticabticino2",
                    "name": "Keuken Spots",
                    "original_name": "sdomoticabticino2",
                    "platform": "mqtt",
                    "unique_id": "sdomotica_light_2",
                },
                {
                    "area_id": "keuken",
                    "config_entry_id": "sdomotica_entry",
                    "device_id": "dev_2",
                    "entity_id": "cover.sdomoticabticino68",
                    "name": "Gordijn Keuken Terras",
                    "original_name": "18#4#02",
                    "platform": "mqtt",
                    "unique_id": "sdomotica_cover_18_4_02",
                },
                {
                    "area_id": "cv_ruimte",
                    "config_entry_id": "sdomotica_entry",
                    "device_id": "dev_3",
                    "entity_id": "switch.sdomoticabticino62",
                    "name": "Pomp Schakelaar",
                    "original_name": "sdomoticabticino62",
                    "platform": "mqtt",
                    "unique_id": "sdomotica_switch_62",
                },
                {
                    "area_id": "keuken",
                    "config_entry_id": "sdomotica_entry",
                    "device_id": "dev_4",
                    "entity_id": "media_player.audio_zone_22",
                    "name": "Keuken Audio",
                    "original_name": "audio_zone_22",
                    "platform": "mqtt",
                    "unique_id": "sdomotica_zone_22",
                },
                {
                    "area_id": "woonkamer",
                    "config_entry_id": "hue_entry",
                    "device_id": "dev_5",
                    "entity_id": "light.hue_bloom",
                    "name": "Hue Bloom",
                    "original_name": "Hue Bloom",
                    "platform": "hue",
                    "unique_id": "hue_unique_123",
                },
            ]
        },
    }


def test_extract_sdomotica_entities(mock_registry_data):
    """Test extracting only SDomotica and audio zone entities."""
    entities = extract_sdomotica_entities(mock_registry_data)
    assert len(entities) == 4

    by_id = {e.entity_id: e for e in entities}
    assert "light.sdomoticabticino2" in by_id
    assert "cover.sdomoticabticino68" in by_id
    assert "switch.sdomoticabticino62" in by_id
    assert "media_player.audio_zone_22" in by_id
    assert "light.hue_bloom" not in by_id

    # Verify light properties
    light = by_id["light.sdomoticabticino2"]
    assert light.domain == "light"
    assert light.where == "2"
    assert light.who == "1"
    assert light.name == "Keuken Spots"
    assert light.area_id == "keuken"
    assert light.compute_myhome_unique_id("00:03:50:AA:BB:CC") == "00:03:50:aa:bb:cc-1-2"

    # Verify cover with interface
    cover = by_id["cover.sdomoticabticino68"]
    assert cover.domain == "cover"
    assert cover.who == "2"
    # Even if address in entity_id was 68, let's verify interface parsing if address has #4#
    cover_with_int = SDomoticaEntity(
        domain="cover",
        entity_id="cover.sdomoticabticino68",
        address="18#4#02",
        original_unique_id="sdomotica_cover_18",
        name="Gordijn Keuken Terras",
    )
    assert cover_with_int.where == "18"
    assert cover_with_int.interface == "02"
    assert cover_with_int.compute_myhome_unique_id("00:03:50:AA:BB:CC") == "00:03:50:aa:bb:cc-2-18#4#02"

    # Verify switch
    switch = by_id["switch.sdomoticabticino62"]
    assert switch.domain == "switch"
    assert switch.where == "62"
    assert switch.who == "1"
    assert switch.name == "Pomp Schakelaar"
    assert switch.area_id == "cv_ruimte"
    assert switch.compute_myhome_unique_id("00:03:50:AA:BB:CC") == "00:03:50:aa:bb:cc-1-62"

    # Verify audio zone
    audio = by_id["media_player.audio_zone_22"]
    assert audio.domain == "media_player"
    assert audio.address == "22"
    assert audio.who == "16"
    assert audio.compute_myhome_unique_id("00:03:50:AA:BB:CC") == "00:03:50:aa:bb:cc-16-22"


def test_generate_myhome_yaml(mock_registry_data):
    """Test generating myhome.yaml content."""
    entities = extract_sdomotica_entities(mock_registry_data)
    yaml_text = generate_myhome_yaml(entities, gateway_mac="00:03:50:11:22:33")

    assert 'mac: "00:03:50:11:22:33"' in yaml_text
    assert "sdomoticabticino2:" in yaml_text
    assert 'where: "2"' in yaml_text
    assert 'name: "Keuken Spots"' in yaml_text
    assert "sdomoticabticino62:" in yaml_text
    assert 'where: "62"' in yaml_text
    assert "sdomoticabticino68:" in yaml_text
    assert "audio_zone_22:" in yaml_text
    assert 'zone: "22"' in yaml_text


def test_migrate_registry_in_place(tmp_path, mock_registry_data):
    """Test in-place migration of core.entity_registry."""
    storage_dir = tmp_path / ".storage"
    storage_dir.mkdir()
    reg_file = storage_dir / "core.entity_registry"
    reg_file.write_text(json.dumps(mock_registry_data, indent=2), encoding="utf-8")

    entities = extract_sdomotica_entities(mock_registry_data)
    count, backup = migrate_registry_in_place(reg_file, entities, gateway_mac="00:03:50:99:88:77")

    assert count == 4
    assert backup is not None
    assert backup.is_file()

    # Read back updated registry
    updated_data = json.loads(reg_file.read_text(encoding="utf-8"))
    by_eid = {e["entity_id"]: e for e in updated_data["data"]["entities"]}

    # Migrated entities
    light_entry = by_eid["light.sdomoticabticino2"]
    assert light_entry["platform"] == "myhome"
    assert light_entry["unique_id"] == "00:03:50:99:88:77-1-2"
    assert light_entry["area_id"] == "keuken"

    switch_entry = by_eid["switch.sdomoticabticino62"]
    assert switch_entry["platform"] == "myhome"
    assert switch_entry["unique_id"] == "00:03:50:99:88:77-1-62"

    audio_entry = by_eid["media_player.audio_zone_22"]
    assert audio_entry["platform"] == "myhome"
    assert audio_entry["unique_id"] == "00:03:50:99:88:77-16-22"

    # Unmigrated entities untouched
    hue_entry = by_eid["light.hue_bloom"]
    assert hue_entry["platform"] == "hue"
    assert hue_entry["unique_id"] == "hue_unique_123"


def test_find_helpers(tmp_path):
    """Test helper functions find_entity_registry and find_gateway_mac."""
    # When file doesn't exist
    assert find_entity_registry(tmp_path) is None
    assert find_gateway_mac_from_config(tmp_path) is None

    # Setup files
    storage = tmp_path / ".storage"
    storage.mkdir()
    reg = storage / "core.entity_registry"
    reg.write_text("{}", encoding="utf-8")
    assert find_entity_registry(tmp_path) == reg

    # Test gateway MAC extraction
    cfg_entries = storage / "core.config_entries"
    cfg_entries.write_text(
        json.dumps(
            {
                "data": {
                    "entries": [
                        {
                            "domain": "myhome",
                            "data": {"mac": "00:03:50:12:34:56"},
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    assert find_gateway_mac_from_config(tmp_path) == "00:03:50:12:34:56"


def test_main_cli_modes(tmp_path, mock_registry_data):
    """Test CLI execution across all options."""
    storage_dir = tmp_path / ".storage"
    storage_dir.mkdir()
    reg_file = storage_dir / "core.entity_registry"
    reg_file.write_text(json.dumps(mock_registry_data), encoding="utf-8")

    yaml_out = tmp_path / "out_myhome.yaml"

    # 1. CLI with --generate-yaml
    ret = main(["--config-dir", str(tmp_path), "--generate-yaml", str(yaml_out)])
    assert ret == 0
    assert yaml_out.is_file()
    assert "sdomoticabticino2:" in yaml_out.read_text(encoding="utf-8")

    # 2. CLI with --dry-run
    ret = main(["--config-dir", str(tmp_path), "--dry-run", "--migrate-registry"])
    assert ret == 0

    # 3. CLI with invalid dir
    ret = main(["--config-dir", str(tmp_path / "nonexistent")])
    assert ret == 1
