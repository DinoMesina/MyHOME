# OpenWebNet Protocol & WHO Specifications Archive

Welcome to the **OpenWebNet Protocol & WHO Specifications Archive**. This document serves as the official open-access registry and cross-check inventory of all technical manuals, frame syntax, dimension definitions, and PDF specifications published by BTicino / Legrand for the OpenWebNet protocol across MyHOME systems.

Historically, these technical specifications were distributed through the *MyOpen Community* portal (`myopen-legrandgroup.com` / `myopen-bticino.it`), which is no longer active. To ensure that developers, installers, and community members have permanent access to accurate protocol documentation, we maintain this centralized registry.

An interactive version of this page is also hosted on our [GitHub Wiki](https://github.com/OpenWebNet-HA/MyHOME/wiki/OpenWebNet-Protocol-&-WHO-Specifications).

---

## 📋 Community Cross-Check: Call for BTicino Installers & Software Specialists

If you are a **certified BTicino / Legrand installer**, **system integrator**, or **MyHOME software specialist** (such as **@xtimmy86x**, **@lyubomirtraykov**, and fellow community professionals), your real-world experience across varied plant configurations and engineering software is invaluable.

We invite installers and software specialists to review and cross-check this archive:

### 🔍 What We Need Installers & Software Specialists to Review:

1. **Document Versions & Revision Dates**:
   - Compare your PDF archive against the [Master WHO Family Inventory](#-master-who-family-inventory) table below.
   - Look at the cover page and revision history (e.g. *Last date modify*, *Version number*). If your copy is newer than what is listed, please share the version details!

2. **Plant Topologies & Gateway Quirks**:
   - **Scenario Programmers (`MH200`, `MH200N`, `MH201`, `MH202`)**: Differences in session limits, memory banks, execution delays, and scenario frame syntax.
   - **Cross-Bus Interfaces (`F422`)**: Edge cases with interface addressing (`WHERE#4#INTERFACE`) on complex multi-riser installations.
   - **Next-Gen & Hybrid Gateways (`F454`, `F455`, `MyHomeServer1`, `F461`)**: Firmware variations, HMAC-SHA256 authentication behaviors, and SSDP UPnP discovery.

3. **Software Tooling & Official Specifications (MyHOME_Suite / TiMyHome)**:
   - Command definitions or exported XML dictionaries from Legrand/BTicino configuration software (**MyHOME_Suite**, **TiMyHome**, **Virtual Configurator**, **MyHOME_Up**).
   - Any technical addenda or documentation for:
     - **`WHO = 1` & `WHO = 24`**: DALI & DALI-2 gateway ballasts (tunable white, color temperature, RGB/RGBW, e.g. **F429G**).
     - **`WHO = 14`**: Actuator diagnostics, hardware lock/unlock states, and operating counters.
     - **`WHO = 18` & `WHO = 22`**: Multi-tariff smart metering, load shedding, and phase diagnostics.
     - **`WHO = 25`**: CEN+ extended scenario pushes and dry contact interfaces (**3477**).

> **💡 How to Contribute:** You can share filenames, revision dates, technical sheets, or bus monitor traces by opening an issue on the [OpenWebNet-HA/MyHOME GitHub repository](https://github.com/OpenWebNet-HA/MyHOME/issues) or commenting directly in [PR #232](https://github.com/OpenWebNet-HA/MyHOME/pull/232). Every contribution helps ensure open, permanent documentation for the entire MyHOME ecosystem.

---

## 📚 Master WHO Family Inventory

The table below catalogs every known OpenWebNet function family (`WHO`), its official Legrand document title, current known version, archive status, and Home Assistant platform mapping.

### Status Legend
- 🟢 **Archived & Verified**: Official PDF is preserved in our archive with full syntax verified.
- 🟡 **Legacy Copy Available / Cross-Check Needed**: Legacy documentation or reverse-engineered definitions exist; seeking confirmation of the latest official version.
- 🔴 **Needed / Missing**: Seeking the official Legrand/BTicino PDF specification.

| WHO | Subsystem / Function | Official Document Title / Filename | Known Version & Date | Status | Home Assistant Entity / Platform | Notes & Supported Hardware |
|:---:|:---|:---|:---:|:---:|:---|:---|
| **0** | **Scenarios (Basic)** | `OpenWebNet_Community_Scenarios` / `WHO_0.pdf` | v1.0.0 (2006) | 🟡 | `event`, automations | 32 standard scenarios (e.g. 3551 4-button module). |
| **1** | **Lighting (Illuminazione)** | `OpenWebNet_Community_1_Lighting` / `WHO_1.pdf` | v1.2.0 (2012) | 🟡 | `light` | ON, OFF, Dimming (1-100%, 10 levels, steps), Blink, Timer, Speed of transition. Extended lighting & DALI dimensions (tunable white / RGBW via F429/F429G). |
| **2** | **Automation (Automazione)** | `OpenWebNet_Community_2_Automation` / `WHO_2.pdf` | v1.0.0 (2006) | 🟡 | `cover` | Roller shutters, venetian blinds, motorized curtains, gates. Standard UP/DOWN/STOP and advanced absolute positioning percentage (0-100%, Legrand 67557). |
| **3** | **Load Control (Legacy)** | `OpenWebNet_Community_3_LoadControl` / `WHO_3.pdf` | v1.0.0 (2006) | 🟡 | `switch`, `sensor` | Priority-based load disconnection central unit (F421). Inhibit/force actuators. |
| **4** | **Thermoregulation (Termoregolazione)** | `OpenWebNet_Community_Heating` / `WHO_4.pdf` | v1.1.0 (2008) | 🟡 | `climate`, `sensor` | 4-zone / 99-zone central units (3550), standalone thermostats (L/N/NT4691), external probe sensors (3475), manual/auto/antifreeze/off/protection modes, heating/cooling season toggle. |
| **5** | **Burglar Alarm (Antifurto)** | `OpenWebNet_Community_BurglarAlarm` / `WHO_5.pdf` | v1.0.0 (2006) | 🟡 | `alarm_control_panel` | Central units (3485, 3486), partition arming/disarming, panic alarms, gas/water technical alarms, sensor zone status. |
| **6** | **Door Entry Call & Lock** | `OpenWebNet_Community_DoorEntry` / `WHO_6.pdf` | v1.0.0 (2006) | 🟡 | `lock`, `switch`, `event` | Audio door entry calls, door lock release (`*6*10*<WHERE>##`), staircase light, camera switching, incoming call chimes. |
| **7** | **Video Door Entry** | `OpenWebNet_Community_VideoDoorEntry` / `WHO_7.pdf` | v1.0.0 (2006) | 🟡 | `camera` | Video session establishment, camera selection, video stream routing over IP. |
| **9** | **Auxiliary (Comandi Ausiliari)** | `OpenWebNet_Community_Auxiliary` / `WHO_9.pdf` | v1.0.0 (2006) | 🟡 | `switch` | Auxiliary channels (AUX 1 to AUX 9) for triggering remote relays, annunciators, or inter-system signals without occupying lighting addresses. |
| **13** | **Gateway Management** | `OpenWebNet_Community_Gateway` / `WHO_13.pdf` | v1.0.0 (2006) | 🟡 | Core diagnostics | Date/time synchronization (`*#13**0*...`), firmware version query, IP configuration, MAC address, uptime, reboot command. |
| **14** | **Actuator Diagnostics** | `OpenWebNet_Community_Diagnostics` / `WHO_14.pdf` | Pending check | 🔴 | Core diagnostics / maintenance | Actuator operating state queries, hardware fault reports, locking/unlocking APL endpoints, operating hours counters. |
| **15** | **CEN Scenario Control** | `OpenWebNet_Community_CEN` / `WHO_15.pdf` | v1.0.0 (2006) | 🟡 | `event`, device triggers | Pushbutton scenario events: Press, Short Release, Extended Press (long push), Release after extended press. Scenarios 1-32, buttons 1-32 (3477, 3478, H4651, LN4652). |
| **16** | **Sound Distribution (Diffusione Sonora)** | `OpenWebNet_Community_4_soundsystem_v1_0_1_EN.doc` / `WHO_16.pdf` | **v1.0.1 (2011-11-24)** | 🟢 | `media_player` | Multi-room audio matrix control: Amplifier ON/OFF, volume control (step & %), audio input source selection (RDS tuner, RCA/aux, USB, Bluetooth), equalizer (bass, treble, balance), station presets, RDS text (F441, F441M, F450, 3487). |
| **17** | **Scenario Programmer** | `OpenWebNet_Community_ScenarioProgrammer` / `WHO_17.pdf` | v1.0.0 (2006) | 🟡 | `switch`, `event` | MH200 / MH200N / MH202 scenario programmer integration, enable/disable automated schedules, trigger macro executions. |
| **18** | **Energy Management** | `OpenWebNet_Community_Energy` / `WHO_18.pdf` | v1.0.0 (2008) | 🟡 | `sensor` | Electricity, water, and gas pulse meters. Instantaneous power (W), cumulative active energy (kWh), current (mA), voltage (V), power factor, tariff periods (F520, F521, F522, F523, 3522). |
| **22** | **Load Control (New Generation)** | `OpenWebNet_Community_LoadControlNew` / `WHO_22.pdf` | Pending check | 🔴 | `sensor`, `switch` | Modern smart load shedding central unit (F522/F523), dynamic threshold management, per-phase monitoring. |
| **24** | **Lighting Management & DALI** | `OpenWebNet_Community_LightingManagement` / `WHO_24.pdf` | Pending check | 🔴 | `light`, `sensor` | Advanced lighting control, DALI ballast addressing, lux sensors, daylight harvesting, multi-sensor motion/illuminance reporting (Legrand 048834, F429G). |
| **25** | **CEN+ Scenario Control & Dry Contacts** | `OpenWebNet_Community_CENPlus` / `WHO_25.pdf` | Pending check | 🟡 | `event`, `binary_sensor` | Extended CEN protocol with 256 buttons/scenarios, start/short/long press differentiation, dry contact interface telemetry (Legrand 3477 binary sensors, MH201). |
| **1000** | **Automation Group Commands** | Embedded in WHO 2 | — | 🟡 | `cover` | Area and General group broadcast commands for automation. |
| **1001** | **Lighting Group Commands** | Embedded in WHO 1 | — | 🟡 | `light` | Area and General group broadcast commands for lighting. |
| **1004** | **Temperature Group Commands** | Embedded in WHO 4 | — | 🟡 | `climate` | Zone group commands for thermoregulation. |

---

## 🔌 Gateway Architecture & Hardware Profiles

The table below outlines supported hardware gateways, transport layers, queue pacing requirements, and authentication mechanisms:

| Model | Hardware Type | Transport | Default Port | Auth Protocol | Queue Pacing | Features & Firmware Notes |
|:---|:---|:---|:---:|:---|:---:|:---|
| **MH200** | Scenario Programmer | TCP/IP | 20000 | Open password / None | 150 ms | Embedded ARM, scenario scheduler, legacy buffer limits. |
| **MH200N** | Scenario Programmer | TCP/IP | 20000 | Open password / None | 100 ms | Updated network interface, scenario engine. |
| **MH201** | Scenario Controller | TCP/IP | 20000 | Open password / None | 80 ms | High-performance DIN-rail scenario controller. |
| **MH202** | Scenario Programmer | TCP/IP | 20000 | Open password / None | 50 ms | High-speed ARM CPU, expanded memory and scenario memory. |
| **F452** | Web Server IP | TCP/IP | 20000 | Open password / None | 150 ms | Early generation IP gateway. |
| **F453AV** | Audio/Video Web Server | TCP/IP | 20000 | Open password / None | 120 ms | Supports door entry and basic web control. |
| **F454** | Web Server IP | TCP/IP | 20000 | Open numeric password | 80 ms | Dual bus interface, widely deployed standard DIN gateway. |
| **F455** | Advanced IP Gateway | TCP/IP | 20000 | Open numeric password | 50 ms | High-throughput industrial gateway. |
| **MyHomeServer1** | Modern IoT Gateway | TCP/IP | 20000 | **HMAC-SHA2 (SHA-256)** | 30 ms | Fast SoC, alphanumeric credentials, cloud integration bridge. |
| **F461** | Next-Gen DIN Server | TCP/IP | 20000 | Alphanumeric / HMAC | 20 ms | Latest generation BTicino DIN-rail server/gateway. |
| **Legrand 3578** | OpenZigBee USB Interface | Serial USB | `/dev/ttyUSB*` | None (Serial bypass) | 40 ms | 19200 baud, 8N1, ZigBee wireless SCS bridge (`#<unit_id>` addressing). |

---

## 🔍 OpenWebNet Frame Syntax Quick Reference

OpenWebNet messages always begin with `*` and end with `##`. Fields are separated by `*`:

1. **Standard Command / Status Message**:
   ```text
   *WHO*WHAT*WHERE##
   ```
   *Example*: `*1*1*21##` (Turn ON light at address A=2, PL=1)

2. **Dimension Request (Query)**:
   ```text
   *#WHO*WHERE*DIMENSION##
   ```
   *Example*: `*#4*1*0##` (Query measured temperature of Zone 1)

3. **Dimension Writing (Command with Parameters)**:
   ```text
   *#WHO*WHERE*#DIMENSION*VAL1*VAL2*...*VALn##
   ```
   *Example*: `*#16*1*#1*30##` (Set volume of audio Amplifier 1 to 30%)

4. **Dimension Response (Status Report)**:
   ```text
   *#WHO*WHERE*DIMENSION*VAL1*VAL2*...*VALn##
   ```
   *Example*: `*#4*1*0*0215*1##` (Zone 1 temperature is 21.5 °C, Heating mode)

5. **Acknowledge (ACK / NACK)**:
   - `*#*1##` : **ACK** (Command accepted by gateway/bus)
   - `*#*0##` : **NACK** (Command rejected, syntax error, or buffer busy)

---

## 🛠️ Testing & Live Bus Capture in Home Assistant

To capture raw OpenWebNet frames from physical hardware or diagnostic sessions:

1. Add the Lovelace Bus Monitor Card to your dashboard:
   ```yaml
   type: custom:myhome-bus-card
   ```
2. Operate your devices (e.g. adjust a DALI color ballast, toggle a dry contact switch, or change audio volume).
3. Click **`📋 Report Issue / Copy Trace`** to copy a sanitized diagnostics report with the exact bus frames.
