let deviceTypes = {};   // catalog from /api/device_types
let cards = [];         // {uid, device_id, device_type, kwargs, x, y}
let capsByDeviceId = {}; // last-known real capabilities (positions) per device_id, from /api/devices
let liveValues = {};     // device_id -> { position_id: value }
let existingMapping = []; // preserved as-is, this page doesn't edit DUT mapping
let uidCounter = 0;

function nextUid() {
  uidCounter += 1;
  return `card_${uidCounter}`;
}

function defaultKwargs(deviceType) {
  const type = deviceTypes[deviceType];
  const kwargs = {};
  if (type) {
    for (const field of type.fields) kwargs[field.name] = field.default;
  }
  return kwargs;
}

// ---- loading ----

async function loadDeviceTypes() {
  const res = await fetch('/api/device_types');
  deviceTypes = await res.json();
  renderSidebar();
}

function renderSidebar() {
  const byCategory = {};
  for (const [typeName, info] of Object.entries(deviceTypes)) {
    byCategory[info.category] = byCategory[info.category] || [];
    byCategory[info.category].push([typeName, info]);
  }
  const categoryLabels = { psu: 'Power Supplies', relay: 'Relays', daq: 'Data Acquisition', generic: 'Generic / SCPI' };
  let html = '';
  for (const [cat, items] of Object.entries(byCategory)) {
    html += `<h2>${categoryLabels[cat] || cat}</h2>`;
    for (const [typeName, info] of items) {
      html += `<div class="type-card" draggable="true" data-type="${typeName}">${info.label}</div>`;
    }
  }
  document.getElementById('type-list').innerHTML = html;

  document.querySelectorAll('.type-card').forEach(el => {
    el.addEventListener('dragstart', (e) => {
      e.dataTransfer.setData('text/plain', el.dataset.type);
    });
  });
}

async function loadExistingConfig() {
  const res = await fetch('/api/config');
  const config = await res.json();
  existingMapping = config.mapping || [];
  const typeCounters = {};
  for (const entry of config.devices || []) {
    typeCounters[entry.device_type] = (typeCounters[entry.device_type] || 0) + 1;
    cards.push({
      uid: nextUid(),
      device_id: entry.device_id,
      device_type: entry.device_type,
      kwargs: entry.kwargs || {},
      x: typeof entry.x === 'number' ? entry.x : 40 + (typeCounters[entry.device_type] * 30),
      y: typeof entry.y === 'number' ? entry.y : 40 + (typeCounters[entry.device_type] * 30),
    });
  }
}

async function loadCapabilities() {
  try {
    const res = await fetch('/api/devices');
    const devices = await res.json();
    capsByDeviceId = {};
    for (const d of devices) capsByDeviceId[d.device_id] = d;
  } catch (e) {
    console.error('loadCapabilities failed:', e);
  }
}

// ---- rendering ----

function renderCanvas() {
  const canvas = document.getElementById('canvas');
  canvas.innerHTML = '';
  for (const card of cards) {
    canvas.appendChild(buildCardElement(card));
  }
}

function buildCardElement(card) {
  const el = document.createElement('div');
  el.className = 'device-card';
  el.style.left = `${card.x}px`;
  el.style.top = `${card.y}px`;
  el.dataset.uid = card.uid;

  const typeInfo = deviceTypes[card.device_type] || { label: card.device_type, category: 'generic', fields: [] };
  const caps = capsByDeviceId[card.device_id];

  el.innerHTML = `
    <div class="card-header">
      <input type="text" value="${card.device_id}" data-role="device-id">
      <span class="type-label">${typeInfo.label}</span>
      <button class="card-btn" data-role="settings-toggle" title="Settings">⚙</button>
      <button class="card-btn" data-role="remove" title="Remove">✕</button>
    </div>
    <div class="card-body" data-role="body"></div>
    <div class="settings-panel" data-role="settings" style="display:none;"></div>
  `;

  const body = el.querySelector('[data-role="body"]');
  body.innerHTML = renderBody(card, typeInfo, caps);

  const settings = el.querySelector('[data-role="settings"]');
  settings.innerHTML = renderSettings(card, typeInfo);

  wireCardEvents(el, card, typeInfo);
  return el;
}

function renderBody(card, typeInfo, caps) {
  const category = typeInfo.category;
  if (category === 'psu') return renderPsuBody(card, caps);
  if (category === 'relay') return renderRelayBody(card, caps);
  if (category === 'daq') return renderDaqBody(card, caps);
  return renderGenericBody(card, caps);
}

function fmt(value, digits) {
  if (value === undefined || value === null) return '—';
  if (typeof value === 'number') return value.toFixed(digits);
  return String(value);
}

function renderPsuBody(card, caps) {
  // Figure out how many channels this PSU has, preferring real capabilities
  // (accurate post-save), falling back to the configured kwarg (pre-save preview).
  const numChannels = caps
    ? new Set(caps.positions.map(p => (p.id.match(/^\D*(\d+)/) || [null, '1'])[1])).size || 1
    : parseInt(card.kwargs.num_channels || 1, 10);

  let html = '';
  for (let ch = 1; ch <= numChannels; ch++) {
    const vKey = numChannels > 1 || (caps && caps.positions.some(p => p.id === `v${ch}`)) ? `v${ch}` : 'voltage';
    const iKey = numChannels > 1 || (caps && caps.positions.some(p => p.id === `i${ch}`)) ? `i${ch}` : 'current';
    const outKey = numChannels > 1 || (caps && caps.positions.some(p => p.id === `output${ch}`)) ? `output${ch}` : 'output';
    const vVal = getLive(card.device_id, `${vKey}_meas`) ?? getLive(card.device_id, vKey);
    const iVal = getLive(card.device_id, `${iKey}_meas`) ?? getLive(card.device_id, iKey);
    const outVal = getLive(card.device_id, outKey);
    html += `
      <div class="readout-row">
        <span class="readout-label">Ch${ch} V</span>
        <span class="readout-value volts" data-readout="${vKey}_meas|${vKey}">${fmt(vVal, 2)}</span>
      </div>
      <div class="readout-row">
        <span class="readout-label">Ch${ch} A</span>
        <span class="readout-value amps" data-readout="${iKey}_meas|${iKey}">${fmt(iVal, 3)}</span>
      </div>
      <div class="toggle-row">
        <span class="readout-label">Output ${numChannels > 1 ? ch : ''}</span>
        <div class="toggle-switch ${outVal ? 'on' : ''}" data-toggle="${outKey}"><div class="knob"></div></div>
      </div>
    `;
  }
  return html;
}

function renderRelayBody(card, caps) {
  const numChannels = caps
    ? caps.positions.filter(p => p.id.startsWith('relay')).length
    : parseInt(card.kwargs.num_channels || 8, 10);
  let cells = '';
  for (let ch = 1; ch <= numChannels; ch++) {
    const val = getLive(card.device_id, `relay${ch}`);
    cells += `<div class="relay-cell">
      <div class="relay-led ${val ? 'on' : ''}" data-toggle="relay${ch}">${ch}</div>
    </div>`;
  }
  return `<div class="relay-grid">${cells}</div>`;
}

function renderDaqBody(card, caps) {
  const numChannels = caps
    ? caps.positions.filter(p => p.id.startsWith('ch')).length
    : parseInt(card.kwargs.num_channels || 8, 10);
  let html = '';
  for (let ch = 1; ch <= numChannels; ch++) {
    const val = getLive(card.device_id, `ch${ch}`);
    const unit = caps ? (caps.positions.find(p => p.id === `ch${ch}`) || {}).unit || '' : '';
    html += `
      <div class="readout-row">
        <span class="readout-label">Ch${ch}</span>
        <span class="readout-value plain" data-readout="ch${ch}">${fmt(val, 2)}${val !== undefined && val !== null ? ' ' + unit : ''}</span>
      </div>`;
  }
  return html || '<div class="generic-row">(connect to see channels)</div>';
}

function renderGenericBody(card, caps) {
  if (!caps) return '<div class="generic-row">(save &amp; reconnect to see positions)</div>';
  return caps.positions.map(p => {
    const val = getLive(card.device_id, p.id);
    return `<div class="generic-row"><span>${p.label}</span><span class="val" data-readout="${p.id}">${fmt(val, 3)}${p.unit ? ' ' + p.unit : ''}</span></div>`;
  }).join('');
}

function renderSettings(card, typeInfo) {
  let html = '';
  for (const field of typeInfo.fields) {
    const val = card.kwargs[field.name] !== undefined ? card.kwargs[field.name] : field.default;
    html += `<label>${field.label}<input type="${field.type === 'number' ? 'number' : 'text'}"
              data-kwarg="${field.name}" value="${val}"></label>`;
  }
  return html || '<div style="color:#8fa1b3;font-size:11px;">(no settings for this device type)</div>';
}

function getLive(deviceId, positionId) {
  const dev = liveValues[deviceId];
  if (!dev) return undefined;
  return dev[positionId];
}

// ---- events ----

function wireCardEvents(el, card, typeInfo) {
  const header = el.querySelector('.card-header');
  const deviceIdInput = el.querySelector('[data-role="device-id"]');
  const settingsToggle = el.querySelector('[data-role="settings-toggle"]');
  const settingsPanel = el.querySelector('[data-role="settings"]');
  const removeBtn = el.querySelector('[data-role="remove"]');

  deviceIdInput.addEventListener('change', () => { card.device_id = deviceIdInput.value.trim(); });
  deviceIdInput.addEventListener('mousedown', (e) => e.stopPropagation());

  settingsToggle.addEventListener('click', () => {
    settingsPanel.style.display = settingsPanel.style.display === 'none' ? 'block' : 'none';
  });

  removeBtn.addEventListener('click', () => {
    cards = cards.filter(c => c.uid !== card.uid);
    renderCanvas();
  });

  settingsPanel.querySelectorAll('input[data-kwarg]').forEach(input => {
    input.addEventListener('change', () => {
      card.kwargs[input.dataset.kwarg] = input.type === 'number' ? Number(input.value) : input.value;
    });
  });

  // toggles (output switches, relay LEDs) — only meaningful once connected for real
  el.querySelectorAll('[data-toggle]').forEach(toggle => {
    toggle.addEventListener('click', async () => {
      const positionId = toggle.dataset.toggle;
      if (!capsByDeviceId[card.device_id]) {
        alert('Save & Reconnect first so this device is actually connected.');
        return;
      }
      const currentlyOn = toggle.classList.contains('on');
      try {
        await fetch('/api/set_position', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ device_id: card.device_id, position_id: positionId, value: !currentlyOn }),
        });
        toggle.classList.toggle('on');
      } catch (e) {
        alert(`Could not toggle: ${e}`);
      }
    });
  });

  // drag-to-reposition via the header
  header.addEventListener('mousedown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    const canvasRect = document.getElementById('canvas').getBoundingClientRect();
    const startX = e.clientX;
    const startY = e.clientY;
    const originX = card.x;
    const originY = card.y;

    function onMove(moveEvent) {
      const dx = moveEvent.clientX - startX;
      const dy = moveEvent.clientY - startY;
      card.x = Math.max(0, originX + dx);
      card.y = Math.max(0, originY + dy);
      el.style.left = `${card.x}px`;
      el.style.top = `${card.y}px`;
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
  wrap.addEventListener('dragover', (e) => e.preventDefault());
  wrap.addEventListener('drop', (e) => {
    e.preventDefault();
    const deviceType = e.dataTransfer.getData('text/plain');
    if (!deviceType || !deviceTypes[deviceType]) return;
    const canvasRect = canvas.getBoundingClientRect();
    const x = e.clientX - canvasRect.left + wrap.scrollLeft;
    const y = e.clientY - canvasRect.top + wrap.scrollTop;

    const existingOfType = cards.filter(c => c.device_type === deviceType).length;
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

// ---- save / reconnect ----

function setStatus(message, isError) {
  const el = document.getElementById('status-msg');
  el.textContent = message;
  el.style.color = isError ? '#ff6b6b' : '#f4f4f4';
}

async function saveAndReconnect() {
  const ids = cards.map(c => c.device_id);
  const uniqueIds = new Set(ids);
  if (uniqueIds.size !== ids.length || ids.some(id => !id)) {
    alert('Each device needs a unique, non-empty name.');
    return;
  }

  const saveBtn = document.getElementById('save-btn');
  saveBtn.disabled = true;
  setStatus('Saving configuration…');

  const devices = cards.map(c => ({
    device_type: c.device_type,
    device_id: c.device_id,
    kwargs: c.kwargs,
    x: c.x,
    y: c.y,
  }));

  try {
    const saveRes = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ devices, mapping: existingMapping }),
    });
    if (!saveRes.ok) {
      const data = await saveRes.json();
      setStatus(`Save failed: ${data.detail || 'unknown error'}`, true);
      return;
    }

    setStatus('Reconnecting devices…');
    const reconnectRes = await fetch('/api/reconnect', { method: 'POST' });
    const reconnectData = await reconnectRes.json();
    if (!reconnectRes.ok) {
      setStatus(`Reconnect failed: ${reconnectData.detail || 'unknown error'}`, true);
      return;
    }

    await loadCapabilities();
    renderCanvas();

    if (reconnectData.failed && reconnectData.failed.length) {
      setStatus(`Connected: ${reconnectData.connected.join(', ') || 'none'}. Failed: ${reconnectData.failed.join(', ')}`, true);
    } else {
      setStatus(`All devices connected: ${reconnectData.connected.join(', ') || 'none'}`);
    }
  } catch (e) {
    setStatus(`Error: ${e}`, true);
  } finally {
    saveBtn.disabled = false;
  }
}

// ---- live polling ----

async function pollLiveValues() {
  try {
    const res = await fetch('/api/live_values');
    const data = await res.json();
    if (data.busy) {
      setStatus('A test is running — live readouts paused.');
      return;
    }
    liveValues = data.values || {};
    updateReadoutsInPlace();
  } catch (e) {
    // quietly ignore — likely a transient reload/reconnect in progress
  }
}

function updateReadoutsInPlace() {
  document.querySelectorAll('[data-readout]').forEach(elm => {
    const keys = elm.dataset.readout.split('|');
    const uidCard = elm.closest('.device-card');
    if (!uidCard) return;
    const card = cards.find(c => c.uid === uidCard.dataset.uid);
    if (!card) return;
    let value;
    for (const key of keys) {
      value = getLive(card.device_id, key);
      if (value !== undefined) break;
    }
    const digits = elm.classList.contains('amps') ? 3 : 2;
    elm.textContent = fmt(value, digits);
  });
  document.querySelectorAll('[data-toggle]').forEach(elm => {
    const uidCard = elm.closest('.device-card');
    if (!uidCard) return;
    const card = cards.find(c => c.uid === uidCard.dataset.uid);
    if (!card) return;
    const value = getLive(card.device_id, elm.dataset.toggle);
    if (value === undefined) return;
    elm.classList.toggle('on', !!value);
  });
}

window.addEventListener('DOMContentLoaded', async () => {
  await loadDeviceTypes();
  await loadExistingConfig();
  await loadCapabilities();
  renderCanvas();
  setupCanvasDropTarget();
  document.getElementById('save-btn').addEventListener('click', saveAndReconnect);
  setStatus('Loaded. Drag device types onto the canvas, then Save & Reconnect.');
  setInterval(pollLiveValues, 1500);
});
