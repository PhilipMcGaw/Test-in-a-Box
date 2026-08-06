(() => {
  'use strict';

  const quickCommands = [
    'ID', '*IDN?', '*OPT?', 'MODE', 'STATUS', '*STB?',
    'UA', 'IA', 'SB', 'MU', 'MI', 'OVP',
    'SB,S', 'GTR', 'MODE,UI', 'OVP,36',
    'UA,12', 'IA,1', 'SB,R',
  ];

  const commandHistory = [];
  let historyIndex = 0;

  const byId = id => document.getElementById(id);
  const terminal = byId('terminal');
  const commandInput = byId('command');
  const status = byId('status');

  function timestamp() {
    return new Date().toLocaleTimeString([], { hour12: false });
  }

  function append(direction, text) {
    terminal.textContent += `[${timestamp()}] ${direction} ${text}\n`;
    terminal.scrollTop = terminal.scrollHeight;
  }

  async function readJson(response) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }

  async function loadTargets() {
    const [devicesResponse, portsResponse] = await Promise.all([
      fetch('/api/protocol/devices', { cache: 'no-store' }),
      fetch('/api/serial_ports', { cache: 'no-store' }),
    ]);

    const devices = await readJson(devicesResponse) || [];
    const ports = await readJson(portsResponse) || [];

    const deviceSelect = byId('device');
    deviceSelect.innerHTML = '';

    for (const device of devices) {
      const option = document.createElement('option');
      option.value = device.device_id;
      option.textContent =
        `${device.device_id} — ${device.display_name}`;
      deviceSelect.appendChild(option);
    }

    if (!devices.length) {
      const option = document.createElement('option');
      option.value = '';
      option.textContent = 'No connected query-capable instruments';
      deviceSelect.appendChild(option);
    }

    const portSelect = byId('serial-port');
    portSelect.innerHTML = '';

    for (const port of ports) {
      const option = document.createElement('option');
      option.value = port.device;
      option.textContent = port.display_name || port.device;
      if (port.device.toUpperCase() === 'COM15') {
        option.selected = true;
      }
      portSelect.appendChild(option);
    }

    if (!ports.length) {
      const option = document.createElement('option');
      option.value = '';
      option.textContent = 'No COM ports found';
      portSelect.appendChild(option);
    }
  }

  function setMode() {
    const direct = byId('mode').value === 'serial';
    byId('serial-settings').hidden = !direct;
    byId('device-settings').hidden = direct;
  }

  function requestBody(command) {
    const mode = byId('mode').value;

    return {
      mode,
      command,
      expect_response: byId('expect-response').checked,
      device_id: byId('device').value || null,
      serial_port: byId('serial-port').value || null,
      baudrate: Number(byId('baudrate').value),
      data_bits: Number(byId('data-bits').value),
      parity: byId('parity').value,
      stop_bits: Number(byId('stop-bits').value),
      timeout: Number(byId('timeout').value),
      command_terminator: byId('command-terminator').value,
      reply_terminator: byId('reply-terminator').value,
    };
  }

  async function sendCommand() {
    const command = commandInput.value.trim();
    if (!command) {
      return;
    }

    commandHistory.push(command);
    historyIndex = commandHistory.length;
    append('TX >', command);
    status.textContent = 'Sending…';
    byId('send').disabled = true;

    try {
      const response = await fetch('/api/protocol/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody(command)),
      });

      const data = await readJson(response);

      if (!response.ok) {
        const message = data?.detail || `HTTP ${response.status}`;
        append('ERR!', message);
        status.textContent = message;
        return;
      }

      if (byId('expect-response').checked) {
        const reply = data.response || '<empty response>';
        append('RX <', reply);
      } else {
        append('OK  ', 'write-only command sent');
      }

      status.textContent =
        `Completed in ${Number(data.elapsed_seconds || 0).toFixed(3)} s`;
    } catch (error) {
      append('ERR!', error.message || String(error));
      status.textContent = error.message || String(error);
    } finally {
      byId('send').disabled = false;
      commandInput.focus();
      commandInput.select();
    }
  }

  function saveLog() {
    const blob = new Blob([terminal.textContent], {
      type: 'text/plain;charset=utf-8',
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    const stamp = new Date().toISOString().replaceAll(':', '-');
    anchor.href = url;
    anchor.download = `tiab-protocol-${stamp}.txt`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  for (const command of quickCommands) {
    const button = document.createElement('button');
    button.className = 'quick-command';
    button.textContent = command;
    button.addEventListener('click', () => {
      commandInput.value = command;
      commandInput.focus();
    });
    byId('quick-commands').appendChild(button);
  }

  byId('mode').addEventListener('change', setMode);
  byId('send').addEventListener('click', sendCommand);
  byId('clear-log').addEventListener('click', () => {
    terminal.textContent = '';
  });
  byId('save-log').addEventListener('click', saveLog);
  byId('copy-log').addEventListener('click', async () => {
    await navigator.clipboard.writeText(terminal.textContent);
    status.textContent = 'Session log copied.';
  });

  commandInput.addEventListener('keydown', event => {
    if (event.key === 'Enter') {
      event.preventDefault();
      sendCommand();
      return;
    }

    if (event.key === 'ArrowUp' && commandHistory.length) {
      event.preventDefault();
      historyIndex = Math.max(0, historyIndex - 1);
      commandInput.value = commandHistory[historyIndex];
    }

    if (event.key === 'ArrowDown' && commandHistory.length) {
      event.preventDefault();
      historyIndex = Math.min(
        commandHistory.length,
        historyIndex + 1
      );
      commandInput.value =
        historyIndex < commandHistory.length
          ? commandHistory[historyIndex]
          : '';
    }
  });

  setMode();
  loadTargets().catch(error => {
    status.textContent = `Could not load connections: ${error}`;
  });
  commandInput.focus();
})();
