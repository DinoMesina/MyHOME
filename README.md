# MyHOME — OpenWebNet Integration for Home Assistant

[![Validate with hassfest](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/hassfest.yml/badge.svg)](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/hassfest.yml)
[![HACS Validation](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/validate.yml/badge.svg)](https://github.com/OpenWebNet-HA/MyHOME/actions/workflows/validate.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Integration for **BTicino / Legrand MyHOME** SCS bus systems connected via OpenWebNet IP gateways.

Now maintained by the **[OpenWebNet-HA](https://github.com/OpenWebNet-HA)** community organisation.

---

> [!IMPORTANT]
> ### 🛡️ Current Stable Status & Community Testing
>
> - **`master` Branch (Current Stable)**: This branch remains the **current stable release** for day-to-day production use.
> - **`v2-phase1-architecture` Branch (Testing & Modernization)**: A complete modernization and architectural overhaul is underway in **[PR #232](https://github.com/OpenWebNet-HA/MyHOME/pull/232)** and the [`v2-phase1-architecture`](https://github.com/OpenWebNet-HA/MyHOME/tree/v2-phase1-architecture) branch.
> - **Stability First**: To ensure zero disruption, the new architecture will remain in its dedicated branch until it has been thoroughly tested across diverse hardware gateways (`MH200`, `MH200N`, `MH202`, `F454`, `MyHomeServer1`, etc.) and proven completely reliable. Only once verified will it be merged into `master`.
>
> **👉 Help us test the new architecture:**
> 1. In HACS, redownload the MyHOME integration and select the **`v2-phase1-architecture`** branch (or grab it from [PR #232](https://github.com/OpenWebNet-HA/MyHOME/pull/232)).
> 2. Restart Home Assistant. All your existing entity IDs and friendly names are strictly preserved.
> 3. Share your feedback, gateway model, and test results in our community hub: **[Issue #229](https://github.com/OpenWebNet-HA/MyHOME/issues/229)** or directly on **[PR #232](https://github.com/OpenWebNet-HA/MyHOME/pull/232)**.

---

## 🚀 What's Coming in V2 (On Branch `v2-phase1-architecture`)

The upcoming v2 release includes:
- **Declarative Hardware Profiles**: Auto-detects and paces queues specifically for `MH200`, `MH200N`, `MH202`, `F454`, and `MyHomeServer1` to prevent buffer overflows and dropped commands.
- **Zero-Friction Upgrade**: Strictly preserves all existing entity IDs (`light.keuken`) and names (`MAC-WHERE` → `MAC-WHO-WHERE` migration).
- **Sound System 2.0 & Streaming Proxy**: Multi-room audio matrix (F441/F441M) with dynamic streaming from Music Assistant or Spotify Connect to wired BTicino zones.
- **Comprehensive Quality Standards**: 500+ unit tests, strict async stream lifecycles, and 100% green CI.

📖 [Read the full v2 architecture documentation and technical specs →](https://github.com/OpenWebNet-HA/MyHOME/tree/v2-phase1-architecture)

---

## 📦 Current Version Installation & Configuration

### Installation via HACS
1. Open **HACS** in Home Assistant.
2. Search for **MyHOME** (or add this repository as a Custom Repository if not yet listed).
3. Click **Download** and restart Home Assistant.

### Adding the Gateway
- Go to **Settings** → **Devices & Services** → **Add Integration** → **MyHOME**.
- The gateway IP address and port (default: `20000`) will be auto-discovered via UPnP/SSDP if supported, or can be entered manually.
- If your gateway requires OpenWebNet authentication, enter your 9-digit HMAC password.

### Device Configuration (Current Version)
In this current stable version on `master`, entity definitions and device options can also be configured via YAML.
Please refer to the [Project Wiki & Configuration Guide](https://github.com/anotherjulien/MyHOME/wiki/Configuration) for legacy entity syntax and examples.

---

## 👥 Organization & Community
This project has transitioned from the original repository by [@anotherjulien](https://github.com/anotherjulien) to the **[OpenWebNet-HA](https://github.com/OpenWebNet-HA)** community organisation.

- **Community Hub & Discussion**: [#229](https://github.com/OpenWebNet-HA/MyHOME/issues/229)
- **Phase 1 Pull Request & Testing**: [#232](https://github.com/OpenWebNet-HA/MyHOME/pull/232)
- **Roadmap & Feature Requests**: [Issue Tracker](https://github.com/OpenWebNet-HA/MyHOME/issues)
