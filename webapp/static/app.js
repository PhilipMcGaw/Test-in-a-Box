const TOOLBOX = {
  kind: "categoryToolbox",
  contents: [
    {
      kind: "category",
      name: "Power Supplies",
      colour: "210",
      contents: [
        { kind: "block", type: "hw_psu_set_voltage" },
        { kind: "block", type: "hw_psu_set_current" },
        { kind: "block", type: "hw_psu_output" },
        { kind: "block", type: "hw_psu_read_voltage" },
        { kind: "block", type: "hw_psu_read_current" },
        { kind: "block", type: "hw_psu_ramp_voltage" },
      ],
    },
    {
      kind: "category",
      name: "Generic Instruments",
      colour: "210",
      contents: [
        { kind: "block", type: "hw_set" },
        { kind: "block", type: "hw_get" },
      ],
    },
    {
      kind: "category",
      name: "Operator Input",
      colour: "290",
      contents: [
        { kind: "block", type: "hw_prompt" },
      ],
    },
    {
      kind: "category",
      name: "Logic & Checks",
      colour: "0",
      contents: [
        { kind: "block", type: "hw_assert" },
        { kind: "block", type: "hw_within_tolerance" },
        { kind: "block", type: "logic_compare" },
        { kind: "block", type: "logic_operation" },
        { kind: "block", type: "logic_boolean" },
      ],
    },
    {
      kind: "category",
      name: "Loops",
      colour: "120",
      contents: [
        { kind: "block", type: "controls_repeat_ext" },
        { kind: "block", type: "controls_whileUntil" },
        { kind: "block", type: "controls_for" },
      ],
    },
    {
      kind: "category",
      name: "Timing & Results",
      colour: "65",
      contents: [
        { kind: "block", type: "hw_wait" },
        { kind: "block", type: "hw_log" },
      ],
    },
    {
      kind: "category",
      name: "Math",
      colour: "230",
      contents: [
        { kind: "block", type: "math_number" },
        { kind: "block", type: "math_arithmetic" },
      ],
    },
    {
      kind: "category",
      name: "Variables",
      colour: "330",
      custom: "VARIABLE",
    },
  ],
};

let workspace;

async function loadDevices() {
  const res = await fetch('/api/devices');
  const devices = await res.json();

  const outputs = [];
  const inputs = [];

  const psuVoltageOutputs = [];
  const psuCurrentOutputs = [];
  const psuOutputSwitches = [];
  const psuVoltageInputs = [];
  const psuCurrentInputs = [];

  function channelNumber(positionId) {
    const match = String(positionId).match(/(\d+)/);
    return match ? Number(match[1]) : 1;
  }

  function positionValue(deviceId, positionId) {
    return `${deviceId}|${positionId}`;
  }

  function psuLabel(deviceId, positionId, description, channelCount) {
    if (channelCount <= 1) {
      return `${deviceId}: ${description}`;
    }

    return (
      `${deviceId}: Channel ${channelNumber(positionId)} ${description}`
    );
  }

  for (const dev of devices) {
    const positions = dev.positions || [];

    for (const pos of positions) {
      const label = `${dev.device_id}: ${pos.label}`;
      const value = positionValue(dev.device_id, pos.id);

      if (pos.kind.startsWith('output')) {
        outputs.push([label, value]);
      } else {
        inputs.push([label, value]);
      }
    }

    // Identify PSU positions by engineering meaning rather than by driver
    // name, so the blocks work with mock, Aim-TTi and future PSU drivers.
    const voltageOutputs = positions.filter(pos =>
      pos.kind === 'output_analog' &&
      pos.unit === 'V' &&
      !String(pos.id).endsWith('_meas')
    );

    const currentOutputs = positions.filter(pos =>
      pos.kind === 'output_analog' &&
      pos.unit === 'A' &&
      !String(pos.id).endsWith('_meas')
    );

    const outputSwitches = positions.filter(pos =>
      pos.kind === 'output_digital' &&
      (
        String(pos.id).toLowerCase().startsWith('output') ||
        String(pos.label).toLowerCase().includes('output')
      )
    );

    const voltageInputs = positions.filter(pos =>
      pos.kind === 'input_analog' &&
      pos.unit === 'V'
    );

    const currentInputs = positions.filter(pos =>
      pos.kind === 'input_analog' &&
      pos.unit === 'A'
    );

    const channelCount = Math.max(
      voltageOutputs.length,
      currentOutputs.length,
      outputSwitches.length,
      voltageInputs.length,
      currentInputs.length,
      1
    );

    for (const pos of voltageOutputs) {
      psuVoltageOutputs.push([
        psuLabel(
          dev.device_id,
          pos.id,
          'Voltage',
          channelCount
        ),
        positionValue(dev.device_id, pos.id),
      ]);
    }

    for (const pos of currentOutputs) {
      psuCurrentOutputs.push([
        psuLabel(
          dev.device_id,
          pos.id,
          'Current Limit',
          channelCount
        ),
        positionValue(dev.device_id, pos.id),
      ]);
    }

    for (const pos of outputSwitches) {
      psuOutputSwitches.push([
        psuLabel(
          dev.device_id,
          pos.id,
          'Output',
          channelCount
        ),
        positionValue(dev.device_id, pos.id),
      ]);
    }

    for (const pos of voltageInputs) {
      psuVoltageInputs.push([
        psuLabel(
          dev.device_id,
          pos.id,
          'Measured Voltage',
          channelCount
        ),
        positionValue(dev.device_id, pos.id),
      ]);
    }

    for (const pos of currentInputs) {
      psuCurrentInputs.push([
        psuLabel(
          dev.device_id,
          pos.id,
          'Measured Current',
          channelCount
        ),
        positionValue(dev.device_id, pos.id),
      ]);
    }
  }

  window.HW_OUTPUT_POSITIONS = outputs.length
    ? outputs
    : [["(no output instruments)", "none|none"]];

  window.HW_INPUT_POSITIONS = inputs.length
    ? inputs
    : [["(no input instruments)", "none|none"]];

  window.HW_PSU_VOLTAGE_OUTPUTS = psuVoltageOutputs.length
    ? psuVoltageOutputs
    : [["(no PSU voltage outputs)", "none|none"]];

  window.HW_PSU_CURRENT_OUTPUTS = psuCurrentOutputs.length
    ? psuCurrentOutputs
    : [["(no PSU current outputs)", "none|none"]];

  window.HW_PSU_OUTPUT_SWITCHES = psuOutputSwitches.length
    ? psuOutputSwitches
    : [["(no PSU outputs)", "none|none"]];

  window.HW_PSU_VOLTAGE_INPUTS = psuVoltageInputs.length
    ? psuVoltageInputs
    : [["(no PSU voltage measurements)", "none|none"]];

  window.HW_PSU_CURRENT_INPUTS = psuCurrentInputs.length
    ? psuCurrentInputs
    : [["(no PSU current measurements)", "none|none"]];

  const list = document.getElementById('device-list');
  list.innerHTML = devices.map(device =>
    `<li><strong>${device.device_id}</strong> ` +
    `(${device.device_type}) — ` +
    `${device.positions.length} position(s)</li>`
  ).join('');
}

async function loadDuts() {
  try {
    const res = await fetch('/api/duts');
    const duts = await res.json();
    window.HW_DUTS = duts.length ? duts.map(d => [d, d]) : [["(no DUTs configured)", "none"]];
  } catch (e) {
    console.error('loadDuts failed:', e);
    window.HW_DUTS = [["(no DUTs configured)", "none"]];
  }
}

// Some locked-down browser profiles (seen with corporate Firefox policies)
// disable localStorage entirely, which throws instead of just no-op'ing.
// Wrap it so a blocked storage doesn't take the whole app down with it —
// worst case, workspace save/restore across reloads just doesn't happen.
const safeStorage = {
  get(key) {
    try { return localStorage.getItem(key); }
    catch (e) { console.warn('localStorage unavailable (get):', e); return null; }
  },
  set(key, value) {
    try { localStorage.setItem(key, value); }
    catch (e) { console.warn('localStorage unavailable (set) — workspace will not persist across reloads:', e); }
  },
};

function initWorkspace() {
  workspace = Blockly.inject('blocklyDiv', {
    toolbox: TOOLBOX,
    trashcan: true,
    zoom: { controls: true, wheel: true },
    media: '/static/blockly/media/',
  });

  const saved = safeStorage.get('tiab_workspace');
  if (saved) {
    try {
      Blockly.serialization.workspaces.load(JSON.parse(saved), workspace);
    } catch (e) {
      console.warn('could not restore saved workspace', e);
    }
  }

  workspace.addChangeListener(() => {
    const state = Blockly.serialization.workspaces.save(workspace);
    safeStorage.set('tiab_workspace', JSON.stringify(state));
  });
}

function appendConsole(line) {
  const el = document.getElementById('console');
  el.textContent += line + "\n";
  el.scrollTop = el.scrollHeight;
}

let currentState = 'idle';

function applyState(state) {
  currentState = state;
  const runBtn = document.getElementById('run-btn');
  const pauseBtn = document.getElementById('pause-btn');
  const stepBtn = document.getElementById('step-btn');
  const stopBtn = document.getElementById('stop-btn');

  runBtn.textContent = (state === 'paused' || state === 'pause_requested') ? '▶ Resume' : '▶ Run';
  runBtn.disabled = (state === 'running');
  pauseBtn.disabled = (state !== 'running');
  stepBtn.disabled = (state !== 'paused');
  stopBtn.disabled = !(state === 'running' || state === 'paused' || state === 'pause_requested' || state === 'step');
}

async function respondToPrompt(promptId, label) {
  const value = window.prompt(label, '') || '';
  try {
    await fetch('/api/control/prompt_response', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt_id: promptId, value }),
    });
  } catch (e) {
    appendConsole(`[error] could not send prompt response: ${e}`);
  }
}

let ws;
function connectConsole() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws/console`);
  ws.onmessage = (evt) => {
    if (evt.data.startsWith('__STATE__:')) {
      applyState(evt.data.slice('__STATE__:'.length));
    } else if (evt.data.startsWith('__PROMPT__:')) {
      const rest = evt.data.slice('__PROMPT__:'.length);
      const sep = rest.indexOf(':');
      const promptId = rest.slice(0, sep);
      const label = rest.slice(sep + 1);
      appendConsole(`[prompt] waiting for operator input: ${label}`);
      respondToPrompt(promptId, label);
    } else {
      appendConsole(evt.data);
    }
  };
  ws.onclose = () => appendConsole('[console disconnected — reload the page]');
}

async function runScript() {
  if (currentState === 'paused' || currentState === 'pause_requested') {
    await fetch('/api/control/resume', { method: 'POST' });
    return;
  }
  const code = Blockly.Python.workspaceToCode(workspace);
  document.getElementById('generated-code').textContent = code;
  document.getElementById('console').textContent = '';
  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    });
    const data = await res.json();
    if (!res.ok) appendConsole(`[error] ${data.detail || 'run failed'}`);
  } catch (e) {
    appendConsole(`[error] ${e}`);
  }
}

async function pauseScript() {
  await fetch('/api/control/pause', { method: 'POST' });
}

async function stepScript() {
  await fetch('/api/control/step', { method: 'POST' });
}

async function stopScript() {
  await fetch('/api/control/stop', { method: 'POST' });
}

async function syncStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    applyState(data.state);
  } catch (e) {
    console.warn('could not fetch initial status', e);
  }
}

// ---- sequences (save/load workspaces to/from the server's sequences/ folder) ----

async function refreshSequenceList() {
  const select = document.getElementById('sequence-select');
  try {
    const res = await fetch('/api/sequences');
    const names = await res.json();
    select.innerHTML = names.length
      ? names.map(n => `<option value="${n}">${n}</option>`).join('')
      : '<option value="">(no saved sequences)</option>';
  } catch (e) {
    select.innerHTML = '<option value="">(could not load list)</option>';
  }
}

async function saveSequence() {
  const nameInput = document.getElementById('sequence-name');
  const name = nameInput.value.trim();
  if (!name) {
    alert('Enter a name for this sequence first.');
    return;
  }
  const state = Blockly.serialization.workspaces.save(workspace);
  try {
    const res = await fetch(`/api/sequences/${encodeURIComponent(name)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace: state }),
    });
    const data = await res.json();
    if (!res.ok) {
      alert(`Could not save: ${data.detail || 'unknown error'}`);
      return;
    }
    nameInput.value = '';
    await refreshSequenceList();
  } catch (e) {
    alert(`Could not save: ${e}`);
  }
}

async function loadSequence() {
  const select = document.getElementById('sequence-select');
  const name = select.value;
  if (!name) return;
  try {
    const res = await fetch(`/api/sequences/${encodeURIComponent(name)}`);
    const data = await res.json();
    if (!res.ok) {
      alert(`Could not load: ${data.detail || 'unknown error'}`);
      return;
    }
    workspace.clear();
    Blockly.serialization.workspaces.load(data, workspace);
  } catch (e) {
    alert(`Could not load: ${e}`);
  }
}

window.addEventListener('DOMContentLoaded', async () => {
  try { await loadDevices(); } catch (e) { console.error('loadDevices failed:', e); }
  try { await loadDuts(); } catch (e) { console.error('loadDuts failed:', e); }
  try { initWorkspace(); } catch (e) { console.error('initWorkspace failed:', e); }
  try { connectConsole(); } catch (e) { console.error('connectConsole failed:', e); }
  try { await syncStatus(); } catch (e) { console.error('syncStatus failed:', e); }
  try { await refreshSequenceList(); } catch (e) { console.error('refreshSequenceList failed:', e); }

  document.getElementById('run-btn').addEventListener('click', runScript);
  document.getElementById('pause-btn').addEventListener('click', pauseScript);
  document.getElementById('step-btn').addEventListener('click', stepScript);
  document.getElementById('stop-btn').addEventListener('click', stopScript);
  document.getElementById('refresh-devices-btn').addEventListener('click', async () => {
    await loadDevices();
    await loadDuts();
  });
  document.getElementById('save-sequence-btn').addEventListener('click', saveSequence);
  document.getElementById('load-sequence-btn').addEventListener('click', loadSequence);
});
