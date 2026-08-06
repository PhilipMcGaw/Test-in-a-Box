/*
Python generators for Test in a Box Blockly blocks.

Generated procedures call the flat execution functions supplied by server.py:
set(), get(), wait(), log(), assert_that() and ask_operator().
*/


function splitPosition(block, fieldName = 'POSITION') {
  const raw = block.getFieldValue(fieldName) || 'none|none';
  const separator = raw.indexOf('|');

  if (separator < 0) {
    return ['none', 'none'];
  }

  return [
    raw.slice(0, separator),
    raw.slice(separator + 1),
  ];
}


Blockly.Python.forBlock['hw_set'] = function (block) {
  const [deviceId, positionId] = splitPosition(block);
  const value = Blockly.Python.valueToCode(
    block,
    'VALUE',
    Blockly.Python.ORDER_NONE
  ) || '0';

  return (
    `set(${JSON.stringify(deviceId)}, ` +
    `${JSON.stringify(positionId)}, ${value})\n`
  );
};


Blockly.Python.forBlock['hw_get'] = function (block) {
  const [deviceId, positionId] = splitPosition(block);
  const code =
    `get(${JSON.stringify(deviceId)}, ${JSON.stringify(positionId)})`;

  return [code, Blockly.Python.ORDER_ATOMIC];
};


// ---------------------------------------------------------------------------
// PSU blocks
// ---------------------------------------------------------------------------

Blockly.Python.forBlock['hw_psu_set_voltage'] = function (block) {
  const [deviceId, positionId] = splitPosition(block);
  const value = Blockly.Python.valueToCode(
    block,
    'VALUE',
    Blockly.Python.ORDER_NONE
  ) || '0';

  return (
    `set(${JSON.stringify(deviceId)}, ` +
    `${JSON.stringify(positionId)}, ${value})\n`
  );
};


Blockly.Python.forBlock['hw_psu_set_current'] = function (block) {
  const [deviceId, positionId] = splitPosition(block);
  const value = Blockly.Python.valueToCode(
    block,
    'VALUE',
    Blockly.Python.ORDER_NONE
  ) || '0';

  return (
    `set(${JSON.stringify(deviceId)}, ` +
    `${JSON.stringify(positionId)}, ${value})\n`
  );
};


Blockly.Python.forBlock['hw_psu_output'] = function (block) {
  const [deviceId, positionId] = splitPosition(block);
  const enabled = block.getFieldValue('STATE') === 'ON'
    ? 'True'
    : 'False';

  return (
    `set(${JSON.stringify(deviceId)}, ` +
    `${JSON.stringify(positionId)}, ${enabled})\n`
  );
};


Blockly.Python.forBlock['hw_psu_read_voltage'] = function (block) {
  const [deviceId, positionId] = splitPosition(block);
  const code =
    `get(${JSON.stringify(deviceId)}, ${JSON.stringify(positionId)})`;

  return [code, Blockly.Python.ORDER_ATOMIC];
};


Blockly.Python.forBlock['hw_psu_read_current'] = function (block) {
  const [deviceId, positionId] = splitPosition(block);
  const code =
    `get(${JSON.stringify(deviceId)}, ${JSON.stringify(positionId)})`;

  return [code, Blockly.Python.ORDER_ATOMIC];
};


Blockly.Python.forBlock['hw_psu_ramp_voltage'] = function (block) {
  const [deviceId, positionId] = splitPosition(block);

  const start = Blockly.Python.valueToCode(
    block,
    'START',
    Blockly.Python.ORDER_NONE
  ) || '0';
  const end = Blockly.Python.valueToCode(
    block,
    'END',
    Blockly.Python.ORDER_NONE
  ) || '12';
  const step = Blockly.Python.valueToCode(
    block,
    'STEP',
    Blockly.Python.ORDER_NONE
  ) || '0.1';
  const dwell = Blockly.Python.valueToCode(
    block,
    'DWELL',
    Blockly.Python.ORDER_NONE
  ) || '100';
  const dwellUnit = block.getFieldValue('DWELL_UNIT');

  const blockSuffix = String(block.id || 'voltage')
    .replace(/[^A-Za-z0-9_]/g, '_');

  const startVar = `_tiab_ramp_start_${blockSuffix}`;
  const endVar = `_tiab_ramp_end_${blockSuffix}`;
  const stepVar = `_tiab_ramp_step_${blockSuffix}`;
  const dwellVar = `_tiab_ramp_dwell_${blockSuffix}`;
  const valueVar = `_tiab_ramp_voltage_${blockSuffix}`;

  const dwellExpression = dwellUnit === 'MS'
    ? `((${dwell}) / 1000)`
    : `(${dwell})`;

  return (
    `${startVar} = (${start})\n` +
    `${endVar} = (${end})\n` +
    `${stepVar} = abs((${step}))\n` +
    `${dwellVar} = ${dwellExpression}\n` +
    `if ${stepVar} <= 0:\n` +
    `    ${stepVar} = 0.1\n` +
    `${valueVar} = ${startVar}\n` +
    `if ${endVar} >= ${startVar}:\n` +
    `    while ${valueVar} <= ${endVar}:\n` +
    `        set(${JSON.stringify(deviceId)}, ` +
    `${JSON.stringify(positionId)}, ${valueVar})\n` +
    `        wait(${dwellVar})\n` +
    `        ${valueVar} += ${stepVar}\n` +
    `else:\n` +
    `    while ${valueVar} >= ${endVar}:\n` +
    `        set(${JSON.stringify(deviceId)}, ` +
    `${JSON.stringify(positionId)}, ${valueVar})\n` +
    `        wait(${dwellVar})\n` +
    `        ${valueVar} -= ${stepVar}\n`
  );
};

// ---------------------------------------------------------------------------
// Relay blocks
// ---------------------------------------------------------------------------

Blockly.Python.forBlock['hw_relay_set'] = function (block) {
  const [deviceId, positionId] = splitPosition(block);
  const enabled = block.getFieldValue('STATE') === 'ON'
    ? 'True'
    : 'False';

  return (
    `set(${JSON.stringify(deviceId)}, ` +
    `${JSON.stringify(positionId)}, ${enabled})\n`
  );
};


Blockly.Python.forBlock['hw_relay_read'] = function (block) {
  const [deviceId, positionId] = splitPosition(block);
  const code =
    `get(${JSON.stringify(deviceId)}, ${JSON.stringify(positionId)})`;

  return [code, Blockly.Python.ORDER_ATOMIC];
};


Blockly.Python.forBlock['hw_relay_all'] = function (block) {
  const raw = block.getFieldValue('BANK') ||
    '{"deviceId":"none","positions":[]}';
  const enabled = block.getFieldValue('STATE') === 'ON'
    ? 'True'
    : 'False';

  let bank;
  try {
    bank = JSON.parse(raw);
  } catch (error) {
    bank = { deviceId: 'none', positions: [] };
  }

  return (bank.positions || []).map(positionId =>
    `set(${JSON.stringify(bank.deviceId)}, ` +
    `${JSON.stringify(positionId)}, ${enabled})\n`
  ).join('');
};


// ---------------------------------------------------------------------------
// Timing, results and checks
// ---------------------------------------------------------------------------

Blockly.Python.forBlock['hw_wait'] = function (block) {
  const seconds = Blockly.Python.valueToCode(
    block,
    'SECONDS',
    Blockly.Python.ORDER_NONE
  ) || '1';

  return `wait(${seconds})\n`;
};


Blockly.Python.forBlock['hw_log'] = function (block) {
  const label = block.getFieldValue('MESSAGE') || 'Value';
  const value = Blockly.Python.valueToCode(
    block,
    'VALUE',
    Blockly.Python.ORDER_NONE
  );

  // Preserve old saved message-only log blocks.
  if (!value) {
    return `log(${JSON.stringify(label)})\n`;
  }

  return `log(${JSON.stringify(label)}, ${value})\n`;
};


Blockly.Python.forBlock['hw_assert'] = function (block) {
  const condition = Blockly.Python.valueToCode(
    block,
    'CONDITION',
    Blockly.Python.ORDER_NONE
  ) || 'True';
  const message = block.getFieldValue('MESSAGE');

  return (
    `assert_that(${condition}, ${JSON.stringify(message)})\n`
  );
};


Blockly.Python.forBlock['hw_prompt'] = function (block) {
  const label = block.getFieldValue('LABEL');
  const dutUid = block.getFieldValue('DUT');

  return (
    `ask_operator(${JSON.stringify(label)}, ` +
    `${JSON.stringify(dutUid)})\n`
  );
};


Blockly.Python.forBlock['hw_within_tolerance'] = function (block) {
  const measured = Blockly.Python.valueToCode(
    block,
    'MEASURED',
    Blockly.Python.ORDER_NONE
  ) || '0';
  const target = Blockly.Python.valueToCode(
    block,
    'TARGET',
    Blockly.Python.ORDER_NONE
  ) || '0';
  const tolerance = Blockly.Python.valueToCode(
    block,
    'TOLERANCE',
    Blockly.Python.ORDER_NONE
  ) || '0';

  const code =
    `(abs((${measured}) - (${target})) <= (${tolerance}))`;

  return [code, Blockly.Python.ORDER_ATOMIC];
};
