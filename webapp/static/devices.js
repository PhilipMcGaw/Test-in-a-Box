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


function renderPsuBody(card, capabilities) {
  const numChannels = capabilities
    ? (
        new Set(
          (capabilities.positions || []).map(position => {
            const match = position.id.match(/^\D*(\d+)/);
            return match ? match[1] : '1';
          })
        ).size || 1
      )
    : parseInt(card.kwargs.num_channels || 1, 10);

  let html = '';

  for (let channel = 1; channel <= numChannels; channel += 1) {
    const hasNumberedVoltage = capabilities &&
      capabilities.positions.some(
        position => position.id === `v${channel}`
      );

    const hasNumberedCurrent = capabilities &&
      capabilities.positions.some(
        position => position.id === `i${channel}`
      );

    const hasNumberedOutput = capabilities &&
      capabilities.positions.some(
        position => position.id === `output${channel}`
      );

    const voltageKey =
      numChannels > 1 || hasNumberedVoltage
        ? `v${channel}`
        : 'voltage';

    const currentKey =
      numChannels > 1 || hasNumberedCurrent
        ? `i${channel}`
        : 'current';

    const outputKey =
      numChannels > 1 || hasNumberedOutput
        ? `output${channel}`
        : 'output';

    const voltageValue =
      getLive(card.device_id, `${voltageKey}_meas`) ??
      getLive(card.device_id, voltageKey);

    const currentValue =
      getLive(card.device_id, `${currentKey}_meas`) ??
      getLive(card.device_id, currentKey);

    const outputValue = getLive(
      card.device_id,
      outputKey
    );

    html += `
      <div class="readout-row">
        <span class="readout-label">Ch${channel} V</span>
        <span
          class="readout-value volts"
          data-readout="${voltageKey}_meas|${voltageKey}">
          ${fmt(voltageValue, 2)}
        </span>
      </div>

      <div class="readout-row">
        <span class="readout-label">Ch${channel} A</span>
        <span
          class="readout-value amps"
          data-readout="${currentKey}_meas|${currentKey}">
          ${fmt(currentValue, 3)}
        </span>
      </div>

      <div class="toggle-row">
        <span class="readout-label">
          Output ${numChannels > 1 ? channel : ''}
        </span>
        <div
          class="toggle-switch ${outputValue ? 'on' : ''}"
          data-toggle="${outputKey}">
          <div class="knob"></div>
        </div>
      </div>
    `;
  }

  return html;
}


function renderRelayBody(card, capabilities) {
  const numChannels = capabilities
    ? capabilities.positions.filter(
        position => position.id.startsWith('relay')
      ).length
    : parseInt(card.kwargs.num_channels || 8, 10);

  let cells = '';

  for (let channel = 1; channel <= numChannels; channel += 1) {
    const value = getLive(
      card.device_id,
      `relay${channel}`
    );

    cells += `
      <div class="relay-cell">
        <div
          class="relay-led ${value ? 'on' : ''}"
          data-toggle="relay${channel}">
          ${channel}
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
    .querySelectorAll('input[data-kwarg]')
    .forEach(input => {
      input.addEventListener('change', () => {
        card.kwargs[input.dataset.kwarg] =
          input.type === 'number'
            ? Number(input.value)
            : input.value;
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

    const existingOfType = cards.filter(
      card => card.device_type === deviceType
    ).length;

    const card = {
      uid: nextUid(),
      device_id: `${deviceType}_${existingOfType + 1}`,
      device_type: deviceType,
      kwargs: defaultKwargs(deviceType),
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
    x: card.x,
    y: card.y,
  }));

  try {
    const saveResponse = await fetch('/api/config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        devices,
        mapping: existingMapping,
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
