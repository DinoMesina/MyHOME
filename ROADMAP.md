# MyHOME for Home Assistant — Project Roadmap & Community Consultation

Welcome to the development roadmap and community consultation for the **MyHOME for Home Assistant** integration.

Our overarching mission is to provide the most reliable, complete, and high-performance integration between Home Assistant and the BTicino / Legrand SCS OpenWebNet ecosystem. We adhere to strict standards: **zero-latency asynchronous architecture**, **hardware-level protocol fidelity**, **100% automated test coverage**, and **full Home Assistant Core 2025/2026 compatibility**.

---

## 🗺️ Current Delivery Status (Unified Beta v2.0.0b11)

Through intense community collaboration and engineering, the major architectural milestones originally planned across Phases 1, 2, 3, and 4 have been **consolidated, fully implemented, and validated with 100% statement and branch test coverage** in the **v2.0.0b11 Unified Beta**.

```mermaid
gantt
    title MyHOME Integration Status & Roadmap
    dateFormat  YYYY-MM
    section Delivered in v2.0.0b11
    Phase 1: Dual Async Transports, Core Features & Bus Monitor    :done, 2026-08, 2026-09
    Phase 2: Standalone OWNd Library (P1) & CEN/CEN+ Triggers (P2)  :done, 2026-09, 2026-09
    Phase 2: Native DIN Bus Timers (WHO 1)                         :done, 2026-09, 2026-09
    Phase 3: Central Unit 3550/4695 (P4) & Multi-Gateway (P6)      :done, 2026-09, 2026-09
    Phase 4: Real-World Trace Replay CI Fixture Engine (P5)        :done, 2026-09, 2026-09
    DALI Tunable White & Color Temperature (Dim 14)                :done, 2026-09, 2026-09
    WHO 18 Energy Power/Meters & WHO 16 Audio Matrix Proxy         :done, 2026-09, 2026-09
    section Active Community Consultation
    RFC: P7 Group Sync, P3 Cover Calibration, WHO 14/24/22 Scope   :active, 2026-09, 2026-11
```

---

## 📦 What is Shipped & Operational in v2.0.0b11

The following table summarizes the completed architectural features and protocol subsystems verified in the current release:

| Priority / Feature | Subsystem | Implementation Status | Highlights |
|---|---|---|---|
| **Standalone Protocol Engine (P1)** | Core | ✅ **Shipped** (`OWNd 2.0.0b5`) | Extracted into an independent, strongly typed Python library on PyPI; shared with CLI tools and MCP servers. |
| **CEN / CEN+ UI Device Triggers (P2)** | WHO=15 / 25 | ✅ **Shipped** | First-class Home Assistant UI device triggers with string-preserved addressing (`"0001"`), gateway MAC isolation, and all 8 press/held/release actions. |
| **Native Hardware Bus Timers** | WHO=1 | ✅ **Shipped** | Offloaded countdown timers on Legrand DIN actuators (F411) via `myhome.turn_on_timed` or `timer`/`duration` parameters in `light.turn_on` / `switch.turn_on`. |
| **Central Unit Coordination (P4)** | WHO=4 | ✅ **Shipped** | Dedicated master coordination for 99-zone Central Unit (`#0`, model 3550) and 4-zone Central Unit (`#0#1`, model 4695). Master Seasonal switches propagate to subordinate zones. |
| **Multi-Gateway Isolation (P6)** | Core / Dispatcher | ✅ **Shipped** | Namespaced event dispatchers (`f"myhome_cen_event_{mac}"`) and device trigger filtering by parent gateway MAC (`via_device`), eliminating cross-talk across multi-gateway plants. |
| **Real-World CI Trace Replay (P5)** | Testing / CI | ✅ **Shipped** | Automated pytest fixture engine (`tests/test_trace_replay.py`) replaying frozen on-wire bus captures (e.g. Nicola Cavallo's 100-frame trace from F454) directly against HA state machines. |
| **DALI Tunable White & Dimmers** | WHO=1 | ✅ **Shipped** | DALI DT8 tunable white (Kelvin 2000K–6535K / mireds, Dimension 14), HSV color auto-promotion (Dimension 12), and dimming speed curves. |
| **Fancoil Thermoregulation** | WHO=4 | ✅ **Shipped** | 3-speed fancoil control (`auto`, `low`, `medium`, `high`) using dimension 11, temperature offset tracking, and startup sweeps. |
| **Sound System 2.0 & Streaming Proxy**| WHO=16 | ✅ **Shipped** | Multi-room matrix amplifier control (F441/F441M), volume normalization (0–31 scale), software mute, and Dynamic Streaming Proxy for Music Assistant / Spotify. |
| **Energy Management & Metering** | WHO=18 | ✅ **Shipped** | Instantaneous power (W), line voltage (V), current (mA), and energy counters wired into Home Assistant energy sensors. |
| **Burglar Alarm** | WHO=5 | ✅ **Shipped** | Partitions, arm away/home, disarm, panic trigger, and zone 0 synchronization for central units (3485/3486). |
| **Dry Contacts & Technical Alarms** | WHO=25 | ✅ **Shipped** | Dynamic discovery, inverted contact states, and event dispatching for Legrand 3477 binary sensors. |
| **Lovelace Bus Monitor Card** | Frontend | ✅ **Shipped** (`<myhome-bus-card>`) | Live scrolling stream, color-coded WHO badges, syntax injector, and 1-click **"📋 Report Issue / Copy Trace"** clipboard exporter. |

---

## 🗳️ Community RFC: How Should We Deal With the Last Remaining Items?

With the foundational architecture and primary subsystems delivered, only a small set of specialized protocol capabilities remains from the original RFC #248 gap analysis. 

We invite community members, certified installers, and power users to review the options below and share their input in [**RFC Discussion #248**](https://github.com/orgs/OpenWebNet-HA/discussions/248):

---

### 1. 💡 P7: Lighting Groups & General Sync (`WHO = 1`)

#### The Technical Context:
In OpenWebNet, lighting actuators can be triggered individually (`WHERE=10`), by group (`WHERE=#1` through `#255`), by environment/room (`WHERE=room`), or generally across the whole plant (`WHERE=0`). 
In ideal installations, actuators broadcast individual status frames (`*1*0*10##`, `*1*0*11##`) after executing a group or general command. However, on older gateways or specific actuator configurations, actuators do **not** emit individual status messages, leaving Home Assistant entities out of sync with the physical lights.

#### Open Questions for the Community:
1. **Group Mapping Definition**: Should group memberships be defined in `myhome.yaml` / UI Options (e.g. `groups: { 1: ["light.kitchen", "light.dining"] }`), or should Home Assistant trigger an asynchronous status sweep (`*#1*WHERE##`) whenever a group actuation is intercepted on the bus?
2. **Priority**: For your installation, do you actively use physical MyHOME group/general buttons, and are your entity states desynchronizing today?

---

### 2. 🪟 P3: Cover Calibration & Dynamic Hardware Position Promotion (`WHO = 2`)

#### The Technical Context:
Home Assistant currently provides **virtual travel-time positioning** for all covers (calculating percentage open/closed based on configured travel duration). 
Legrand advanced shutter actuators (such as the 67557, LN4672M2, and F401) support native hardware positioning via Dimension 10 (`*#2*WHERE*10*Position*...##`) and an automatic travel calibration routine (`shutterRun=AUTO`).

#### Open Questions for the Community:
1. **Calibration Service**: Would a `myhome.calibrate_cover` service (triggering physical calibration on the actuator) be valuable, or is manual travel-time estimation sufficient and safer?
2. **Auto-Promotion**: Should covers that report Dimension 10 frames automatically promote themselves to hardware positioning mode without user intervention?

---

### 3. 🔒 WHO 14: Actuator Maintenance Locks & Relay Cycle Counters

#### The Technical Context:
OpenWebNet WHO 14 handles actuator diagnostics, relay cycle counters, and hardware maintenance locks (preventing physical buttons from toggling a relay during maintenance or security states). 
Legrand does not publish an open specification for WHO 14; frames are largely proprietary diagnostic codes from DIN actuators.

#### Open Questions for the Community:
1. **Use Case**: Does anyone in the community have a practical automation use case for software maintenance lock switches on Legrand DIN actuators, or does this add unnecessary entity clutter?
2. **Recommendation**: Should WHO 14 remain an internal diagnostic listener (visible in the Bus Monitor card) rather than exposing Home Assistant lock entities?

---

### 4. 🏢 WHO 24: Legrand Commercial Lighting Management Room Controllers

#### The Technical Context:
WHO 24 is designed for commercial Legrand Lighting Management controllers (**BMNE500**, **BMview**, **002645**) used in office buildings and schools. It regulates maintained lux levels, daylight harvesting, and profile activation (`*24*1#Profile*WHERE##`). 
Residential MyHOME plants almost universally use standard WHO=1 lighting and DALI gateways (F429).

#### Open Questions for the Community:
1. **User Base**: Is anyone in the community running commercial BMNE500 / WHO 24 lighting controllers in their installation?
2. **Recommendation**: Should WHO 24 be deferred to an optional extension rather than core residential integration scope?

---

### 5. 🎵 WHO 22: Legacy Multi-Room FM Tuner & RDS Navigation

#### The Technical Context:
WHO 22 defines protocol frames for obsolete Legrand analog FM radio tuner modules (frequency stepping, station presets, and RDS text streaming). 
Modern installations stream digital music from **Music Assistant**, **Spotify Connect**, or AirPlay directly into BTicino audio zones via the **Dynamic Proxy** pattern on the F441 matrix.

#### Open Questions for the Community:
1. **Deprecation**: Should WHO 22 FM tuner controls be formally deprecated in favor of our active F441 Dynamic Streaming Proxy?

---

## 💬 How to Participate

Please share your feedback, real-world bus captures, and advice in our GitHub discussions:

👉 **[Join the Community Discussion on RFC #248](https://github.com/orgs/OpenWebNet-HA/discussions/248)**  
👉 **[Report Beta Issues or Submit Bus Traces](https://github.com/OpenWebNet-HA/MyHOME/issues)**
