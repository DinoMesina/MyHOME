# MyHOME — OpenWebNet Integration for Home Assistant

[![Validate with hassfest](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/hassfest.yml/badge.svg)](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/hassfest.yml)
[![HACS Validation](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/validate.yml/badge.svg)](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/validate.yml)
[![test-coverage](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/test-coverage.yaml/badge.svg)](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/test-coverage.yaml)
[![Coverage](coverage.svg)](https://app.codecov.io/gh/OpenWebNet-HA/MyHOME/tree/v2-phase1-architecture)
[![Codecov](https://codecov.io/gh/OpenWebNet-HA/MyHOME/branch/v2-phase1-architecture/graph/badge.svg)](https://app.codecov.io/gh/OpenWebNet-HA/MyHOME/tree/v2-phase1-architecture)
[![PyPI Standards & Packaging](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/pypi_standards.yml/badge.svg)](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/pypi_standards.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Latest Release](https://img.shields.io/github/v/release/OpenWebNet-HA/MyHOME?include_prereleases&label=release&logo=github)](https://github.com/OpenWebNet-HA/MyHOME/releases)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Wiki Docs](https://img.shields.io/badge/Wiki-OpenWebNet%20Docs-blue.svg)](https://github.com/OpenWebNet-HA/MyHOME/wiki/OpenWebNet-Protocol-&-WHO-Specifications)
[![Discussions](https://img.shields.io/badge/Discussions-Join-blue?logo=github)](https://github.com/OpenWebNet-HA/MyHOME/discussions)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Modern, async-native Home Assistant integration for **BTicino / Legrand MyHOME** SCS bus systems connected via OpenWebNet IP gateways.

Maintained by the **[OpenWebNet-HA](https://github.com/OpenWebNet-HA)** community organisation.

[📦 Installation](#-installation) • [🏛️ Supported Hardware](#️-supported-hardware) • [📚 Wiki Docs](https://github.com/OpenWebNet-HA/MyHOME/wiki) • [💬 Discussions](https://github.com/OpenWebNet-HA/MyHOME/discussions) • [🤝 Contributing](CONTRIBUTING.md) • [🔒 Security](SECURITY.md)

> [!TIP]
> **🧪 Community Testing Active**: The modernized architecture is currently undergoing community validation in **[PR #232](https://github.com/OpenWebNet-HA/MyHOME/pull/232)**. Because HACS does not index unmerged Git branches from its default store, please see the [Testing the V2 Architecture Branch](#testing-the-v2-architecture-branch-v2-phase1-architecture) guide below to install it in 2 minutes!

---

## 🌟 Key Features & Modern V2 Architecture

- **Declarative Hardware Profiles**: Auto-detects and tunes connection limits and queue pacing specifically for your gateway model (`MH200`, `MH200N`, `MH202`, `F454`, `F455`, `AM4890`, `MyHomeServer1`, and `Legrand 3578`). Eliminates hardware session exhaustion and buffer overflows.
- **USB / Serial Gateway & OpenZigBee Support**: Native asynchronous transport for the **Legrand 3578 USB/Serial interface** via `pyserial-asyncio` with dynamic port discovery, authentication bypass, and OpenZigBee addressing (`<8-digit id>#9`).
- **Zero-Friction Migration**: Upgrades preserve all existing custom entity IDs (`light.keuken`, `cover.living`) and friendly names. Unique IDs migrate transparently (`MAC-WHERE` → `MAC-WHO-WHERE`) with no broken dashboards or automations.
- **Token-Bucket Bus Pacing**: Hardened priority command queue with model-specific inter-frame delays (e.g. 150ms for legacy MH200 vs 20ms for F454) preventing command dropping during heavy automation bursts.
- **Dynamic Bus Auto-Discovery**: Automatically discovers entities from physical bus events and status sweeps without requiring manual `myhome.yaml` configuration. Full support for **F422 cross-bus routing** (e.g. `18#4#02`).
- **Sound System 2.0 & Audio Matrix (WHO=16)**: Complete multi-room audio support for F441 / F441M matrices and amplifiers, including zone power, volume normalization (0–31 scale), software mute emulation, and dynamic streaming proxy.
- **Streaming Audio Dynamic Proxy**: Seamlessly stream from **Music Assistant**, **Spotify Connect**, or any HA media player to wired BTicino audio zones using a thread-safe `DecoderPool` with analog gain-staging.
- **Dimmable Light Detection**: Auto-detects dimming capabilities directly from bus events with transition support.
- **Comprehensive Test Suite**: Over 700 automated unit tests (100% line coverage) executed across modern Python 3.12+ and Home Assistant core standards.

---

## 📚 Documentation & OpenWebNet Protocol Specifications (Wiki)

We now maintain a comprehensive, community-curated **[GitHub Wiki](https://github.com/OpenWebNet-HA/MyHOME/wiki/OpenWebNet-Protocol-&-WHO-Specifications)** documenting the OpenWebNet protocol, hardware profiles, and WHO subsystem specifications:

👉 **[OpenWebNet Protocol & WHO Specifications Wiki](https://github.com/OpenWebNet-HA/MyHOME/wiki/OpenWebNet-Protocol-&-WHO-Specifications)**

### Key Wiki Resources & Current Status
- **[WHO Specifications Archive & Status Matrix](https://github.com/OpenWebNet-HA/MyHOME/wiki/OpenWebNet-Protocol-&-WHO-Specifications#openwebnet-who-specifications-matrix)**: Complete catalog of all OpenWebNet WHO families (WHO 0 to WHO 1004) with official PDF documentation references, current implementation status, and frame syntax.
- **[Hardware Gateway Profiles](https://github.com/OpenWebNet-HA/MyHOME/wiki/Gateway-Profiles)**: Deep dive into connection constraints, socket limits, pacing delays, and watchdog behaviors for MH200, MH200N, MH202, F454, F455, MyHomeServer1, and Legrand 3578.
- **[Sound System 2.0 & Audio Matrix Guide](https://github.com/OpenWebNet-HA/MyHOME/wiki/Sound-System-2.0-&-Audio-Matrix)**: Setup instructions for F441/F441M matrices, room amplifier calibration, and Dynamic Proxy streaming.
- **[Bus Monitor Lovelace Card](https://github.com/OpenWebNet-HA/MyHOME/wiki/Bus-Monitor-Lovelace-Card)**: Bus card installation, live frame decoding, diagnostic logging, and syntax injector reference.
- **[Community Contribution Guide](https://github.com/OpenWebNet-HA/MyHOME/wiki/OpenWebNet-Protocol-&-WHO-Specifications#how-to-contribute-specifications)**: How to cross-check documentation versions and contribute missing WHO PDF specifications.

---

## 🏛️ Supported Hardware

### Gateway Profiles

| Gateway Model | Protocol Support | Max Command Workers | Inter-Frame Delay | UPnP Discovery | Notes |
|---|---|---|---|---|---|
| **F454** | OpenWebNet / HMAC | 4 workers | 20 ms | ✅ Port 49153 | Full high-speed multi-session support |
| **F455** | OpenWebNet / HMAC | 4 workers | 20 ms | ✅ Port 49153 | Dual-bus capable |
| **MH202** | OpenWebNet / HMAC | 3 workers | 30 ms | ✅ Port 49153 | Modern scenario programmer gateway |
| **MyHomeServer1** | OpenWebNet / HMAC | 4 workers | 20 ms | ✅ SSDP | Cloud/local hybrid gateway |
| **MH200N** | OpenWebNet | 2 workers | 80 ms | ❌ Manual | Second-generation scenario programmer |
| **MH200** *(Legacy)* | OpenWebNet | 1 worker | 150 ms | ❌ Manual | Strict single-session pacing; watchdog hardened |
| **AM4890** | OpenWebNet | 2 workers | 100 ms | ❌ Manual | Compact residential gateway |
| **Legrand 3578** | OpenWebNet (Serial) | 2 workers | 50 ms | ❌ Manual (Serial) | USB / Serial gateway & OpenZigBee interface |

### Supported Entity Domains

| Domain | WHO | Capabilities |
|---|---|---|
| **`light`** | WHO=1 | On/Off, Dimmers with brightness control & transitions |
| **`switch`** | WHO=1 | Relays, auxiliary switches, socket actuators |
| **`cover`** | WHO=2 | Motorized shutters, blinds, roll-ups with state tracking |
| **`climate`** | WHO=4 | Heating, cooling, 4-pipe systems, thermostats, setpoints |
| **`binary_sensor`**| WHO=25 | Magnetic contacts, door/window sensors, PIR motion |
| **`sensor`** | WHO=18 | Power meters, energy counters, voltage, pulse monitors |
| **`button`** | WHO=1 / 25 | Scenario buttons, lock/unlock triggers, bus ping |
| **`media_player`** | WHO=16 | F441/F441M audio zones, source tracking, volume, mute |

---

## 📦 Installation

### Testing the V2 Architecture Branch (`v2-phase1-architecture`)

While the V2 architecture is actively being validated in **[PR #232](https://github.com/OpenWebNet-HA/MyHOME/pull/232)**, HACS will not automatically display unmerged git branches or permit adding `OpenWebNet-HA/MyHOME` under *Custom repositories* (it will return `Repository 'openwebnet-ha/myhome' exists in the store`).

You can easily install and test the modernized branch right now using either method below:

#### Method A: Manual Installation (Recommended)

1. Download the branch archive:  
   👉 **[Download v2-phase1-architecture.zip](https://github.com/OpenWebNet-HA/MyHOME/archive/refs/heads/v2-phase1-architecture.zip)**
2. Unzip the archive on your computer.
3. Open your Home Assistant configuration directory (via **Samba Share**, **Studio Code Server**, or **File Editor** add-on).
4. Copy the `custom_components/myhome` directory into your Home Assistant `/config/custom_components/myhome/` folder (overwriting the existing files).
5. Clear your browser cache and restart Home Assistant (**Developer Tools → YAML → Restart**).

> [!NOTE]
> All existing entity names, custom entity IDs, and gateway configurations are preserved automatically.

#### Method B: One-Liner via Terminal & SSH Add-on

If you have the **Terminal & SSH** add-on enabled in Home Assistant, run this command:
```bash
cd /config/custom_components
wget https://github.com/OpenWebNet-HA/MyHOME/archive/refs/heads/v2-phase1-architecture.zip -O temp_myhome.zip
unzip -q temp_myhome.zip
rm -rf myhome
mv MyHOME-v2-phase1-architecture/custom_components/myhome ./
rm -rf MyHOME-v2-phase1-architecture temp_myhome.zip
```
Then restart Home Assistant (**Developer Tools → YAML → Restart**).

---

### Standard Installation (Stable Releases via HACS)

*(Available once PR #232 is merged into the main release channel)*

1. Open **HACS** in your Home Assistant UI.
2. Search for **MyHOME** in the Integrations tab.
3. Click **Download** and select the latest version.
4. Restart Home Assistant.

---

## ⚙️ Configuration

### Adding the Gateway

1. Navigate to **Settings → Devices & Services → Add Integration**.
2. Search for **MyHOME**.
3. Choose your gateway type:
   - **Network Gateway (TCP/IP)**:
     - **Auto-Discovery**: The integration automatically discovers UPnP/SSDP-compatible gateways on your local subnet (e.g. F454, MH202, MyHomeServer1).
     - **Manual IP Setup**: For gateways without UPnP (e.g. MH200), enter the gateway IP address, port (default `20000`), MAC address, and OpenWebNet password (default `12345`).
   - **USB / Serial Gateway (Legrand 3578 / OpenZigBee)**:
     - Select your physical serial device (e.g. `/dev/ttyUSB0` or `COM3`) from the dynamically populated port picker.
     - Select your baud rate (default `19200`).
     - Serial transport operates with zero authentication overhead (no IP password challenge needed) and natively routes OpenZigBee addresses (`<8-digit id>#9`).
4. Select or confirm your gateway hardware profile from the dropdown.

### Options Flow (Fine-Tuning)

Go to **Settings → Devices & Services → MyHOME → Configure** to customize:
- **Scan Interval**: Frequency of background state sync sweeps.
- **Command Queue Delay**: Override inter-frame delay if your gateway experiences packet loss.
- **Audio Decoders Pool**: Map network media players to physical matrix source inputs (see below).

---

## 🎵 Multi-Room Audio & Dynamic Proxy

The BTicino sound system matrix (F441 / F441M) is an analog matrix switch. It routes physical source inputs (IN 1–4) to amplified room zones.

This integration includes a **Dynamic Proxy** that lets you stream IP audio (via Music Assistant, Spotify Connect, AirPlay, etc.) directly to your wired BTicino zones.

### Hardware Routing Architecture

```
┌────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│     Media Source       │      │       DecoderPool       │      │      F441M Matrix       │
│  (Music Assistant /    │─────▶│  - claims idle decoder  │─────▶│   (Hardware Routing)    │
│   Spotify Connect)     │      │  - gain staging (clean) │      │                         │
│                        │      │  - activates zone (O/I) │      │   IN 1 ────▶ Living     │
└────────────────────────┘      └─────────────────────────┘      │   IN 2 ────▶ Kitchen    │
                                             ▲                   │   IN 3 ────▶ Bedroom    │
                                             │                   └─────────────────────────┘
                                  ┌──────────┴──────────┐                     ▲
                                  │   Network Decoders   │                     │
                                  │                      │                     │
                                  │  Decoder 1 (Wiim)    │────── RCA ──────────┘ (IN 1)
                                  │  Decoder 2 (HiFiDAC) │────── RCA ──────────┘ (IN 2)
                                  └──────────────────────┘
```

### Setting Up Streaming

1. Wire your network streamer (e.g. Raspberry Pi running squeezelite, WiiM, Cambridge Audio) to one of the matrix inputs (e.g. Source 1 or 2).
2. In Home Assistant, ensure the streamer is available as a `media_player` entity.
3. Open **MyHOME Options** (`Configure`), navigate to **Decoders**, and specify:
   - **Entity**: The streamer's `media_player` entity ID.
   - **Source**: The physical matrix input number (1–4) it is plugged into.
   - **Pre-Gain**: Analog offset percentage (recommended `15–20%` for line-level DACs, `0%` for fixed pre-amps).
4. Send audio from Music Assistant or Spotify to your BTicino zone entity:
   - The proxy automatically claims the decoder, wakes it, applies gain staging, and activates the zone.
   - When playback stops, the decoder is released back to the pool.

---

## 📡 Real-Time Bus Monitor & Diagnostics

The integration includes an in-band real-time bus monitor operating over the existing gateway event stream with zero extra socket connections:

### Lovelace Bus Monitor Card (`<myhome-bus-card>`)

A modern custom Lovelace element is automatically registered with zero configuration:

- **Live Bus Stream**: High-performance scrolling feed with color-coded badges for subsystems (Lighting `WHO=1`, Automation `WHO=2`, Climate `WHO=4`, Sound `WHO=16`, Energy `WHO=18`, CEN `WHO=15/25`) and ACK (`*#*1##`) / NACK (`*#*0##`) highlighting.
- **Interactive Controls**: Live Pause/Resume, buffer clearing, and instant filtering by subsystem, WHERE address, and Direction (RX/TX).
- **Manual Frame Injector**: Send raw OpenWebNet diagnostic frames directly to the bus with syntax validation.
- **One-Click Diagnostic Bug Reporter**: Click **"📋 Copy Diagnostic Report"** to copy a sanitized, GitHub-ready Markdown bundle containing:
  - Home Assistant Core & integration versions
  - Hardware gateway profile, firmware, connection type, queue pacing, and worker counts
  - Live buffer depth and RX/TX counters
  - Collapsible OpenWebNet bus trace (`<details><summary>OpenWebNet Bus Trace</summary>`)
  - Direct link opening pre-filled GitHub Issue Forms!

### 📝 Structured GitHub Issue Forms

When reporting issues or requesting new device support on GitHub, interactive forms ensure complete diagnostics:
- **Bug Report**: Gateway profile dropdown, connection type, HA version, diagnostics JSON attachment, and pre-formatted bus trace.
- **Device Support Request**: Structured form for adding new BTicino/Legrand modular components with WHO codes and frame samples.

---

## 🛠️ Development & Quality Standards

This project enforces strict code quality and packaging standards:

```bash
# Run the complete test suite
pytest tests/

# Run with coverage report
pytest --cov=custom_components.myhome --cov-report=term-missing tests/

# Validate PyPI packaging and PEP 517 compliance
python -m build
twine check --strict dist/*
check-wheel-contents dist/*.whl
```

### CI Workflows
- **`hassfest`**: Official Home Assistant manifest and metadata validation.
- **`validate`**: Official HACS compliance checks.
- **`test-coverage`**: 701 automated unit tests with snapshot matching and coverage tracking.
- **`pypi_standards`**: Strict wheel hygiene, metadata verification, and packaging checks.

### 📊 Code Coverage & Quality Assurance

The integration maintains 739 automated unit tests (100% line coverage across all modules) covering core protocol handling, hardware profiles, discovery, state reconciliation, and error boundaries.

<!-- START_COVERAGE_TABLE -->

| Component / Module | Coverage | Notes |
|---|:---:|---|
| [`__init__.py`](custom_components/myhome/__init__.py) | **100%** | Setup lifecycle and zero-friction entity migration |
| [`alarm_control_panel.py`](custom_components/myhome/alarm_control_panel.py) | **100%** | Core integration component |
| [`binary_sensor.py`](custom_components/myhome/binary_sensor.py) | **100%** | Magnetic contacts, door/window sensors, motion sensors |
| [`bus_monitor.py`](custom_components/myhome/bus_monitor.py) | **100%** | In-band 500-frame circular ring buffer tap (0 extra sockets) |
| [`button.py`](custom_components/myhome/button.py) | **100%** | Scenario buttons and bus diagnostic pings |
| [`climate.py`](custom_components/myhome/climate.py) | **100%** | Heating, cooling, 4-pipe systems, and thermostat controls |
| [`config_flow.py`](custom_components/myhome/config_flow.py) | **100%** | Step handlers, user entry, reauth, and options flow |
| [`const.py`](custom_components/myhome/const.py) | **100%** | Protocol commands, dimensions, and integration constants |
| [`core/transport/base.py`](custom_components/myhome/core/transport/base.py) | **100%** | Abstract transport layer defining OWN lifecycle contract |
| [`core/transport/serial.py`](custom_components/myhome/core/transport/serial.py) | **100%** | Async Serial/USB transport for Legrand 3578 / OpenZigBee |
| [`core/transport/tcp.py`](custom_components/myhome/core/transport/tcp.py) | **100%** | Modular TCP/IP socket transport with framed stream parsing |
| [`cover.py`](custom_components/myhome/cover.py) | **100%** | Motorized shutters, blinds, roll-ups with state tracking |
| [`decoder_pool.py`](custom_components/myhome/decoder_pool.py) | **100%** | Thread-safe streaming proxy audio pool |
| [`device_trigger.py`](custom_components/myhome/device_trigger.py) | **100%** | Stateless CEN/CEN+ scenario device automation triggers |
| [`diagnostics.py`](custom_components/myhome/diagnostics.py) | **100%** | Config entry diagnostics with sensitive data redaction |
| [`gateway.py`](custom_components/myhome/gateway.py) | **100%** | Hardware handler, lockout prevention, token-bucket queue |
| [`gateway_profile.py`](custom_components/myhome/gateway_profile.py) | **100%** | Hardware models (`MH200`, `F454`, etc.) and queue pacing limits |
| [`light.py`](custom_components/myhome/light.py) | **100%** | Relays, auto-dimmer detection, and brightness transitions |
| [`media_player.py`](custom_components/myhome/media_player.py) | **100%** | F441/F441M sound system zones, dynamic proxy, gain-staging |
| [`myhome_device.py`](custom_components/myhome/myhome_device.py) | **100%** | Home Assistant device registry schema compliance |
| [`ownd/connection.py`](custom_components/myhome/ownd/connection.py) | **100%** | Hardened TCP stream, fail-closed auth, watchdog loop |
| [`ownd/discovery.py`](custom_components/myhome/ownd/discovery.py) | **100%** | SSDP & UPnP gateway detection and descriptor parsing |
| [`ownd/message.py`](custom_components/myhome/ownd/message.py) | **100%** | OpenWebNet frame parsers, encoders, and dimension decoders |
| [`sensor.py`](custom_components/myhome/sensor.py) | **100%** | Power meters, energy counters, and pulse sensors |
| [`switch.py`](custom_components/myhome/switch.py) | **100%** | Relay actuators, auxiliary switches, socket controllers |
| [`validate.py`](custom_components/myhome/validate.py) | **100%** | Device & gateway schemas, custom WHERE validators, sensor injections |
| [`websocket.py`](custom_components/myhome/websocket.py) | **100%** | WebSocket API for real-time bus streaming, history, and diagnostics |

<!-- END_COVERAGE_TABLE -->

> **Live Test Execution**: View the live code coverage dashboard directly on [**Codecov (v2-phase1-architecture)**](https://app.codecov.io/gh/OpenWebNet-HA/MyHOME/tree/v2-phase1-architecture) or download the interactive HTML report from the [**test-coverage GitHub Actions run**](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/test-coverage.yaml).

---

## 🗺️ Roadmap

- [x] **Phase 1: Architecture Decoupling & Modernization**
  - [x] Declarative hardware gateway profiles (`MH200` to `F454`).
  - [x] Zero-friction migration (preserving custom entity IDs and friendly names).
  - [x] Token-bucket bus pacing and sentinel worker lifecycle.
  - [x] Synthetic mock TCP test harness with 701+ unit tests (100% coverage).
  - [x] PyPI packaging pipeline & GitHub Actions CI green across all workflows.
- [x] **Phase 2: Monitoring & Real-time Diagnostics**
  - [x] In-band Unified Bus Listener (500-frame circular ring buffer, 0 extra sockets).
  - [x] Native Home Assistant Diagnostics (`diagnostics.py`).
  - [x] WebSocket streaming API & real-time Lovelace bus monitor card.
  - [x] One-click diagnostic bundle & GitHub Issue Forms.
  - [x] USB / Serial Gateway support (Legrand 3578 / OpenZigBee).
  - [x] Stateless CEN/CEN+ scenario device triggers (`device_trigger.py`).

---

## 👥 Credits & Attribution

This integration is developed and maintained by the **[OpenWebNet-HA](https://github.com/OpenWebNet-HA)** community.

Special thanks to:
- **[@anotherjulien](https://github.com/anotherjulien)** for creating the original MyHOME integration and laying the protocol foundations.
- **[@GreenGrassBlueOcean](https://github.com/GreenGrassBlueOcean)** for the v2 modernized architecture, gateway profiles, streaming proxy, and test suite.
- **[@mantovanellimatteo](https://github.com/mantovanellimatteo)**, **[@fedem95](https://github.com/fedem95)**, **[@lyubomirtraykov](https://github.com/lyubomirtraykov)**, **[@Interstellar0verdrive](https://github.com/Interstellar0verdrive)**, and **Cedric Rohou** for key bugfixes, platform extensions, and community testing.
