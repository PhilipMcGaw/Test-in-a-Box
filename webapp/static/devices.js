let deviceTypes = {};    // catalogue from /api/device_types
let cards = [];          // {uid, device_id, device_type, kwargs, x, y}
let capsByDeviceId = {}; // last-known capabilities per device_id
let liveValues = {};     // device_id -> {position_id: value}
let existingMapping = []; // preserved as-is; this page does not edit DUT mapping
let uidCounter = 0;


function nextUid() {
  uidCounter += 1;
  return `card_${uidCounter}`;
}


function defaultDeviceId(deviceType) {
  const info = deviceTypes[deviceType] || {};
  const baseLabel = String(
    info.label || info.default_role || deviceType
  ).trim();

  const existingNames = new Set(
    cards.map(card => card.device_id.trim().toLowerCase())
  );

  let sequence = 1;
  let candidate = `${baseLabel} ${sequence}`;

  while (existingNames.has(candidate.toLowerCase())) {
    sequence += 1;
    candidate = `${baseLabel} ${sequence}`;
  }

  return candidate;
}


function defaultKwargs(deviceType) {
  const type = deviceTypes[deviceType];
  const kwargs = {};

  if (type) {
    for (const field of type.fields || []) {
      kwargs[field.name] = field.default;
    }
  }

  return kwargs;
}


function formatApiError(data, fallback = 'Unknown error') {
  if (!data) {
    return fallback;
  }

  const detail = data.detail;

  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail.map(item => {
      if (typeof item === 'string') {
        return item;
      }

      if (item && typeof item === 'object') {
        const location = Array.isArray(item.loc)
          ? item.loc.join(' → ')
          : '';

        const message =
          item.msg ||
          item.message ||
          JSON.stringify(item);

        return location ? `${location}: ${message}` : message;
      }

      return String(item);
    }).join('; ');
  }

  if (detail && typeof detail === 'object') {
    try {
      return JSON.stringify(detail);
    } catch {
      return String(detail);
    }
  }

  if (typeof data.message === 'string') {
    return data.message;
  }

  try {
    return JSON.stringify(data);
  } catch {
    return fallback;
  }
}


async function readJsonSafely(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}


// ---------------------------------------------------------------------------
// Loading
// ---------------------------------------------------------------------------

async function loadDeviceTypes() {
  const response = await fetch('/api/device_types');

  if (!response.ok) {
    const data = await readJsonSafely(response);
    throw new Error(
      formatApiError(data, `HTTP ${response.status}`)
    );
  }

  deviceTypes = await response.json();
  renderSidebar();
}


function renderSidebar() {
  const byCategory = {};

  for (const [typeName, info] of Object.entries(deviceTypes)) {
    const category = info.category || 'generic';
    byCategory[category] = byCategory[category] || [];
    byCategory[category].push([typeName, info]);
  }

  const categoryLabels = {
    psu: 'Power Supplies',
    relay: 'Relays',
    daq: 'Data Acquisition',
    generic: 'Generic / SCPI',
  };

  let html = '';

  for (const [category, items] of Object.entries(byCategory)) {
    html += `<h2>${categoryLabels[category] || category}</h2>`;

    for (const [typeName, info] of items) {
      const status = info.status_description || info.status || '';
      const title = status
        ? `${info.label}: ${status}`
        : info.label;

      html += `
        <div
          class="type-card"
          draggable="true"
          data-type="${escapeHtml(typeName)}"
          title="${escapeHtml(title)}">
          ${escapeHtml(info.label)}
        </div>
      `;
    }
  }

  document.getElementById('type-list').innerHTML = html;

  document.querySelectorAll('.type-card').forEach(element => {
    element.addEventListener('dragstart', event => {
      event.dataTransfer.setData(
        'text/plain',
        element.dataset.type
      );
    });
  });
}


async function loadExistingConfig() {
  const response = await fetch('/api/config');

  if (!response.ok) {
    const data = await readJsonSafely(response);
    throw new Error(
      formatApiError(data, `HTTP ${response.status}`)
    );
  }

  const config = await response.json();
  existingMapping = config.mapping || [];

  const typeCounters = {};

  for (const entry of config.devices || []) {
    typeCounters[entry.device_type] =
      (typeCounters[entry.device_type] || 0) + 1;

    cards.push({
      uid: nextUid(),
      device_id: entry.device_id,
      device_type: entry.device_type,
      kwargs: entry.kwargs || {},
      channel_labels: entry.channel_labels || {},
      x: typeof entry.x === 'number'
        ? entry.x
        : 40 + (typeCounters[entry.device_type] * 30),
      y: typeof entry.y === 'number'
        ? entry.y
        : 40 + (typeCounters[entry.device_type] * 30),
    });
  }
}


async function loadCapabilities() {
  try {
    const response = await fetch('/api/devices');

    if (!response.ok) {
      const data = await readJsonSafely(response);
      throw new Error(
        formatApiError(data, `HTTP ${response.status}`)
      );
    }

    const devices = await response.json();
    capsByDeviceId = {};

    for (const device of devices) {
      capsByDeviceId[device.device_id] = device;
    }
  } catch (error) {
    console.error('loadCapabilities failed:', error);
    capsByDeviceId = {};
  }
}


// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

function renderCanvas() {
  const canvas = document.getElementById('canvas');
  canvas.innerHTML = '';

  for (const card of cards) {
    canvas.appendChild(buildCardElement(card));
  }
}


function buildCardElement(card) {
  const element = document.createElement('div');
  element.className = 'device-card';
  element.style.left = `${card.x}px`;
  element.style.top = `${card.y}px`;
  element.dataset.uid = card.uid;

  const typeInfo = deviceTypes[card.device_type] || {
    label: card.device_type,
    category: 'generic',
    fields: [],
  };

  const capabilities = capsByDeviceId[card.device_id];

  element.innerHTML = `
    <div class="card-header">
      <input
        type="text"
        value="${escapeHtml(card.device_id)}"
        data-role="device-id">
      <span class="type-label">${escapeHtml(typeInfo.label)}</span>
      <button
        class="card-btn"
        data-role="settings-toggle"
        title="Settings">⚙</button>
      <button
        class="card-btn"
        data-role="remove"
        title="Remove">✕</button>
    </div>
    <div class="card-body" data-role="body"></div>
    <div
      class="settings-panel"
      data-role="settings"
      style="display:none;"></div>
  `;

  const body = element.querySelector('[data-role="body"]');
  body.innerHTML = renderBody(card, typeInfo, capabilities);

  const settings = element.querySelector('[data-role="settings"]');
  settings.innerHTML = renderSettings(card, typeInfo);

  wireCardEvents(element, card);
  return element;
}


function renderBody(card, typeInfo, capabilities) {
  const category = typeInfo.category;

  if (category === 'psu') {
    return renderPsuBody(card, capabilities);
  }

  if (category === 'relay') {
    return renderRelayBody(card, capabilities);
  }

  if (category === 'daq') {
    return renderDaqBody(card, capabilities);
  }

  return renderGenericBody(card, capabilities);
}


function fmt(value, digits) {
  if (value === undefined || value === null) {
    return '—';
  }

  if (typeof value === 'number') {
    return value.toFixed(digits);
  }

  return String(value);
}


function findPosition(positions, ids, predicate = null) {
  for (const id of ids) {
    const match = positions.find(position => position.id === id);
    if (match) {
      return match;
    }
  }
  return predicate ? positions.find(predicate) || null : null;
}


function commissioningSetpoint(card, position, value) {
  if (!position) {
    return '';
  }

  return `
    <div class="commission-control">
      <label>${escapeHtml(position.label)}</label>
      <div class="commission-input-row">
        <input
          type="number"
          step="any"
          inputmode="decimal"
          class="commission-number"
          data-commission-value="${escapeHtml(position.id)}"
          value="${
            typeof value === 'number' && Number.isFinite(value)
              ? escapeHtml(value)
              : ''
          }">
        <span class="commission-unit">
          ${escapeHtml(position.unit || '')}
        </span>
        <button
          type="button"
          class="commission-apply"
          data-commission-apply="${escapeHtml(position.id)}">
          Apply
        </button>
      </div>
    </div>
  `;
}


function commissioningMeasurement(card, position) {
  if (!position) {
    return '';
  }

  const value = getLive(card.device_id, position.id);

  return `
    <div class="readout-row">
      <span class="readout-label">${escapeHtml(position.label)}</span>
      <span
        class="readout-value plain"
        data-readout="${escapeHtml(position.id)}">
        ${fmt(value, 3)}${
          position.unit ? ` ${escapeHtml(position.unit)}` : ''
        }
      </span>
    </div>
  `;
}


function renderPsuBody(card, capabilities) {
  if (!capabilities) {
    return (
      '<div class="generic-row">' +
      'Save &amp; Reconnect to commission this PSU.' +
      '</div>'
    );
  }

  if (capabilities.error) {
    return `
      <div class="generic-row">
        <span>Connection error</span>
        <span class="val">${escapeHtml(capabilities.error)}</span>
      </div>
    `;
  }

  const positions = capabilities.positions || [];
  const numbered = positions.some(position =>
    /^v\d+$|^i\d+$|^output\d+$/.test(String(position.id))
  );

  const channelNumbers = positions
    .map(position => {
      const match = String(position.id).match(/\d+/);
      return match ? Number(match[0]) : null;
    })
    .filter(value => value !== null);

  const channelCount = numbered && channelNumbers.length
    ? Math.max(...channelNumbers)
    : 1;

  let html = '';

  for (let channel = 1; channel <= channelCount; channel += 1) {
    const suffix = numbered ? String(channel) : '';
    const channelHeading = channelCount > 1
      ? `<div class="commission-channel-heading">Channel ${channel}</div>`
      : '';

    const voltageSet = findPosition(
      positions,
      [`v${suffix}`, 'voltage_set', 'voltage'],
      position =>
        position.kind === 'output_analog' &&
        String(position.unit || '').toLowerCase() === 'v'
    );

    const currentSet = findPosition(
      positions,
      [`i${suffix}`, 'current_set', 'current'],
      position =>
        position.kind === 'output_analog' &&
        String(position.unit || '').toLowerCase() === 'a'
    );

    const output = findPosition(
      positions,
      [`output${suffix}`, 'output'],
      position =>
        position.kind === 'output_digital' &&
        /output|enable/i.test(`${position.id} ${position.label}`)
    );

    const voltageActual = findPosition(
      positions,
      [`v${suffix}_meas`, 'voltage_actual', 'voltage_meas'],
      position =>
        position.kind === 'input_analog' &&
        String(position.unit || '').toLowerCase() === 'v'
    );

    const currentActual = findPosition(
      positions,
      [`i${suffix}_meas`, 'current_actual', 'current_meas'],
      position =>
        position.kind === 'input_analog' &&
        String(position.unit || '').toLowerCase() === 'a'
    );

    const powerActual = findPosition(
      positions,
      ['power_actual', 'power_meas'],
      position =>
        position.kind === 'input_analog' &&
        String(position.unit || '').toLowerCase() === 'w'
    );

    const range = findPosition(
      positions,
      [`range${suffix}`, 'range1', 'range']
    );

    html += channelHeading;
    html += '<div class="psu-section-label">SETPOINTS</div>';
    html += commissioningSetpoint(
      card,
      voltageSet,
      voltageSet ? getLive(card.device_id, voltageSet.id) : undefined
    );
    html += commissioningSetpoint(
      card,
      currentSet,
      currentSet ? getLive(card.device_id, currentSet.id) : undefined
    );

    if (range) {
      const rangeValue = getLive(card.device_id, range.id);
      html += `
        <div class="range-row">
          <label class="readout-label">${escapeHtml(range.label)}</label>
          <select
            class="range-select"
            data-range-select="${escapeHtml(range.id)}">
            <option value="0" ${Number(rangeValue) === 0 ? 'selected' : ''}>
              15 V / 5 A
            </option>
            <option value="1" ${Number(rangeValue) === 1 ? 'selected' : ''}>
              35 V / 3 A
            </option>
            <option value="2" ${Number(rangeValue) === 2 ? 'selected' : ''}>
              35 V / 500 mA
            </option>
          </select>
        </div>
        <div class="range-warning">
          Changing range switches the PSU output off.
        </div>
      `;
    }

    if (output) {
      const enabled = Boolean(getLive(card.device_id, output.id));
      html += `
        <div class="psu-section-label">OUTPUT CONTROL</div>
        <div class="toggle-row">
          <span class="readout-label">${escapeHtml(output.label)}</span>
          <div
            class="toggle-switch ${enabled ? 'on' : ''}"
            data-toggle="${escapeHtml(output.id)}">
            <div class="knob"></div>
          </div>
        </div>
      `;
    }

    html += '<div class="psu-section-label">LIVE MEASUREMENTS</div>';
    html += commissioningMeasurement(card, voltageActual);
    html += commissioningMeasurement(card, currentActual);
    html += commissioningMeasurement(card, powerActual);
  }

  return html || (
    '<div class="generic-row">No PSU commissioning controls available.</div>'
  );
}

function relayChannelCount(card, capabilities) {
  if (capabilities) {
    const count = (capabilities.positions || []).filter(
      position => String(position.id).startsWith('relay')
    ).length;

    if (count > 0) {
      return count;
    }
  }

  return parseInt(card.kwargs.num_channels || 8, 10);
}


function relayChannelLabel(card, capabilities, positionId, channel) {
  const configured = card.channel_labels?.[positionId];

  if (configured) {
    return configured;
  }

  const position = (capabilities?.positions || []).find(
    item => item.id === positionId
  );

  return position?.label || `Relay ${channel}`;
}


function renderRelayBody(card, capabilities) {
  const numChannels = relayChannelCount(card, capabilities);
  let cells = '';

  for (let channel = 1; channel <= numChannels; channel += 1) {
    const positionId = `relay${channel}`;
    const value = getLive(card.device_id, positionId);
    const label = relayChannelLabel(
      card,
      capabilities,
      positionId,
      channel
    );

    cells += `
      <div class="relay-cell">
        <div
          class="relay-led ${value ? 'on' : ''}"
          data-toggle="${positionId}"
          title="${escapeHtml(`Relay ${channel}: ${label}`)}">
          <span class="relay-number">${channel}</span>
          <span class="relay-label">${escapeHtml(label)}</span>
        </div>
      </div>
    `;
  }

  return `<div class="relay-grid">${cells}</div>`;
}


function renderDaqBody(card, capabilities) {
  const numChannels = capabilities
    ? capabilities.positions.filter(
        position => position.id.startsWith('ch')
      ).length
    : parseInt(card.kwargs.num_channels || 8, 10);

  let html = '';

  for (let channel = 1; channel <= numChannels; channel += 1) {
    const positionId = `ch${channel}`;
    const value = getLive(card.device_id, positionId);

    const unit = capabilities
      ? (
          capabilities.positions.find(
            position => position.id === positionId
          ) || {}
        ).unit || ''
      : '';

    html += `
      <div class="readout-row">
        <span class="readout-label">Ch${channel}</span>
        <span
          class="readout-value plain"
          data-readout="${positionId}">
          ${fmt(value, 2)}${
            value !== undefined && value !== null && unit
              ? ` ${escapeHtml(unit)}`
              : ''
          }
        </span>
      </div>
    `;
  }

  return html ||
    '<div class="generic-row">(connect to see channels)</div>';
}


function renderGenericBody(card, capabilities) {
  if (!capabilities) {
    return (
      '<div class="generic-row">' +
      '(save &amp; reconnect to see positions)' +
      '</div>'
    );
  }

  if (capabilities.error) {
    return `
      <div class="generic-row">
        <span>Connection error</span>
        <span class="val">${escapeHtml(capabilities.error)}</span>
      </div>
    `;
  }

  return (capabilities.positions || []).map(position => {
    const value = getLive(
      card.device_id,
      position.id
    );

    return `
      <div class="generic-row">
        <span>${escapeHtml(position.label)}</span>
        <span
          class="val"
          data-readout="${escapeHtml(position.id)}">
          ${fmt(value, 3)}${
            position.unit
              ? ` ${escapeHtml(position.unit)}`
              : ''
          }
        </span>
      </div>
    `;
  }).join('');
}


function renderSettings(card, typeInfo) {
  let html = '';

  for (const field of typeInfo.fields || []) {
    const value =
      card.kwargs[field.name] !== undefined
        ? card.kwargs[field.name]
        : field.default;

    if (field.name === 'serial_port' || field.type === 'serial_port') {
      const currentValue = String(value ?? '');

      html += `
        <label>
          ${escapeHtml(field.label)}
          <select
            data-kwarg="${escapeHtml(field.name)}"
            data-serial-port-select="${escapeHtml(field.name)}">
            <option value="${escapeHtml(currentValue)}" selected>
              ${escapeHtml(currentValue || 'Select a COM port')}
            </option>
          </select>
        </label>
        <div class="serial-port-actions">
          <button
            type="button"
            class="discover-btn"
            data-refresh-serial-field="${escapeHtml(field.name)}">
            Refresh COM Ports
          </button>
          <button
            type="button"
            class="discover-btn"
            data-probe-serial-field="${escapeHtml(field.name)}">
            Find Compatible Instrument
          </button>
        </div>
        <div
          class="discovery-status"
          data-serial-status="${escapeHtml(field.name)}">
        </div>
      `;
      continue;
    }

    if (field.type === 'discovery') {
      const currentValue = String(value ?? '');
      const currentLabel = currentValue
        ? currentValue
        : (field.empty_label || 'No instrument selected');

      html += `
        <label>
          ${escapeHtml(field.label)}
          <select
            data-kwarg="${escapeHtml(field.name)}"
            data-discovery-select="${escapeHtml(field.name)}">
            <option value="${escapeHtml(currentValue)}" selected>
              ${escapeHtml(currentLabel)}
            </option>
          </select>
        </label>
        <button
          type="button"
          class="discover-btn"
          data-discover-field="${escapeHtml(field.name)}"
          data-discovery-driver="${escapeHtml(
            field.discovery_driver || card.device_type
          )}">
          Scan for Devices
        </button>
        <div
          class="discovery-status"
          data-discovery-status="${escapeHtml(field.name)}">
        </div>
      `;
      continue;
    }

    html += `
      <label>
        ${escapeHtml(field.label)}
        <input
          type="${field.type === 'number' ? 'number' : 'text'}"
          data-kwarg="${escapeHtml(field.name)}"
          value="${escapeHtml(String(value ?? ''))}">
      </label>
    `;
  }

  if (typeInfo.category === 'relay') {
    const capabilities = capsByDeviceId[card.device_id];
    const numChannels = relayChannelCount(card, capabilities);

    html += `
      <div class="relay-label-settings">
        <div class="relay-label-heading">Relay channel labels</div>
        <div class="relay-label-help">
          Give each channel a meaningful engineering name.
          Leave a field blank to use the default relay number.
        </div>
    `;

    for (let channel = 1; channel <= numChannels; channel += 1) {
      const positionId = `relay${channel}`;
      const configuredLabel =
        card.channel_labels?.[positionId] || '';

      html += `
        <label class="relay-label-setting">
          <span>Relay ${channel}</span>
          <input
            type="text"
            maxlength="80"
            data-channel-label="${positionId}"
            value="${escapeHtml(configuredLabel)}"
            placeholder="Relay ${channel}">
        </label>
      `;
    }

    html += '</div>';
  }

  if (typeInfo.setup_note) {
    html += `
      <div class="instrument-setup-note">
        <strong>Setup note</strong>
        <p>${escapeHtml(typeInfo.setup_note)}</p>
        ${
          typeInfo.product_url
            ? `<a
                 href="${escapeHtml(typeInfo.product_url)}"
                 target="_blank"
                 rel="noopener noreferrer">
                 Open manufacturer product page
               </a>`
            : ''
        }
      </div>
    `;
  }

  return html || (
    '<div style="color:#8fa1b3;font-size:11px;">' +
    '(no settings for this device type)' +
    '</div>'
  );
}

function getLive(deviceId, positionId) {
  const device = liveValues[deviceId];

  if (!device) {
    return undefined;
  }

  return device[positionId];
}


function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}


// ---------------------------------------------------------------------------
// Card events
// ---------------------------------------------------------------------------

async function fetchSerialPorts() {
  const response = await fetch('/api/serial_ports');
  const data = await readJsonSafely(response);

  if (!response.ok) {
    throw new Error(formatApiError(data, `HTTP ${response.status}`));
  }

  return Array.isArray(data) ? data : [];
}


function populateSerialPortSelect(select, ports, currentValue = '') {
  select.innerHTML = '';

  if (!ports.length) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = 'No COM ports found';
    select.appendChild(option);
    return;
  }

  for (const port of ports) {
    const option = document.createElement('option');
    option.value = port.device;
    option.textContent = port.display_name || port.device;
    select.appendChild(option);
  }

  if (ports.some(port => port.device === currentValue)) {
    select.value = currentValue;
  }
}


function wireCardEvents(element, card) {
  const header = element.querySelector('.card-header');
  const deviceIdInput = element.querySelector(
    '[data-role="device-id"]'
  );
  const settingsToggle = element.querySelector(
    '[data-role="settings-toggle"]'
  );
  const settingsPanel = element.querySelector(
    '[data-role="settings"]'
  );
  const removeButton = element.querySelector(
    '[data-role="remove"]'
  );

  deviceIdInput.addEventListener('change', () => {
    card.device_id = deviceIdInput.value.trim();
  });

  deviceIdInput.addEventListener('mousedown', event => {
    event.stopPropagation();
  });

  settingsToggle.addEventListener('click', () => {
    settingsPanel.style.display =
      settingsPanel.style.display === 'none'
        ? 'block'
        : 'none';
  });

  removeButton.addEventListener('click', () => {
    cards = cards.filter(
      candidate => candidate.uid !== card.uid
    );
    renderCanvas();
  });

  settingsPanel
    .querySelectorAll('[data-kwarg]')
    .forEach(control => {
      control.addEventListener('change', () => {
        card.kwargs[control.dataset.kwarg] =
          control.type === 'number'
            ? Number(control.value)
            : control.value;
      });

      control.addEventListener('mousedown', event => {
        event.stopPropagation();
      });
    });

  settingsPanel
    .querySelectorAll('[data-channel-label]')
    .forEach(control => {
      control.addEventListener('change', () => {
        const positionId = control.dataset.channelLabel;
        const label = control.value.trim();

        card.channel_labels = card.channel_labels || {};

        if (label) {
          card.channel_labels[positionId] = label;
        } else {
          delete card.channel_labels[positionId];
        }
      });

      control.addEventListener('mousedown', event => {
        event.stopPropagation();
      });
    });

  settingsPanel
    .querySelectorAll('[data-refresh-serial-field]')
    .forEach(button => {
      button.addEventListener('click', async () => {
        const fieldName = button.dataset.refreshSerialField;
        const select = settingsPanel.querySelector(
          `[data-serial-port-select="${fieldName}"]`
        );
        const status = settingsPanel.querySelector(
          `[data-serial-status="${fieldName}"]`
        );

        button.disabled = true;
        status.textContent = 'Reading Windows COM ports…';

        try {
          const ports = await fetchSerialPorts();
          populateSerialPortSelect(
            select,
            ports,
            card.kwargs[fieldName] || ''
          );

          if (!ports.length) {
            card.kwargs[fieldName] = '';
            status.textContent = 'No COM ports are currently available.';
            return;
          }

          if (!ports.some(
            port => port.device === card.kwargs[fieldName]
          )) {
            select.selectedIndex = 0;
            card.kwargs[fieldName] = select.value;
          }

          status.textContent =
            `Found ${ports.length} COM port${ports.length === 1 ? '' : 's'}.`;
        } catch (error) {
          status.textContent =
            `COM port refresh failed: ${error.message || error}`;
        } finally {
          button.disabled = false;
        }
      });
    });

  settingsPanel
    .querySelectorAll('[data-probe-serial-field]')
    .forEach(button => {
      button.addEventListener('click', async () => {
        const fieldName = button.dataset.probeSerialField;
        const select = settingsPanel.querySelector(
          `[data-serial-port-select="${fieldName}"]`
        );
        const status = settingsPanel.querySelector(
          `[data-serial-status="${fieldName}"]`
        );

        button.disabled = true;
        status.textContent =
          'Opening each COM port and requesting instrument identity…';

        try {
          const response = await fetch('/api/serial_ports/probe', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              device_type: card.device_type,
              kwargs: card.kwargs,
            }),
          });

          const data = await readJsonSafely(response);

          if (!response.ok) {
            throw new Error(
              formatApiError(data, `HTTP ${response.status}`)
            );
          }

          const compatible = (data || []).filter(
            item => item.compatible
          );

          select.innerHTML = '';

          if (!compatible.length) {
            const ports = (data || []).map(item => item.port_metadata);
            populateSerialPortSelect(
              select,
              ports.filter(Boolean),
              card.kwargs[fieldName] || ''
            );
            status.textContent =
              'No compatible instrument identified. Check cable, baud rate, ' +
              'terminator, and whether another program owns the port.';
            return;
          }

          for (const item of compatible) {
            const option = document.createElement('option');
            option.value = item.port;
            option.textContent = item.display_name || item.port;
            select.appendChild(option);
          }

          select.selectedIndex = 0;
          card.kwargs[fieldName] = select.value;

          const selected = compatible[0];
          const identity = selected.identity || {};
          const identityText = [
            identity.manufacturer,
            identity.model,
            identity.serial
              ? `S/N ${identity.serial}`
              : '',
          ].filter(Boolean).join(' ');

          status.textContent =
            `Identified ${compatible.length} compatible instrument` +
            `${compatible.length === 1 ? '' : 's'}.` +
            (identityText ? ` Selected: ${identityText}.` : '');
        } catch (error) {
          status.textContent =
            `Instrument scan failed: ${error.message || error}`;
        } finally {
          button.disabled = false;
        }
      });
    });

  settingsPanel
    .querySelectorAll('[data-discover-field]')
    .forEach(button => {
      button.addEventListener('click', async () => {
        const fieldName = button.dataset.discoverField;
        const driverType = button.dataset.discoveryDriver;
        const select = settingsPanel.querySelector(
          `[data-discovery-select="${fieldName}"]`
        );
        const status = settingsPanel.querySelector(
          `[data-discovery-status="${fieldName}"]`
        );

        button.disabled = true;
        status.textContent = 'Scanning…';

        try {
          const response = await fetch(
            `/api/discover/${encodeURIComponent(driverType)}`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                kwargs: card.kwargs,
              }),
            }
          );

          const data = await readJsonSafely(response);

          if (!response.ok) {
            throw new Error(
              formatApiError(data, `HTTP ${response.status}`)
            );
          }

          select.innerHTML = '';

          if (!Array.isArray(data) || data.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No compatible instruments found';
            select.appendChild(option);
            card.kwargs[fieldName] = '';
            status.textContent = 'No compatible instruments found.';
            return;
          }

          for (const item of data) {
            const option = document.createElement('option');
            option.value = item.selector;
            option.textContent = item.display_name;
            select.appendChild(option);
          }

          const currentValue = card.kwargs[fieldName] || '';
          const matchingOption = Array.from(select.options).find(
            option => option.value === currentValue
          );

          if (matchingOption) {
            select.value = currentValue;
          } else {
            select.selectedIndex = 0;
            card.kwargs[fieldName] = select.value;
          }

          status.textContent =
            `Found ${data.length} compatible instrument` +
            `${data.length === 1 ? '' : 's'}.`;
        } catch (error) {
          status.textContent =
            `Scan failed: ${error.message || error}`;
        } finally {
          button.disabled = false;
        }
      });
    });

  element.querySelectorAll('[data-toggle]').forEach(toggle => {
    toggle.addEventListener('click', async () => {
      const positionId = toggle.dataset.toggle;

      if (!capsByDeviceId[card.device_id]) {
        alert(
          'Save & Reconnect first so this instrument is connected.'
        );
        return;
      }

      const currentlyOn = toggle.classList.contains('on');

      try {
        const response = await fetch('/api/set_position', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            device_id: card.device_id,
            position_id: positionId,
            value: !currentlyOn,
          }),
        });

        const data = await readJsonSafely(response);

        if (!response.ok) {
          throw new Error(
            formatApiError(
              data,
              `HTTP ${response.status}`
            )
          );
        }

        toggle.classList.toggle('on');
      } catch (error) {
        alert(`Could not toggle: ${error.message || error}`);
      }
    });
  });

  element.querySelectorAll('[data-commission-apply]').forEach(button => {
    button.addEventListener('click', async () => {
      const positionId = button.dataset.commissionApply;
      const input = element.querySelector(
        `[data-commission-value="${positionId}"]`
      );
      const value = Number(input?.value);

      if (!capsByDeviceId[card.device_id]) {
        alert('Save & Reconnect first so this instrument is connected.');
        return;
      }

      if (!Number.isFinite(value) || value < 0) {
        alert('Enter a valid non-negative numeric value.');
        return;
      }

      button.disabled = true;

      try {
        const response = await fetch('/api/set_position', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            device_id: card.device_id,
            position_id: positionId,
            value,
          }),
        });

        const data = await readJsonSafely(response);
        if (!response.ok) {
          throw new Error(formatApiError(data, `HTTP ${response.status}`));
        }

        liveValues[card.device_id] = liveValues[card.device_id] || {};
        liveValues[card.device_id][positionId] = value;
        await pollLiveValues();
      } catch (error) {
        alert(`Could not apply value: ${error.message || error}`);
      } finally {
        button.disabled = false;
      }
    });
  });

  element.querySelectorAll('[data-commission-value]').forEach(input => {
    input.addEventListener('mousedown', event => event.stopPropagation());
    input.addEventListener('keydown', event => {
      if (event.key === 'Enter') {
        const positionId = input.dataset.commissionValue;
        element.querySelector(
          `[data-commission-apply="${positionId}"]`
        )?.click();
      }
    });
  });

  element.querySelectorAll('[data-range-select]').forEach(select => {
    select.addEventListener('mousedown', event => {
      event.stopPropagation();
    });

    select.addEventListener('change', async () => {
      const positionId = select.dataset.rangeSelect;
      const previousValue = getLive(
        card.device_id,
        positionId
      );

      const confirmed = window.confirm(
        'Changing the PSU range will switch its output off. Continue?'
      );

      if (!confirmed) {
        if (previousValue !== undefined) {
          select.value = String(previousValue);
        }
        return;
      }

      select.disabled = true;

      try {
        const response = await fetch('/api/set_position', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            device_id: card.device_id,
            position_id: positionId,
            value: Number(select.value),
          }),
        });

        const data = await readJsonSafely(response);

        if (!response.ok) {
          throw new Error(
            formatApiError(data, `HTTP ${response.status}`)
          );
        }

        // The physical QL355P disables its output during a range change.
        liveValues[card.device_id] = liveValues[card.device_id] || {};
        liveValues[card.device_id][positionId] = Number(select.value);
        liveValues[card.device_id].output1 = false;

        await pollLiveValues();
        renderCanvas();
      } catch (error) {
        if (previousValue !== undefined) {
          select.value = String(previousValue);
        }
        alert(`Could not change PSU range: ${error.message || error}`);
      } finally {
        select.disabled = false;
      }
    });
  });

  header.addEventListener('mousedown', event => {
    if (
      event.target.tagName === 'INPUT' ||
      event.target.tagName === 'BUTTON'
    ) {
      return;
    }

    const startX = event.clientX;
    const startY = event.clientY;
    const originX = card.x;
    const originY = card.y;

    function onMove(moveEvent) {
      const deltaX = moveEvent.clientX - startX;
      const deltaY = moveEvent.clientY - startY;

      card.x = Math.max(0, originX + deltaX);
      card.y = Math.max(0, originY + deltaY);

      element.style.left = `${card.x}px`;
      element.style.top = `${card.y}px`;
    }

    function onUp() {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    }

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  });
}


function setupCanvasDropTarget() {
  const wrap = document.getElementById('canvas-wrap');
  const canvas = document.getElementById('canvas');

  wrap.addEventListener('dragover', event => {
    event.preventDefault();
  });

  wrap.addEventListener('drop', event => {
    event.preventDefault();

    const deviceType =
      event.dataTransfer.getData('text/plain');

    if (!deviceType || !deviceTypes[deviceType]) {
      return;
    }

    const canvasRect = canvas.getBoundingClientRect();

    const x =
      event.clientX -
      canvasRect.left +
      wrap.scrollLeft;

    const y =
      event.clientY -
      canvasRect.top +
      wrap.scrollTop;

    const card = {
      uid: nextUid(),
      device_id: defaultDeviceId(deviceType),
      device_type: deviceType,
      kwargs: defaultKwargs(deviceType),
      channel_labels: {},
      x: Math.max(0, x - 100),
      y: Math.max(0, y - 20),
    };

    cards.push(card);
    renderCanvas();
  });
}


// ---------------------------------------------------------------------------
// Save and reconnect
// ---------------------------------------------------------------------------

function setStatus(message, isError = false) {
  const element = document.getElementById('status-msg');
  element.textContent = message;
  element.style.color = isError ? '#ff6b6b' : '#f4f4f4';
}


function validateCardsBeforeSave() {
  const ids = cards.map(card => card.device_id.trim());
  const uniqueIds = new Set(ids);

  if (ids.some(id => !id)) {
    return 'Each instrument needs a non-empty name.';
  }

  if (uniqueIds.size !== ids.length) {
    return 'Each instrument needs a unique name.';
  }

  for (const card of cards) {
    if (!deviceTypes[card.device_type]) {
      return (
        `Unknown instrument type "${card.device_type}" ` +
        `for "${card.device_id}".`
      );
    }
  }

  return null;
}


async function saveAndReconnect() {
  const validationError = validateCardsBeforeSave();

  if (validationError) {
    alert(validationError);
    return;
  }

  const saveButton = document.getElementById('save-btn');
  saveButton.disabled = true;
  setStatus('Saving configuration…');

  const devices = cards.map(card => ({
    device_type: card.device_type,
    device_id: card.device_id.trim(),
    kwargs: card.kwargs,
    channel_labels: card.channel_labels || {},
    x: card.x,
    y: card.y,
  }));

  // Remove DUT mappings that refer to instruments deleted from this page.
  const activeDeviceIds = new Set(
    devices.map(device => device.device_id)
  );

  const validMapping = existingMapping.filter(entry =>
    activeDeviceIds.has(entry.device_id)
  );

  try {
    const saveResponse = await fetch('/api/config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        devices,
        mapping: validMapping,
      }),
    });

    const saveData = await readJsonSafely(saveResponse);

    if (!saveResponse.ok) {
      setStatus(
        `Save failed: ${formatApiError(
          saveData,
          `HTTP ${saveResponse.status}`
        )}`,
        true
      );
      return;
    }

    setStatus('Reconnecting instruments…');

    const reconnectResponse = await fetch(
      '/api/reconnect',
      { method: 'POST' }
    );

    const reconnectData =
      await readJsonSafely(reconnectResponse);

    if (!reconnectResponse.ok) {
      setStatus(
        `Reconnect failed: ${formatApiError(
          reconnectData,
          `HTTP ${reconnectResponse.status}`
        )}`,
        true
      );
      return;
    }

    await loadCapabilities();
    renderCanvas();

    const connected = reconnectData?.connected || [];
    const failed = reconnectData?.failed || [];

    if (failed.length) {
      setStatus(
        `Connected: ${connected.join(', ') || 'none'}. ` +
        `Failed: ${failed.join(', ')}`,
        true
      );
    } else {
      setStatus(
        `All instruments connected: ` +
        `${connected.join(', ') || 'none'}`
      );
    }
  } catch (error) {
    setStatus(
      `Error: ${error.message || error}`,
      true
    );
  } finally {
    saveButton.disabled = false;
  }
}


// ---------------------------------------------------------------------------
// Live polling
// ---------------------------------------------------------------------------

async function pollLiveValues() {
  try {
    const response = await fetch('/api/live_values');
    const data = await readJsonSafely(response);

    if (!response.ok) {
      console.warn(
        'Live values failed:',
        formatApiError(data, `HTTP ${response.status}`)
      );
      return;
    }

    if (data.busy) {
      setStatus(
        'A test is running — live readouts paused.'
      );
      return;
    }

    liveValues = data.values || {};
    updateReadoutsInPlace();

    const errors = data.errors || {};
    const errorCount = Object.values(errors).reduce(
      (count, item) =>
        count + Object.keys(item || {}).length,
      0
    );

    if (errorCount > 0) {
      console.warn('Live read errors:', errors);
    }
  } catch (error) {
    console.warn('Live value polling failed:', error);
  }
}


function updateReadoutsInPlace() {
  document.querySelectorAll('[data-readout]').forEach(element => {
    const keys = element.dataset.readout.split('|');
    const cardElement = element.closest('.device-card');

    if (!cardElement) {
      return;
    }

    const card = cards.find(
      candidate => candidate.uid === cardElement.dataset.uid
    );

    if (!card) {
      return;
    }

    let value;

    for (const key of keys) {
      value = getLive(card.device_id, key);

      if (value !== undefined) {
        break;
      }
    }

    const digits =
      element.classList.contains('amps')
        ? 3
        : 2;

    element.textContent = fmt(value, digits);
  });

  document.querySelectorAll('[data-toggle]').forEach(element => {
    const cardElement = element.closest('.device-card');

    if (!cardElement) {
      return;
    }

    const card = cards.find(
      candidate => candidate.uid === cardElement.dataset.uid
    );

    if (!card) {
      return;
    }

    const value = getLive(
      card.device_id,
      element.dataset.toggle
    );

    if (value === undefined) {
      return;
    }

    element.classList.toggle('on', Boolean(value));
  });

  document.querySelectorAll('[data-range-select]').forEach(element => {
    const cardElement = element.closest('.device-card');

    if (!cardElement) {
      return;
    }

    const card = cards.find(
      candidate => candidate.uid === cardElement.dataset.uid
    );

    if (!card) {
      return;
    }

    const value = getLive(
      card.device_id,
      element.dataset.rangeSelect
    );

    if (value !== undefined) {
      element.value = String(value);
    }
  });
}


// ---------------------------------------------------------------------------
// Initialisation
// ---------------------------------------------------------------------------

window.addEventListener('DOMContentLoaded', async () => {
  try {
    setStatus('Loading instrument library…');

    await loadDeviceTypes();
    await loadExistingConfig();
    await loadCapabilities();

    renderCanvas();
    setupCanvasDropTarget();

    document
      .getElementById('save-btn')
      .addEventListener('click', saveAndReconnect);

    setStatus(
      'Loaded. Drag instrument types onto the canvas, ' +
      'then Save & Reconnect.'
    );

    setInterval(pollLiveValues, 1500);
  } catch (error) {
    console.error(error);
    setStatus(
      `Could not load Configure Devices: ` +
      `${error.message || error}`,
      true
    );
  }
});
