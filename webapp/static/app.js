const TOOLBOX = {
  kind: "categoryToolbox",
  contents: [
    { kind: "category", name: "Hardware", colour: "210",
      contents: [
        { kind: "block", type: "hw_set" },
        { kind: "block", type: "hw_get" },
      ] },
    { kind: "category", name: "Logic & Checks", colour: "0",
      contents: [
        { kind: "block", type: "hw_assert" },
        { kind: "block", type: "hw_within_tolerance" },
        { kind: "block", type: "logic_compare" },
        { kind: "block", type: "logic_operation" },
        { kind: "block", type: "logic_boolean" },
      ] },
    { kind: "category", name: "Loops", colour: "120",
      contents: [
        { kind: "block", type: "controls_repeat_ext" },
        { kind: "block", type: "controls_whileUntil" },
        { kind: "block", type: "controls_for" },
      ] },
    { kind: "category", name: "Timing & Notes", colour: "65",
      contents: [
        { kind: "block", type: "hw_wait" },
        { kind: "block", type: "hw_log" },
      ] },
    { kind: "category", name: "Math", colour: "230",
      contents: [
        { kind: "block", type: "math_number" },
        { kind: "block", type: "math_arithmetic" },
      ] },
    { kind: "category", name: "Variables", colour: "330", custom: "VARIABLE" },
  ]
};

let workspace;

async function loadDevices() {
  const res = await fetch('/api/devices');
  const devices = await res.json();

  const outputs = [];
  const inputs = [];
  for (const dev of devices) {
    for (const pos of dev.positions) {
      const label = `${dev.device_id}: ${pos.label}`;
      const value = `${dev.device_id}|${pos.id}`;
      if (pos.kind.startsWith('output')) outputs.push([label, value]);
      else inputs.push([label, value]);
    }
  }
  window.HW_OUTPUT_POSITIONS = outputs.length ? outputs : [["(no output devices)", "none|none"]];
  window.HW_INPUT_POSITIONS = inputs.length ? inputs : [["(no input devices)", "none|none"]];

  const list = document.getElementById('device-list');
  list.innerHTML = devices.map(d =>
    `<li><strong>${d.device_id}</strong> (${d.device_type}) — ${d.positions.length} position(s)</li>`
  ).join('');
}

function initWorkspace() {
  workspace = Blockly.inject('blocklyDiv', {
    toolbox: TOOLBOX,
    trashcan: true,
    zoom: { controls: true, wheel: true },
    media: '/static/blockly/media/',
  });

  const saved = localStorage.getItem('hwapp_workspace');
  if (saved) {
    try {
      Blockly.serialization.workspaces.load(JSON.parse(saved), workspace);
    } catch (e) {
      console.warn('could not restore saved workspace', e);
    }
  }

  workspace.addChangeListener(() => {
    const state = Blockly.serialization.workspaces.save(workspace);
    localStorage.setItem('hwapp_workspace', JSON.stringify(state));
  });
}

function appendConsole(line) {
  const el = document.getElementById('console');
  el.textContent += line + "\n";
  el.scrollTop = el.scrollHeight;
}

let ws;
function connectConsole() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws/console`);
  ws.onmessage = (evt) => appendConsole(evt.data);
  ws.onclose = () => appendConsole('[console disconnected — reload the page]');
}

async function runScript() {
  const code = Blockly.Python.workspaceToCode(workspace);
  document.getElementById('generated-code').textContent = code;
  document.getElementById('console').textContent = '';
  document.getElementById('run-btn').disabled = true;
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
  } finally {
    document.getElementById('run-btn').disabled = false;
  }
}

window.addEventListener('DOMContentLoaded', async () => {
  await loadDevices();
  initWorkspace();
  connectConsole();
  document.getElementById('run-btn').addEventListener('click', runScript);
  document.getElementById('refresh-devices-btn').addEventListener('click', loadDevices);
});
