/**
 * MyHOME Bus Monitor — Custom Lovelace Card
 * 
 * Provides real-time streaming, filtering, and diagnostic frame transmission
 * for BTicino / Legrand MyHOME SCS bus systems via OpenWebNet.
 */

class MyHomeBusCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._frames = [];
    this._maxDisplayFrames = 200;
    this._isPaused = false;
    this._filterWho = "all";
    this._filterWhere = "";
    this._filterDir = "all";
    this._unsub = null;
    this._stats = { captured: 0, total_rx: 0, total_tx: 0 };
  }

  setConfig(config) {
    this._config = Object.assign(
      {
        title: "MyHOME Bus Monitor",
        max_frames: 200,
        mac: null,
      },
      config
    );
    this._maxDisplayFrames = this._config.max_frames || 200;
    this._render();
  }

  set hass(hass) {
    const oldHass = this._hass;
    this._hass = hass;

    // Connect stream once hass is available
    if (!oldHass && hass) {
      this._subscribeStream();
      this._loadHistory();
    }
  }

  connectedCallback() {
    if (this._hass && !this._unsub) {
      this._subscribeStream();
      this._loadHistory();
    }
  }

  disconnectedCallback() {
    if (this._unsub) {
      this._unsub();
      this._unsub = null;
    }
  }

  async _loadHistory() {
    if (!this._hass) return;
    try {
      const res = await this._hass.callWS({
        type: "myhome/bus_monitor/history",
        mac: this._config.mac,
        limit: 50,
      });
      if (res && res.frames) {
        this._frames = res.frames;
        if (res.stats) this._stats = res.stats;
        this._updateFrameList();
        this._updateStats();
      }
    } catch (err) {
      console.warn("MyHOME Bus Monitor: Failed to load initial history", err);
    }
  }

  async _subscribeStream() {
    if (!this._hass || this._unsub) return;
    try {
      this._unsub = await this._hass.connection.subscribeMessage(
        (frame) => this._onNewFrame(frame),
        {
          type: "myhome/bus_monitor/stream",
          mac: this._config.mac,
        }
      );
    } catch (err) {
      console.error("MyHOME Bus Monitor: Failed to subscribe to stream", err);
    }
  }

  _onNewFrame(frame) {
    if (this._isPaused) return;

    if (frame.direction === "rx") this._stats.total_rx++;
    else this._stats.total_tx++;
    this._stats.captured++;

    this._frames.push(frame);
    if (this._frames.length > this._maxDisplayFrames) {
      this._frames.shift();
    }

    this._appendFrameElement(frame);
    this._updateStats();
  }

  _matchesFilter(frame) {
    if (this._filterDir !== "all" && frame.direction !== this._filterDir) {
      return false;
    }
    if (this._filterWho !== "all" && String(frame.who) !== String(this._filterWho)) {
      return false;
    }
    if (this._filterWhere && !String(frame.where || "").toLowerCase().includes(this._filterWhere.toLowerCase())) {
      return false;
    }
    return true;
  }

  _formatWho(who) {
    const map = {
      "1": "Light/Switch",
      "2": "Automation",
      "4": "Heating",
      "15": "CEN",
      "16": "Sound",
      "18": "Energy",
      "25": "CEN+/Sec",
    };
    return map[String(who)] || (who ? `WHO=${who}` : "Sys");
  }

  _getWhoClass(who) {
    switch (String(who)) {
      case "1": return "who-light";
      case "2": return "who-cover";
      case "4": return "who-thermo";
      case "15":
      case "25": return "who-cen";
      case "16": return "who-sound";
      case "18": return "who-energy";
      default: return "who-default";
    }
  }

  _render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--ha-card-font-family, inherit);
        }
        ha-card {
          padding: 16px;
          background: var(--ha-card-background, var(--card-background-color, #fff));
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, none);
          border: var(--ha-card-border-width, 1px) solid var(--ha-card-border-color, var(--divider-color, #e0e0e0));
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }
        .title {
          font-size: 1.15rem;
          font-weight: 600;
          color: var(--primary-text-color);
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .badge {
          font-size: 0.75rem;
          padding: 2px 8px;
          border-radius: 12px;
          font-weight: 500;
        }
        .badge-live {
          background: rgba(76, 175, 80, 0.15);
          color: #2e7d32;
        }
        .badge-paused {
          background: rgba(244, 67, 54, 0.15);
          color: #d32f2f;
        }
        .stats-bar {
          display: flex;
          gap: 16px;
          font-size: 0.8rem;
          color: var(--secondary-text-color);
          margin-bottom: 12px;
          padding-bottom: 8px;
          border-bottom: 1px solid var(--divider-color, #eee);
        }
        .stat-val {
          font-weight: 600;
          color: var(--primary-text-color);
        }
        .controls {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-bottom: 12px;
        }
        select, input[type="text"] {
          background: var(--card-background-color, #fafafa);
          color: var(--primary-text-color);
          border: 1px solid var(--divider-color, #ccc);
          border-radius: 6px;
          padding: 6px 10px;
          font-size: 0.85rem;
        }
        button {
          background: var(--primary-color, #03a9f4);
          color: #fff;
          border: none;
          border-radius: 6px;
          padding: 6px 12px;
          font-size: 0.85rem;
          cursor: pointer;
          font-weight: 500;
          transition: opacity 0.2s;
        }
        button:hover { opacity: 0.85; }
        button.btn-secondary {
          background: var(--secondary-background-color, #eceff1);
          color: var(--primary-text-color);
        }
        .stream-container {
          background: #1e1e1e;
          color: #d4d4d4;
          font-family: monospace, monospace;
          font-size: 0.82rem;
          height: 280px;
          overflow-y: auto;
          border-radius: 8px;
          padding: 8px 12px;
          box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
        }
        .frame-line {
          display: flex;
          gap: 8px;
          padding: 2px 0;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          align-items: center;
        }
        .col-time { color: #888; flex-shrink: 0; }
        .col-dir {
          font-weight: 600;
          padding: 1px 4px;
          border-radius: 4px;
          font-size: 0.72rem;
          flex-shrink: 0;
        }
        .dir-rx { background: #1b5e20; color: #a5d6a7; }
        .dir-tx { background: #e65100; color: #ffcc80; }
        .col-who {
          font-size: 0.75rem;
          padding: 1px 6px;
          border-radius: 4px;
          flex-shrink: 0;
        }
        .who-light { background: #4a3b00; color: #ffe082; }
        .who-cover { background: #0d47a1; color: #90caf9; }
        .who-thermo { background: #b71c1c; color: #ef9a9a; }
        .who-cen { background: #4a148c; color: #ce93d8; }
        .who-sound { background: #004d40; color: #80cbc4; }
        .who-energy { background: #006064; color: #80deea; }
        .who-default { background: #37474f; color: #b0bec5; }
        .col-raw { color: #fff; word-break: break-all; }
        .raw-ack { color: #69f0ae; font-weight: 600; }
        .raw-nack { color: #ff5252; font-weight: 600; }
        .sender-bar {
          display: flex;
          gap: 8px;
          margin-top: 12px;
        }
        .sender-bar input { flex-grow: 1; }
      </style>

      <ha-card>
        <div class="header">
          <div class="title">
            <span>📡 ${this._config.title}</span>
            <span id="badge" class="badge badge-live">LIVE</span>
          </div>
          <div>
            <button id="btn-pause" class="btn-secondary">Pause</button>
            <button id="btn-clear" class="btn-secondary">Clear</button>
          </div>
        </div>

        <div class="stats-bar">
          <div>Captured: <span id="stat-captured" class="stat-val">0</span></div>
          <div>RX: <span id="stat-rx" class="stat-val">0</span></div>
          <div>TX: <span id="stat-tx" class="stat-val">0</span></div>
        </div>

        <div class="controls">
          <select id="filter-who">
            <option value="all">All Subsystems</option>
            <option value="1">Lighting / Switches (WHO=1)</option>
            <option value="2">Automation / Shutters (WHO=2)</option>
            <option value="4">Heating / Thermoregulation (WHO=4)</option>
            <option value="15">CEN Pushbuttons (WHO=15)</option>
            <option value="16">Sound System (WHO=16)</option>
            <option value="18">Energy Management (WHO=18)</option>
            <option value="25">CEN+ / Security (WHO=25)</option>
          </select>

          <input type="text" id="filter-where" placeholder="Filter WHERE (e.g. 12)..." style="width: 140px;" />

          <select id="filter-dir">
            <option value="all">All Directions</option>
            <option value="rx">RX (Bus Traffic)</option>
            <option value="tx">TX (Commands)</option>
          </select>
        </div>

        <div id="stream" class="stream-container"></div>

        <div class="sender-bar">
          <input type="text" id="send-frame" placeholder="Transmit frame (e.g. *1*1*12##)..." />
          <button id="btn-send">Send</button>
        </div>
      </ha-card>
    `;

    this._bindEvents();
  }

  _bindEvents() {
    const root = this.shadowRoot;
    root.getElementById("btn-pause").addEventListener("click", () => this._togglePause());
    root.getElementById("btn-clear").addEventListener("click", () => this._clearBuffer());
    root.getElementById("filter-who").addEventListener("change", (e) => {
      this._filterWho = e.target.value;
      this._updateFrameList();
    });
    root.getElementById("filter-where").addEventListener("input", (e) => {
      this._filterWhere = e.target.value;
      this._updateFrameList();
    });
    root.getElementById("filter-dir").addEventListener("change", (e) => {
      this._filterDir = e.target.value;
      this._updateFrameList();
    });
    root.getElementById("btn-send").addEventListener("click", () => this._sendCustomFrame());
    root.getElementById("send-frame").addEventListener("keydown", (e) => {
      if (e.key === "Enter") this._sendCustomFrame();
    });
  }

  _togglePause() {
    this._isPaused = !this._isPaused;
    const btn = this.shadowRoot.getElementById("btn-pause");
    const badge = this.shadowRoot.getElementById("badge");
    if (this._isPaused) {
      btn.textContent = "Resume";
      badge.textContent = "PAUSED";
      badge.className = "badge badge-paused";
    } else {
      btn.textContent = "Pause";
      badge.textContent = "LIVE";
      badge.className = "badge badge-live";
    }
  }

  async _clearBuffer() {
    this._frames = [];
    this._updateFrameList();
    if (this._hass) {
      try {
        await this._hass.callWS({
          type: "myhome/bus_monitor/clear",
          mac: this._config.mac,
        });
      } catch (err) {
        console.warn("Could not clear backend bus monitor", err);
      }
    }
  }

  async _sendCustomFrame() {
    const input = this.shadowRoot.getElementById("send-frame");
    const frame = input.value.trim();
    if (!frame || !this._hass) return;

    try {
      await this._hass.callWS({
        type: "myhome/bus_monitor/send",
        mac: this._config.mac,
        frame: frame,
      });
      input.value = "";
    } catch (err) {
      alert(`Error sending frame: ${err.message || err}`);
    }
  }

  _updateStats() {
    const root = this.shadowRoot;
    if (!root) return;
    const cap = root.getElementById("stat-captured");
    const rx = root.getElementById("stat-rx");
    const tx = root.getElementById("stat-tx");
    if (cap) cap.textContent = this._stats.captured;
    if (rx) rx.textContent = this._stats.total_rx;
    if (tx) tx.textContent = this._stats.total_tx;
  }

  _updateFrameList() {
    const container = this.shadowRoot.getElementById("stream");
    if (!container) return;
    container.innerHTML = "";
    for (const frame of this._frames) {
      if (this._matchesFilter(frame)) {
        container.appendChild(this._createFrameNode(frame));
      }
    }
    container.scrollTop = container.scrollHeight;
  }

  _appendFrameElement(frame) {
    if (!this._matchesFilter(frame)) return;
    const container = this.shadowRoot.getElementById("stream");
    if (!container) return;
    container.appendChild(this._createFrameNode(frame));
    container.scrollTop = container.scrollHeight;
  }

  _createFrameNode(frame) {
    const div = document.createElement("div");
    div.className = "frame-line";

    const timeStr = frame.iso_time ? frame.iso_time.split("T")[1].substring(0, 12) : "";
    const dirClass = frame.direction === "rx" ? "dir-rx" : "dir-tx";
    const dirLabel = frame.direction ? frame.direction.toUpperCase() : "RX";
    const whoClass = this._getWhoClass(frame.who);
    const whoLabel = this._formatWho(frame.who);

    let rawClass = "col-raw";
    if (frame.is_ack) rawClass += " raw-ack";
    if (frame.is_nack) rawClass += " raw-nack";

    div.innerHTML = `
      <span class="col-time">${timeStr}</span>
      <span class="col-dir ${dirClass}">${dirLabel}</span>
      <span class="col-who ${whoClass}">${whoLabel}</span>
      <span class="${rawClass}">${frame.raw}</span>
    `;
    return div;
  }

  getCardSize() {
    return 6;
  }
}

customElements.define("myhome-bus-card", MyHomeBusCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "myhome-bus-card",
  name: "MyHOME Bus Monitor",
  description: "Real-time OpenWebNet bus traffic stream and diagnostic frame sender.",
  preview: true,
});
