# MyHOME
Modernized MyHOME Custom Component for Home Assistant

[![test-coverage](https://github.com/GreenGrassBlueOcean/MyHOME/actions/workflows/test-coverage.yaml/badge.svg)](https://github.com/GreenGrassBlueOcean/MyHOME/actions/workflows/test-coverage.yaml)
[![codecov](https://codecov.io/gh/GreenGrassBlueOcean/MyHOME/graph/badge.svg)](https://codecov.io/gh/GreenGrassBlueOcean/MyHOME)

*This is a completely modernized, async-native fork of the original integration, specifically hardened for legacy MH200 hardware and modern Home Assistant (2025+).*

## 🌟 Modernization Features

1. **Fully Dynamic Auto-Discovery (No more YAML!):**
   The integration has been completely disentangled from file-system based `myhome.yaml` static configurations. Devices are now registered and configured natively through the Home Assistant UI Device Registry. The integration actively queries the OpenWebNet bus to discover all entities out of the box. Native support for complex **F422 Cross-Bus Routing** (e.g. addresses like `18#4#02`) is also completely handled automatically!
   
2. **Native Audio System Support (WHO=16):**
   Full native support for Bticino/MyHome Audio Matrices, compatible with both legacy baseband and **Sound System 2.0 stereo** hardware. Exposes native `media_player` entities for all audio zones with bidirectional state tracking.
   - **Turn On/Off, Source Selection & Volume:** Full support for `turn_on`, `turn_off`, `select_source`, `volume_set`, `volume_up`, and `volume_down`. Source selection on the zone entities reports the current matrix routing (observed from the bus). Changing the active source from HA is a no-op to avoid hiss (see F441M section below).
   - **Absolute Volume Tracking:** Full support for dimension messages (`*#16*where*#1*vol##`), normalizing the 0–31 hardware scale automatically.
   - **Software Mute Emulation:** Since OpenWebNet lacks a native audio Mute function, this integration fully emulates local muting, keeping physical volume levels accurately cached.

3. **🎵 Dynamic Proxy — Stream Music to Your BTicino Zones:**
   The BTicino audio matrix (F441, S0105A) is a **hardware-only analog switch** — it cannot decode IP-based audio streams on its own. This integration bridges that gap with a *Dynamic Proxy* that lets you stream from **Music Assistant**, **Spotify Connect**, or any HA-compatible media source to your wired BTicino zones.

   **How it works (automatically) — Hardware Routing First:**
   1. You configure one or more *decoders* (network media players physically connected to the matrix source inputs) via the Options UI. You tell the integration which physical source input (1–4) each decoder is wired to.
   2. When Music Assistant or Spotify sends `play_media` to a BTicino zone, the proxy claims an idle decoder, wakes it, and activates the zone with a simple OFF → ON command. It does **not** send matrix source-routing commands (they cause hiss). Routing is expected to already be correct because of physical wall panel selection or a power-on scenario.
   3. Playback state (title, artist, album art) is mirrored back from the decoder to the zone entity in real time.
   4. When the zone is turned off, the decoder is released back to the pool for other zones.

   **Compatible decoders:**
   Any HA-integrated `media_player` entity with network streaming capability:
   - **squeezelite / piCorePlayer** — Free, runs on any Raspberry Pi with a DAC HAT (e.g. HiFiBerry DAC+). Discovered automatically by Music Assistant.
   - **Cambridge Audio** (CXN, etc.) — High-end network streamer with HA integration. Works with `internet_radio` content type since HA 2024.11.
   - **WiiM Mini / Pro** — Budget-friendly network streamer with AirPlay and HA support.
   - Any DLNA, Chromecast, or AirPlay-capable device exposed as a `media_player` in HA.

   **Key features:**
   | Feature | Description |
   |---|---|
   | Thread-safe pool | `asyncio.Lock`-protected `DecoderPool` prevents race conditions when multiple zones compete for the same decoder |
   | Up to 4 simultaneous streams | One decoder per physical source input (F441 has 4 inputs) |
   | Gain staging (anti-hiss) | Per-decoder `pre_gain` offset keeps the analog signal level high and the amplifier gain low, reducing bus noise |
   | Backward compatible | If no decoders are configured, the entity behaves exactly as before — `PLAY_MEDIA` is not advertised |
   | Auto-reload | Changing decoder config in Options UI rebuilds the pool without restarting HA |

4. **Auto-Detect Dimmable Lights:**
   Dimmers are automatically recognized from the OpenWebNet protocol. When the gateway sends a brightness level or brightness preset event, the light entity is promoted from simple on/off to full brightness control with transition support. No manual configuration needed — the integration learns from the bus traffic. A `customize.yaml` fallback is still supported for manual overrides.

5. **Smart Gateway Configuration:**
   The custom setup flow first attempts to auto-discover the gateway's MAC address and model by fetching the UPnP device descriptor directly from known BTicino ports (`http://<IP>:49153/description.xml`). If the gateway does not support UPnP (e.g., older MH200 models), a manual fallback step is presented instead. This eliminates the need to manually look up the MAC address for most modern gateways (F454, MH202, MH201).

6. **MH200 & Stability Hardening:**
   Resolved the fatal "Listener Death" bugs prevalent in the original library. 
   - Strict 120-second active watchdogs drop permanently hung TCP sockets efficiently.
   - Exponential Backoff routines (`2s -> 60s`) guard against embedded gateway DDoS on power restoration.
   - Polling queries (`SCAN_INTERVAL`) drastically reduced by default for passive sensors.
   - Native integration caching (`ConfigEntryNotReady`) entirely eliminates the infamous "Restart required on first installation" crash loop.

7. **Robust Entity Migration & Registry Integrity:**
   The integration includes self-healing logic for entity IDs. On startup, it automatically detects and corrects orphaned or mis-named entities from previous installations, reverting entity IDs back to the standard `light.light_XX` / `cover.cover_XX` format. Legacy `customize.yaml` friendly names are transparently absorbed and applied without requiring any manual re-configuration.

## ⚙️ Installation & Configuration

### 1. Install via HACS (Recommended)
You can install this integration as a Custom Repository via HACS!
1. Go to HACS -> Integrations -> Click the three dots (top right) -> Custom repositories
2. Add this repository URL and select `Integration` as the category.
3. Restart Home Assistant.

### 2. Add the Integration in Home Assistant
**Important:** Do *not* use `configuration.yaml` for this integration. The legacy `myhome.yaml` approach has been completely disabled in favor of modern UI-driven architecture.

1. Go to **Settings -> Devices & Services -> Add Integration**.
2. Search for `MyHOME`.
3. The component will automatically search your local network via SSDP for compatible BTicino gateways (e.g., MH200, F454, MyHomeServer1).
4. If no gateways are found automatically, select "Custom" and enter your gateway's IP address and port. The integration will try to auto-detect the MAC address and model via UPnP. If that fails (e.g., on legacy MH200 gateways), a manual entry form is presented.
5. Enter your gateway's OpenWebNet password when prompted.

### 3. Entity Naming & Discovery
Once connected, the integration strictly uses **Auto-Discovery** to find your Lights, Switches, Covers, and Audio Zones.
Simply use your physical wall switches to interact with your house. Home Assistant will capture the physical bus events, dynamically generate the devices in your dashboard (naming them by their hardware address, e.g., `Light 18`, `Cover 18#4#02`), and store them permanently!

To assign human-readable names (like "Kitchen Lights"):
*   **The Modern Way:** Click on the generated Entity in the Home Assistant UI (`Settings -> Devices`), click the gear icon, and rename it natively.
*   **The Power-User Way:** Use Home Assistant's native [customize.yaml](https://www.home-assistant.io/docs/configuration/customizing-devices/) feature to bulk-rename entities without touching the underlying integration logic.

### 4. Audio Zone Controls
Audio zones are automatically discovered as `media_player` entities when any sound system traffic is detected on the bus.

**Source selection philosophy ("Hardware Routing First")**:  
Source changes are best performed with physical wall panels or a gateway power-on scenario. The integration does not send matrix routing commands over IP (they cause hiss on MH200 gateways). When streaming via the Dynamic Proxy, the software only activates the zone (OFF → ON) and trusts that the matrix is already routed to the correct physical decoder input.

The supported features include:

| Feature | Method |
|---|---|
| Turn On/Off | Standard HA media player controls |
| Volume Up/Down | Step-based volume adjustment |
| Volume Slider | Absolute volume set (0–31 → normalized 0.0–1.0) |
| Source Selection | Physical wall panels (recommended) or gateway power-on scenario |
| Mute | Software-emulated (caches volume, sets to 0, restores on unmute) |

#### F441M Source Routing Architecture ("Hardware Routing First")

> **Important:** The original MH200 gateway (firmware ≤ 2.1.0) **cannot** switch F441M matrix sources hiss-free via IP. All WHO=16 compound routing commands (`*16*3*1XY##`) sent through the IP gateway produce audible analog relay transients. Native wall-panel commands on the bus do not have this problem. The MH200 also does not support CEN/CEN+ virtual triggering over IP.

**Recommended model — Hardware Routing First**

1. Physically connect your network streaming decoder(s) to the source input(s) you want to use (any of Source 1–4).
2. Use physical BTicino wall panels to select that source for the zones you care about. This is clean and hiss-free.
3. (Optional) Program a gateway power-on / startup scenario so zones default to your streaming source(s) after power loss.
4. The integration only sends simple zone ON/OFF commands. It trusts the matrix routing that was set physically or by the scenario. No source-routing commands are ever sent from Home Assistant.

This approach lets you put streaming on **Source 1** (or any source) and have wall panels natively select it without involving the gateway for routing.

The `async_select_source()` method is intentionally a **no-op**. Changing sources from the Home Assistant UI is not supported for hiss-avoidance reasons.

##### Optional: Using a Gateway Power-On Scenario (Legacy / Fixed Routing)

If you prefer all zones to come up already routed to a specific source (e.g. your streaming input), you can still use a power-on scenario. The technique is the same regardless of which source number you chose physically:

1. Open **Configurator TiMH200** (Windows XP SP3 compatibility mode, Run as Administrator).
2. Create a new **Scenario** of type **"All'accensione"** (Power-On / Startup).
3. For each amplifier zone, add a sound system action:
   - **Action:** Stereo ON (`WHAT=3`)
   - **Address:** Compound `1<source><zone_digit>` (e.g. `111` = Source 1, Zone 1)

Example compound addresses (replace the source digit with the one you physically wired your decoder to):

   | Amplifier Zone | Zone Digit | Example for Source 1 | Example for Source 2 |
   |---|---|---|---|
   | 14 | 4 | `*16*3*114##` | `*16*3*124##` |
   | 21 (Bureau) | 1 | `*16*3*111##` | `*16*3*121##` |
   | ... | ... | ... | ... |

5. Upload via Serial (COM1) to the MH200.

> **TiMH200 Upload Bug:** On Windows 10/11, right-click `TiMH200.exe` → Properties → Compatibility → **Windows XP (Service Pack 3)** + **Run as Administrator**.

The old practice of permanently forcing everything to "Source 2 = Aux" is no longer required. Choose whichever source number is most convenient for your physical wiring.

##### Upgrading the Gateway
To restore full IP-based source switching (hiss-free CEN+ triggering), upgrade to an **MH200N**, **F454**, or **F459** gateway. These support `WHO=25` CEN+ virtual triggering over IP with proper SCS frame generation.

For **manual OWN commands** (e.g., via the `myhome.send_message` service), refer to the OpenWebNet specification for WHO=16.

### 5. Setting Up Streaming (Dynamic Proxy)

To stream from Music Assistant, Spotify Connect, or other services to your BTicino audio zones, you need at least one **decoder** — a network media player physically connected to one of the matrix source inputs via RCA or 3.5mm.

#### Prerequisites
- A BTicino audio matrix (F441, S0105A, or similar) with at least one free source input
- A network-capable media player wired to that input, integrated into Home Assistant as a `media_player` entity

#### Configuration
1. Go to **Settings → Devices & Services → MyHOME → Configure**.
2. Scroll to the **Decoder** section.
3. For each connected decoder, fill in:
   - **Entity:** The `media_player` entity ID of the decoder (e.g. `media_player.cambridge_audio_cxn`)
   - **Source:** The BTicino source input number (1–4) the decoder is **physically wired to** on the F441M matrix. This is critical — the integration uses this number when claiming the decoder for a zone.
   - **Pre-gain:** A volume offset percentage (0–50) to optimise the analog signal-to-noise ratio. Recommended values:
     - `0` for decoders with fixed line-level output (e.g. Cambridge Audio with Pre-Amp OFF)
     - `15–20` for software-level decoders (e.g. squeezelite on a HiFiBerry DAC)
     - Higher values for particularly noisy setups — start at `30` and reduce if the decoder clips

4. Click **Submit**. The decoder pool is rebuilt immediately without restarting HA.

**Tip:** With the "Hardware Routing First" model you can wire your main streaming decoder to Source 1 (or any convenient input) and let wall panels select it directly. The software does not need to know or enforce a specific source number for routing — it only needs to know which physical input each decoder is attached to.

#### Gain staging explained
The BTicino 2-wire bus introduces inherent analog noise. The `pre_gain` setting drives the decoder volume proportionally higher than the zone volume (`decoder_vol = zone_vol + pre_gain/100`, capped at 1.0), keeping the analog signal level high while reducing the amplifier's noise floor amplification. The result is cleaner audio at lower listening volumes.

### Advanced Usage & Protocol Handling

The underlying OpenWebNet (`OWNd`) package has been exclusively vendored natively into this component (`custom_components/myhome/ownd`), allowing complete downstream control over exact OpenWebNet protocol implementations to maximize reliability.

#### Supported Hardware
| Gateway | UPnP Auto-Discovery | Notes |
|---|---|---|
| F454 | ✅ | Full UPnP support (port 49153) |
| MH202 / MH201 | ✅ | Full UPnP support |
| MH200 | ❌ | Manual MAC entry required; no UPnP descriptor |
| MyHomeServer1 | ✅ | Should work via SSDP |

| Audio Matrix | Decoder Support | Source Inputs |
|---|---|---|
| F441 / F441M | ✅ | 4 stereo inputs |
| S0105A | ✅ | 4 stereo inputs |
| E46ADCN (amplifier) | ✅ | Receives from matrix |

#### Architecture: Dynamic Proxy (Hardware Routing First)

```
┌──────────────────┐     ┌───────────────┐     ┌──────────────────┐
│  Music Assistant  │     │  DecoderPool  │     │   F441M Matrix   │
│  / Spotify / MA   │────▶│  (asyncio)    │────▶│   (hardware)     │
│                   │     │               │     │                  │
│  play_media()     │     │  claim()      │     │  (routing already│
│                   │     │  release()    │     │   set physically │
└──────────────────┘     │  gain_stage() │     │   or by scenario)│
                          └───────────────┘     │  IN1 ──▶ Zone 3  │
                                ▲               │  IN2 ──▶ Zone 4  │
                                │               │  IN3 ──▶ Zone 5  │
                                │               │  IN4 ──▶ Zone 6  │
                          ┌─────┴──────┐        └──────────────────┘
                          │  Decoders   │
                          │             │
                          │ Cambridge   │──── RCA ───▶ IN1   ← You choose which
                          │ squeezelite │──── RCA ───▶ IN2      physical input
                          └─────────────┘
```

The proxy claims the decoder and only activates the zone (OFF → ON).  
It does **not** send matrix source-routing commands. Routing is managed physically or via gateway scenario.

*(For legacy OpenWebNet implementation documentation, refer to the original bticino open specs).*
