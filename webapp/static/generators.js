/*
Generates Python that calls the flat functions set()/get()/wait()/log()/
assert_that() — these names are bound by the backend at run time to the
matching TestRunner methods (see server.py api_run()).

Blockly v10+ (we're on v13) registers per-block generator functions on
generator.forBlock['block_type'], not generator['block_type'] directly —
that's the piece that was missing before.
*/

Blockly.Python.forBlock['hw_set'] = function (block) {
  const posValue = block.getFieldValue('POSITION');
  const [deviceId, positionId] = posValue.split('|');
  const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  return `set(${JSON.stringify(deviceId)}, ${JSON.stringify(positionId)}, ${value})\n`;
};

Blockly.Python.forBlock['hw_get'] = function (block) {
  const posValue = block.getFieldValue('POSITION');
  const [deviceId, positionId] = posValue.split('|');
  const code = `get(${JSON.stringify(deviceId)}, ${JSON.stringify(positionId)})`;
  return [code, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python.forBlock['hw_wait'] = function (block) {
  const seconds = block.getFieldValue('SECONDS');
  return `wait(${seconds})\n`;
};

Blockly.Python.forBlock['hw_log'] = function (block) {
  const message = block.getFieldValue('MESSAGE');
  return `log(${JSON.stringify(message)})\n`;
};

Blockly.Python.forBlock['hw_assert'] = function (block) {
  const condition = Blockly.Python.valueToCode(block, 'CONDITION', Blockly.Python.ORDER_NONE) || 'True';
  const message = block.getFieldValue('MESSAGE');
  return `assert_that(${condition}, ${JSON.stringify(message)})\n`;
};

Blockly.Python.forBlock['hw_prompt'] = function (block) {
  const label = block.getFieldValue('LABEL');
  const dutUid = block.getFieldValue('DUT');
  return `ask_operator(${JSON.stringify(label)}, ${JSON.stringify(dutUid)})\n`;
};

Blockly.Python.forBlock['hw_within_tolerance'] = function (block) {
  const measured = Blockly.Python.valueToCode(block, 'MEASURED', Blockly.Python.ORDER_NONE) || '0';
  const target = Blockly.Python.valueToCode(block, 'TARGET', Blockly.Python.ORDER_NONE) || '0';
  const tolerance = Blockly.Python.valueToCode(block, 'TOLERANCE', Blockly.Python.ORDER_NONE) || '0';
  const code = `(abs((${measured}) - (${target})) <= (${tolerance}))`;
  return [code, Blockly.Python.ORDER_ATOMIC];
};
