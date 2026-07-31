/*
Generates Python that calls the flat functions set()/get()/wait()/log()/
assert_that() — these names are bound by the backend at run time to the
matching TestRunner methods (see server.py run_generated_code()).
*/

Blockly.Python['hw_set'] = function (block) {
  const posValue = block.getFieldValue('POSITION');
  const [deviceId, positionId] = posValue.split('|');
  const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  return `set(${JSON.stringify(deviceId)}, ${JSON.stringify(positionId)}, ${value})\n`;
};

Blockly.Python['hw_get'] = function (block) {
  const posValue = block.getFieldValue('POSITION');
  const [deviceId, positionId] = posValue.split('|');
  const code = `get(${JSON.stringify(deviceId)}, ${JSON.stringify(positionId)})`;
  return [code, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['hw_wait'] = function (block) {
  const seconds = block.getFieldValue('SECONDS');
  return `wait(${seconds})\n`;
};

Blockly.Python['hw_log'] = function (block) {
  const message = block.getFieldValue('MESSAGE');
  return `log(${JSON.stringify(message)})\n`;
};

Blockly.Python['hw_assert'] = function (block) {
  const condition = Blockly.Python.valueToCode(block, 'CONDITION', Blockly.Python.ORDER_NONE) || 'True';
  const message = block.getFieldValue('MESSAGE');
  return `assert_that(${condition}, ${JSON.stringify(message)})\n`;
};

Blockly.Python['hw_within_tolerance'] = function (block) {
  const measured = Blockly.Python.valueToCode(block, 'MEASURED', Blockly.Python.ORDER_NONE) || '0';
  const target = Blockly.Python.valueToCode(block, 'TARGET', Blockly.Python.ORDER_NONE) || '0';
  const tolerance = Blockly.Python.valueToCode(block, 'TOLERANCE', Blockly.Python.ORDER_NONE) || '0';
  const code = `(abs((${measured}) - (${target})) <= (${tolerance}))`;
  return [code, Blockly.Python.ORDER_ATOMIC];
};
