# Migrating from SDomotica to Native MyHOME (OpenWebNet)

This guide provides a step-by-step, zero-touch migration path for users transitioning from the legacy **SDomotica** bridge to the native Home Assistant **MyHOME (OpenWebNet)** integration.

---

## 📌 Executive Summary

Many Legrand & BTicino MyHOME installations were previously integrated into Home Assistant via SDomotica (either through MQTT or custom bridge software). These installations follow standard legacy naming conventions:
- **Lights**: `light.sdomoticabticino0` through `light.sdomoticabticino60`
- **Covers**: `cover.sdomoticabticino68` through `cover.sdomoticabticino78`
- **Switches**: `switch.sdomoticabticino61`, `switch.sdomoticabticino62`
- **Audio Zones**: `media_player.audio_zone_14` through `media_player.audio_zone_36`

### Our Migration Guarantees
1. **Zero Dashboard Changes**: Your existing Lovelace cards, entity grids, auto-entities filters, and ApexCharts remain 100% operational.
2. **Zero Automation Changes**: Automations, scenes, and scripts referencing `light.sdomoticabticino*` continue working without renaming.
3. **Preserved History & Areas**: Historical database statistics, energy records, and room/area assignments are preserved.

---

## 🚀 Migration Options

You can migrate using either:
1. **The Automated Migration CLI Tool (`scripts/migrate_from_sdomotica.py`)** *(Recommended)*
2. **Direct `myhome.yaml` Configuration**

---

### Option 1: The Automated Migration CLI Tool (Recommended)

The MyHOME repository includes an automated migration utility located at `scripts/migrate_from_sdomotica.py`.

#### Step 1: Preview Entities (Dry Run)
Inspect your current Home Assistant installation to see all detected SDomotica entities:
```bash
python scripts/migrate_from_sdomotica.py --config-dir /config --dry-run
```
*Output summary:*
```
--- Discovered SDomotica Entities ---
  • cover          :  11 devices
  • light          :  62 devices
  • media_player   :   6 devices
  • switch         :   3 devices
-------------------------------------
```

#### Step 2: Choose Your Migration Mode

##### Mode A: Generate `myhome.yaml` (Safe Export)
If you want to keep your device list declared in YAML:
```bash
python scripts/migrate_from_sdomotica.py --config-dir /config --generate-yaml /config/myhome.yaml --gateway-mac 00:03:50:20:00:01
```
This automatically emits a complete `myhome.yaml` pre-keyed to your exact entity IDs:
```yaml
myhome:
  mac: "00:03:50:20:00:01"
  host: "192.168.1.50"
  port: 20000

  light:
    sdomoticabticino2:
      where: "2"
      name: "Keuken Spots"

  cover:
    sdomoticabticino68:
      where: "18"
      interface: "02"
      name: "Gordijn Keuken Terras"
      advanced: false

  switch:
    sdomoticabticino62:
      where: "62"
      name: "Pomp Schakelaar"

  media_player:
    audio_zone_22:
      zone: "22"
      name: "Keuken Audio"
```

##### Mode B: In-Place Entity Registry Migration (Zero-Touch)
To seamlessly transfer your entities directly inside Home Assistant's entity registry:
1. **Stop Home Assistant**:
   ```bash
   ha core stop
   ```
2. **Execute In-Place Registry Migration**:
   ```bash
   python scripts/migrate_from_sdomotica.py --config-dir /config --migrate-registry --gateway-mac 00:03:50:20:00:01
   ```
   *Note: A timestamped backup (`core.entity_registry.backup_sdomotica_<timestamp>`) is automatically created before any modification.*
3. **Start Home Assistant**:
   ```bash
   ha core start
   ```

When Home Assistant restarts, the native MyHOME integration connects to your gateway and binds directly to the existing entity registry records. **No `_2` suffixes, no broken dashboards, and no lost rooms.**

---

### Option 2: Address Translation Cheat Sheet

If manually configuring or adjusting devices, use this mapping table:

| SDomotica Format | MyHOME Configuration | Example | Description |
| :--- | :--- | :--- | :--- |
| **Point Light** (`A=0, PL=2`) | `where: "2"` | `sdomoticabticino2` | Standard SCS lighting actuator |
| **Area Broadcast** (`#WHERE`) | `where: "#1"` | `sdomoticabticino_area1` | Area master switch |
| **Bus Interface Cover** (`18#4#02`) | `where: "18"`, `interface: "02"` | `sdomoticabticino68` | Shutter via F422 interface |
| **Thermoregulation Zone** | `zone: "1"` | `climate.zone_1` | WHO 4 heating zone |
| **Audio Zone** | `zone: "22"` | `media_player.audio_zone_22` | WHO 16 multiroom sound zone |

---

## 🛡️ Post-Migration Verification Checklist

After restarting Home Assistant with MyHOME:
- [ ] Open **Developer Tools ➔ States** and search for `sdomoticabticino`. Verify all entities report their correct state (`on`, `off`, `open`, `closed`).
- [ ] Check your Lovelace dashboards (e.g. Active Lights, Covers grid). Ensure no cards show yellow *"Entity not found"* warnings.
- [ ] Test toggling a light and operating a cover to confirm bidirectional bus feedback.
- [ ] Check the **MyHOME OpenWebNet Bus Monitor** card (`custom:myhome-openwebnet-bus-monitor`) to verify live frame traffic.
