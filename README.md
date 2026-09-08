# MyHOME — OpenWebNet Integration for Home Assistant

[![Validate with hassfest](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/hassfest.yml/badge.svg)](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/hassfest.yml)
[![HACS Validation](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/validate.yml/badge.svg)](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/validate.yml)
[![test-coverage](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/test-coverage.yaml/badge.svg)](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/test-coverage.yaml)
[![Coverage](coverage.svg)](https://app.codecov.io/gh/OpenWebNet-HA/MyHOME/tree/v2-phase1-architecture)
[![Codecov](https://codecov.io/gh/OpenWebNet-HA/MyHOME/branch/v2-phase1-architecture/graph/badge.svg)](https://app.codecov.io/gh/OpenWebNet-HA/MyHOME/tree/v2-phase1-architecture)
[![PyPI Standards & Packaging](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/pypi_standards.yml/badge.svg)](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/pypi_standards.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Modern, async-native Home Assistant integration for **BTicino / Legrand MyHOME** SCS bus systems connected via OpenWebNet IP gateways.

Maintained by the **[OpenWebNet-HA](https://github.com/OpenWebNet-HA)** community organisation.

> [!TIP]
> **🧪 Community Testing Active**: The modernized Phase 1 architecture is currently undergoing community validation in **[PR #232](https://github.com/OpenWebNet-HA/MyHOME/pull/232)**. You can test it today via HACS by selecting the `v2-phase1-architecture` branch or following the testing instructions in [#229](https://github.com/OpenWebNet-HA/MyHOME/issues/229#issuecomment-5587215356)!

---

## 🌟 Key Features & Modern V2 Architecture

- **Declarative Hardware Profiles**: Auto-detects and tunes connection limits and queue pacing specifically for your gateway model (`MH200`, `MH200N`, `MH202`, `F454`, `F455`, `AM4890`, `MyHomeServer1`). Eliminates hardware session exhaustion and serial buffer overflows.
- **Zero-Friction Migration**: Upgrades preserve all existing custom entity IDs (`light.keuken`, `cover.living`) and friendly names. Unique IDs migrate transparently (`MAC-WHERE` → `MAC-WHO-WHERE`) with no broken dashboards or automations.
- **Token-Bucket Bus Pacing**: Hardened priority command queue with model-specific inter-frame delays (e.g. 150ms for legacy MH200 vs 20ms for F454) preventing command dropping during heavy automation bursts.
- **Dynamic Bus Auto-Discovery**: Automatically discovers entities from physical bus events and status sweeps without requiring manual `myhome.yaml` configuration. Full support for **F422 cross-bus routing** (e.g. `18#4#02`).
- **Sound System 2.0 & Audio Matrix (WHO=16)**: Complete multi-room audio support for F441 / F441M matrices and amplifiers, including zone power, volume normalization (0–31 scale), software mute emulation, and dynamic streaming proxy.
- **Streaming Audio Dynamic Proxy**: Seamlessly stream from **Music Assistant**, **Spotify Connect**, or any HA media player to wired BTicino audio zones using a thread-safe `DecoderPool` with analog gain-staging.
- **Dimmable Light Detection**: Auto-detects dimming capabilities directly from bus events with transition support.
- **Comprehensive Test Suite**: Over 500 automated unit tests (88%+ test coverage) executed across modern Python 3.12+ and Home Assistant core standards.

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

### Option 1: Via HACS (Recommended)

1. Open **HACS** in your Home Assistant UI.
2. Click the top-right menu (three dots) → **Custom repositories**.
3. Enter `https://github.com/OpenWebNet-HA/MyHOME`, select **Integration** as category, and click **Add**.
4. Search for `MyHOME` in HACS and click **Download**.
5. Restart Home Assistant.

### Option 2: Manual Installation

1. Download the latest release from the [Releases page](https://github.com/OpenWebNet-HA/MyHOME/releases).
2. Copy the `custom_components/myhome` directory into your Home Assistant `<config_dir>/custom_components/` folder.
3. Restart Home Assistant.

---

## ⚙️ Configuration

### Adding the Gateway

1. Navigate to **Settings → Devices & Services → Add Integration**.
2. Search for **MyHOME**.
3. **Auto-Discovery**: The integration will automatically discover UPnP/SSDP-compatible gateways on your local subnet (e.g. F454, MH202, MyHomeServer1).
4. **Manual Configuration**: If using a legacy gateway without UPnP (e.g. MH200):
   - Enter your gateway IP address and port (default `20000`).
   - Provide the gateway MAC address (found on the physical device sticker).
   - Enter your OpenWebNet password (default `12345`).
5. Select your gateway hardware profile from the dropdown if not auto-detected.

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
- **`test-coverage`**: 501 automated unit tests with snapshot matching and coverage tracking.
- **`pypi_standards`**: Strict wheel hygiene, metadata verification, and packaging checks.

### 📊 Code Coverage & Quality Assurance

The integration maintains over 500 automated tests covering core protocol handling, hardware profiles, discovery, state reconciliation, and error boundaries.

| Component / Module | Coverage | Notes |
|---|:---:|---|
| [`gateway_profile.py`](custom_components/myhome/gateway_profile.py) | **100%** | Hardware models (`MH200`, `F454`, etc.) and queue pacing limits |
| [`const.py`](custom_components/myhome/const.py) | **100%** | Protocol commands, dimensions, and integration constants |
| [`decoder_pool.py`](custom_components/myhome/decoder_pool.py) | **100%** | Thread-safe streaming proxy audio pool |
| [`myhome_device.py`](custom_components/myhome/myhome_device.py) | **100%** | Home Assistant device registry schema compliance |
| [`ownd/discovery.py`](custom_components/myhome/ownd/discovery.py) | **92%** | SSDP & UPnP gateway detection and descriptor parsing |
| [`ownd/message.py`](custom_components/myhome/ownd/message.py) | **91%** | OpenWebNet frame parsers, encoders, and dimension decoders |
| [`config_flow.py`](custom_components/myhome/config_flow.py) | **89%** | Step handlers, user entry, reauth, and options flow |
| [`button.py`](custom_components/myhome/button.py) | **87%** | Scenario buttons and bus diagnostic pings |
| [`binary_sensor.py`](custom_components/myhome/binary_sensor.py) | **86%** | Magnetic contacts, door/window sensors, motion sensors |
| [`cover.py`](custom_components/myhome/cover.py) | **86%** | Motorized shutters, blinds, roll-ups with state tracking |
| [`__init__.py`](custom_components/myhome/__init__.py) | **85%** | Setup lifecycle and zero-friction entity migration |
| [`gateway.py`](custom_components/myhome/gateway.py) | **82%** | Token-bucket pacing queue and event dispatching |
| [`switch.py`](custom_components/myhome/switch.py) | **81%** | Relay actuators, auxiliary switches, socket controllers |
| [`climate.py`](custom_components/myhome/climate.py) | **80%** | Heating, cooling, 4-pipe systems, and thermostat controls |
| [`ownd/connection.py`](custom_components/myhome/ownd/connection.py) | **68%** | Hardened TCP stream, fail-closed auth, watchdog loop |
| [`light.py`](custom_components/myhome/light.py) | **65%** | Relays, auto-dimmer detection, and brightness transitions |
| [`sensor.py`](custom_components/myhome/sensor.py) | **62%** | Power meters, energy counters, and pulse sensors |
| [`media_player.py`](custom_components/myhome/media_player.py) | **62%** | F441/F441M sound system zones, volume normalization |

> **Live Test Execution**: View the live code coverage dashboard directly on [**Codecov (v2-phase1-architecture)**](https://app.codecov.io/gh/OpenWebNet-HA/MyHOME/tree/v2-phase1-architecture) or download the interactive HTML report from the [**test-coverage GitHub Actions run**](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/test-coverage.yaml).

---

## 🗺️ Roadmap

- [x] **Phase 1: Architecture Decoupling & Modernization**
  - [x] Declarative hardware gateway profiles (`MH200` to `F454`).
  - [x] Zero-friction migration (preserving custom entity IDs and friendly names).
  - [x] Token-bucket bus pacing and sentinel worker lifecycle.
  - [x] Synthetic mock TCP test harness with 500+ unit tests (88%+ coverage).
  - [x] PyPI packaging pipeline & GitHub Actions CI green across all workflows.
- [ ] **Phase 2: Monitoring & Real-time Diagnostics**
  - [ ] In-band Unified Bus Listener (500-frame circular ring buffer, 0 extra sockets).
  - [ ] Native Home Assistant Diagnostics (`diagnostics.py`).
  - [ ] WebSocket streaming API & real-time Lovelace bus monitor card.
  - [ ] Stateless CEN/CEN+ scenario device triggers (`device_trigger.py`).

---

## 👥 Credits & Attribution

This integration is developed and maintained by the **[OpenWebNet-HA](https://github.com/OpenWebNet-HA)** community.

Special thanks to:
- **[@anotherjulien](https://github.com/anotherjulien)** for creating the original MyHOME integration and laying the protocol foundations.
- **[@GreenGrassBlueOcean](https://github.com/GreenGrassBlueOcean)** for the v2 modernized architecture, gateway profiles, streaming proxy, and test suite.
- **[@mantovanellimatteo](https://github.com/mantovanellimatteo)**, **[@fedem95](https://github.com/fedem95)**, **[@lyubomirtraykov](https://github.com/lyubomirtraykov)**, **[@Interstellar0verdrive](https://github.com/Interstellar0verdrive)**, and **Cedric Rohou** for key bugfixes, platform extensions, and community testing.
