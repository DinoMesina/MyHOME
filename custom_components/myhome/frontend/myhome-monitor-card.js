/**
 * MyHOME Monitor Card
 * Custom Lovelace card for BTicino MyHOME Gateway & SCS Bus monitoring
 */

class MyHomeMonitorCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  setConfig(config) {
    this._config = {
      title: config.title || '',
      gateway_entity: config.gateway_entity || null,
      device_count_entity: config.device_count_entity || null,
      show_device_counts: config.show_device_counts !== false,
      show_attributes: config.show_attributes !== false,
      ...config
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _findEntities() {
    if (!this._hass) return { gatewayEntity: null, countEntity: null };

    let gatewayEntityId = this._config.gateway_entity;
    let countEntityId = this._config.device_count_entity;

    const allEntities = Object.keys(this._hass.states);

    // Auto-discover gateway connectivity entity if not specified
    if (!gatewayEntityId) {
      gatewayEntityId = allEntities.find(
        (id) => id.startsWith('binary_sensor.') && id.endsWith('_connectivity')
      );
    }

    // Auto-discover device count entity if not specified
    if (!countEntityId) {
      countEntityId = allEntities.find(
        (id) => id.startsWith('sensor.') && id.endsWith('_configured_devices')
      );
    }

    const gatewayEntity = gatewayEntityId ? this._hass.states[gatewayEntityId] : null;
    const countEntity = countEntityId ? this._hass.states[countEntityId] : null;

    return { gatewayEntity, countEntity, gatewayEntityId, countEntityId };
  }

  _formatUptime(isoTimestamp) {
    if (!isoTimestamp) return 'N/A';
    try {
      const start = new Date(isoTimestamp);
      const now = new Date();
      const diffMs = Math.max(0, now - start);
      const diffSec = Math.floor(diffMs / 1000);
      const days = Math.floor(diffSec / 86400);
      const hours = Math.floor((diffSec % 86400) / 3600);
      const mins = Math.floor((diffSec % 3600) / 60);

      if (days > 0) return `${days}d ${hours}h ${mins}m`;
      if (hours > 0) return `${hours}h ${mins}m`;
      return `${mins}m ${diffSec % 60}s`;
    } catch {
      return 'N/A';
    }
  }

  _openMoreInfo(entityId) {
    if (!entityId) return;
    const event = new CustomEvent('hass-more-info', {
      bubbles: true,
      composed: true,
      detail: { entityId },
    });
    this.dispatchEvent(event);
  }

  _render() {
    if (!this._hass) return;

    const { gatewayEntity, countEntity, gatewayEntityId, countEntityId } = this._findEntities();

    if (!gatewayEntity && !countEntity) {
      this.shadowRoot.innerHTML = `
        <style>
          ha-card {
            padding: 16px;
            color: var(--primary-text-color);
            background: var(--ha-card-background, var(--card-background-color, #fff));
            border-radius: var(--ha-card-border-radius, 12px);
          }
          .warning {
            color: var(--warning-color, #ff9800);
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
          }
        </style>
        <ha-card>
          <div class=warning>
            <ha-icon icon=mdi:alert-circle-outline></ha-icon>
            <span>MyHOME Gateway entities not found. Please check integration setup.</span>
          </div>
        </ha-card>
      `;
      return;
    }

    const isConnected = gatewayEntity ? gatewayEntity.state === 'on' : false;
    const gwAttrs = gatewayEntity ? gatewayEntity.attributes : {};
    const countAttrs = countEntity ? countEntity.attributes : {};

    const model = gwAttrs.model || 'MyHOME Gateway';
    const title = this._config.title || gwAttrs.friendly_name?.replace(' Connectivity', '') || model;
    const ip = gwAttrs.ip_address || '-';
    const port = gwAttrs.port || 20000;
    const firmware = gwAttrs.firmware ? `v${gwAttrs.firmware}` : '-';
    const reconnects = gwAttrs.reconnect_count ?? 0;
    const uptime = this._formatUptime(gwAttrs.connected_since);

    const totalDevices = countEntity ? countEntity.state : (countAttrs.total ?? 0);
    const lights = countAttrs.lights ?? 0;
    const covers = countAttrs.covers ?? 0;
    const climate = countAttrs.climate_zones ?? 0;
    const switches = countAttrs.switches ?? 0;
    const sensors = countAttrs.sensors ?? 0;
    const scenarios = countAttrs.scenarios ?? 0;

    this.shadowRoot.innerHTML = `
      <style>
        ha-card {
          padding: 20px;
          background: var(--ha-card-background, var(--card-background-color, #fff));
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, 0 2px 4px rgba(0,0,0,0.1));
          color: var(--primary-text-color);
          font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
        }
        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 16px;
        }
        .brand {
          display: flex;
          align-items: center;
          gap: 12px;
          cursor: pointer;
        }
        .brand-icon {
          width: 42px;
          height: 42px;
          border-radius: 10px;
          background: ${isConnected ? 'rgba(76, 175, 80, 0.12)' : 'rgba(244, 67, 54, 0.12)'};
          display: flex;
          align-items: center;
          justify-content: center;
          color: ${isConnected ? '#4caf50' : '#f44336'};
          transition: background 0.3s;
        }
        .brand-icon ha-icon {
          --mdc-icon-size: 26px;
        }
        .title-group {
          display: flex;
          flex-direction: column;
        }
        .title {
          font-size: 17px;
          font-weight: 600;
          line-height: 1.2;
          color: var(--primary-text-color);
        }
        .subtitle {
          font-size: 12px;
          color: var(--secondary-text-color);
          margin-top: 2px;
        }
        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 5px 12px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 600;
          letter-spacing: 0.3px;
          background: ${isConnected ? 'rgba(76, 175, 80, 0.15)' : 'rgba(244, 67, 54, 0.15)'};
          color: ${isConnected ? '#388e3c' : '#d32f2f'};
          cursor: pointer;
        }
        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: ${isConnected ? '#4caf50' : '#f44336'};
          box-shadow: ${isConnected ? '0 0 8px #4caf50' : 'none'};
        }
        .info-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
          gap: 10px;
          margin-bottom: 16px;
          background: var(--secondary-background-color, rgba(127, 127, 127, 0.05));
          padding: 12px;
          border-radius: 10px;
        }
        .info-item {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .info-label {
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: var(--secondary-text-color);
        }
        .info-value {
          font-size: 13px;
          font-weight: 500;
          color: var(--primary-text-color);
          word-break: break-word;
        }
        .divider {
          height: 1px;
          background: var(--divider-color, rgba(127, 127, 127, 0.15));
          margin: 16px 0;
        }
        .devices-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
        }
        .devices-title {
          font-size: 14px;
          font-weight: 600;
          color: var(--primary-text-color);
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .devices-title ha-icon {
          --mdc-icon-size: 18px;
          color: var(--secondary-text-color);
        }
        .total-badge {
          font-size: 12px;
          font-weight: 600;
          padding: 2px 8px;
          border-radius: 12px;
          background: var(--primary-color, #03a9f4);
          color: #fff;
          cursor: pointer;
        }
        .devices-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
          gap: 10px;
        }
        .device-card {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 10px 6px;
          border-radius: 8px;
          background: var(--card-background-color, var(--ha-card-background, #fafafa));
          border: 1px solid var(--divider-color, rgba(127, 127, 127, 0.12));
          text-align: center;
          cursor: pointer;
          transition: transform 0.15s, border-color 0.15s;
        }
        .device-card:hover {
          transform: translateY(-2px);
          border-color: var(--primary-color, #03a9f4);
        }
        .device-card ha-icon {
          --mdc-icon-size: 22px;
          color: var(--primary-color, #03a9f4);
          margin-bottom: 4px;
        }
        .device-num {
          font-size: 16px;
          font-weight: 700;
          color: var(--primary-text-color);
        }
        .device-label {
          font-size: 11px;
          color: var(--secondary-text-color);
          margin-top: 2px;
        }
      </style>

      <ha-card>
        <div class=header>
          <div class=brand id=brand-header>
            <div class=brand-icon>
              <ha-icon icon="mdi:router-network"></ha-icon>
            </div>
            <div class=title-group>
              <span class="title">${title}</span>
              <span class="subtitle">BTicino SCS Bus Gateway</span>
            </div>
          </div>
          <div class="status-badge" id="status-badge">
            <span class="status-dot"></span>
            <span>${isConnected ? 'Online' : 'Offline'}</span>
          </div>
        </div>

        ${this._config.show_attributes ? `
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">Address</span>
              <span class="info-value">${ip}:${port}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Model</span>
              <span class="info-value">${model}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Firmware</span>
              <span class="info-value">${firmware}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Uptime</span>
              <span class="info-value">${uptime}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Reconnects</span>
              <span class="info-value">${reconnects}</span>
            </div>
          </div>
        ` : ''}

        ${this._config.show_device_counts && countEntity ? `
          <div class="divider"></div>
          <div class="devices-header">
            <div class="devices-title">
              <ha-icon icon="mdi:view-grid-outline"></ha-icon>
              <span>Bus Devices</span>
            </div>
            <span class="total-badge" id="total-badge">${totalDevices} Total</span>
          </div>
          <div class="devices-grid">
            <div class="device-card" id="card-lights">
              <ha-icon icon="mdi:lightbulb-outline"></ha-icon>
              <span class="device-num">${lights}</span>
              <span class="device-label">Lights</span>
            </div>
            <div class="device-card" id="card-covers">
              <ha-icon icon="mdi:window-shutter"></ha-icon>
              <span class="device-num">${covers}</span>
              <span class="device-label">Shutters</span>
            </div>
            <div class="device-card" id="card-climate">
              <ha-icon icon="mdi:thermostat"></ha-icon>
              <span class="device-num">${climate}</span>
              <span class="device-label">Climate</span>
            </div>
            <div class="device-card" id="card-switches">
              <ha-icon icon="mdi:toggle-switch-outline"></ha-icon>
              <span class="device-num">${switches}</span>
              <span class="device-label">Switches</span>
            </div>
            <div class="device-card" id="card-sensors">
              <ha-icon icon="mdi:motion-sensor"></ha-icon>
              <span class="device-num">${sensors}</span>
              <span class="device-label">Sensors</span>
            </div>
            <div class="device-card" id="card-scenarios">
              <ha-icon icon="mdi:palette-outline"></ha-icon>
              <span class="device-num">${scenarios}</span>
              <span class="device-label">Scenarios</span>
            </div>
          </div>
        ` : ''}
      </ha-card>
    `;

    // Add click listeners
    const brand = this.shadowRoot.getElementById('brand-header');
    if (brand && gatewayEntityId) {
      brand.addEventListener('click', () => this._openMoreInfo(gatewayEntityId));
    }
    const badge = this.shadowRoot.getElementById('status-badge');
    if (badge && gatewayEntityId) {
      badge.addEventListener('click', () => this._openMoreInfo(gatewayEntityId));
    }
    const totalBadge = this.shadowRoot.getElementById('total-badge');
    if (totalBadge && countEntityId) {
      totalBadge.addEventListener('click', () => this._openMoreInfo(countEntityId));
    }
    const countCards = this.shadowRoot.querySelectorAll('.device-card');
    countCards.forEach((c) => {
      if (countEntityId) {
        c.addEventListener('click', () => this._openMoreInfo(countEntityId));
      }
    });
  }

  getCardSize() {
    return 4;
  }

  static getStubConfig() {
    return {
      title: 'MyHOME Gateway',
      show_device_counts: true,
      show_attributes: true
    };
  }
}

customElements.define('myhome-monitor-card', MyHomeMonitorCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'myhome-monitor-card',
  name: 'MyHOME Monitor Card',
  description: 'Monitor BTicino MyHOME Gateway status, connectivity, and SCS bus devices.',
  preview: true,
  documentationURL: 'https://github.com/mantovanellimatteo/MyHOME'
});

console.info(
  '%c MYHOME-MONITOR-CARD %c v1.3.0 ',
  'color: white; background: #ea5b0c; font-weight: 700;',
  'color: #ea5b0c; background: white; font-weight: 700;'
);
