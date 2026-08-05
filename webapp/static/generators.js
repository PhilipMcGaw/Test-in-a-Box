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

  const start = Number(block.getFieldValue('START'));
  const end = Number(block.getFieldValue('END'));
  const stepMagnitude = Math.abs(
    Number(block.getFieldValue('STEP'))
  );
  const dwellRaw = Number(block.getFieldValue('DWELL'));
  const dwellUnit = block.getFieldValue('DWELL_UNIT');

  const safeStep = (
    Number.isFinite(stepMagnitude) && stepMagnitude > 0
  ) ? stepMagnitude : 0.1;

  const dwellSeconds = dwellUnit === 'MS'
    ? dwellRaw / 1000
    : dwellRaw;

  const ascending = end >= start;
  const signedStep = ascending ? safeStep : -safeStep;
  const comparison = ascending ? '<=' : '>=';

  // A block-specific variable avoids collisions when multiple ramps are used
  // in the same procedure. Blockly block IDs may contain punctuation, so
  // normalise them into a valid Python identifier.
  const blockSuffix = String(block.id || 'voltage')
    .replace(/[^A-Za-z0-9_]/g, '_');
  const variable = `_tiab_ramp_voltage_${blockSuffix}`;

  return (
    `${variable} = ${start}\n` +
    `while ${variable} ${comparison} ${end}:\n` +
    `    set(${JSON.stringify(deviceId)}, ` +
    `${JSON.stringify(positionId)}, ${variable})\n` +
    `    wait(${dwellSeconds})\n` +
    `    ${variable} += ${signedStep}\n`
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
  const seconds = block.getFieldValue('SECONDS');
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
