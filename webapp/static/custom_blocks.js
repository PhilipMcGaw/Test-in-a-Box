/*
Custom blocks for the hardware test app. Device/position dropdown lists are
populated at page load from GET /api/devices (see app.js), so the toolbox
always reflects whatever's in config.json — no need to edit this file when
you add a new instrument, only when you want a genuinely new *kind* of
block (a new shape, not just a new device).
*/

// Populated by app.js after fetching /api/devices.
// Shape: [["psu1: Set Voltage", "psu1|voltage"], ["relay1: Relay 1", "relay1|relay1"], ...]
window.HW_OUTPUT_POSITIONS = [["(no devices found)", "none|none"]];
window.HW_INPUT_POSITIONS = [["(no devices found)", "none|none"]];

Blockly.Blocks['hw_set'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("set")
      .appendField(new Blockly.FieldDropdown(() => window.HW_OUTPUT_POSITIONS), "POSITION")
      .appendField("to");
    this.appendValueInput("VALUE").setCheck(null);
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(210);
    this.setTooltip("Write a value to an output position (PSU voltage, relay channel, etc.)");
  }
};

Blockly.Blocks['hw_get'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("read")
      .appendField(new Blockly.FieldDropdown(() => window.HW_INPUT_POSITIONS), "POSITION");
    this.setOutput(true, null);
    this.setColour(210);
    this.setTooltip("Read a value from an input position (a measurement).");
  }
};

Blockly.Blocks['hw_wait'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("wait")
      .appendField(new Blockly.FieldNumber(1, 0), "SECONDS")
      .appendField("seconds");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(65);
  }
};

Blockly.Blocks['hw_log'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("log message")
      .appendField(new Blockly.FieldTextInput("note"), "MESSAGE");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(65);
  }
};

Blockly.Blocks['hw_assert'] = {
  init: function () {
    this.appendValueInput("CONDITION")
      .setCheck(null)
      .appendField("assert");
    this.appendDummyInput()
      .appendField("message")
      .appendField(new Blockly.FieldTextInput("check passed"), "MESSAGE");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(0);
    this.setTooltip("Record a pass/fail check in the report. Stops the script on failure.");
  }
};

// Populated by app.js after fetching /api/duts.
window.HW_DUTS = [["(no DUTs configured)", "none"]];

Blockly.Blocks['hw_prompt'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("ask operator for")
      .appendField(new Blockly.FieldTextInput("Serial Number"), "LABEL")
      .appendField("and record for DUT")
      .appendField(new Blockly.FieldDropdown(() => window.HW_DUTS), "DUT");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(290);
    this.setTooltip("Pauses the run and prompts the operator for a value (e.g. a serial number), then records it against the chosen DUT for the report.");
  }
};

Blockly.Blocks['hw_within_tolerance'] = {
  init: function () {
    this.appendValueInput("MEASURED").setCheck(null).appendField("is");
    this.appendValueInput("TARGET").setCheck(null).appendField("within");
    this.appendValueInput("TOLERANCE").setCheck(null).appendField("of");
    this.setInputsInline(true);
    this.setOutput(true, "Boolean");
    this.setColour(0);
    this.setTooltip("True if |measured - target| <= tolerance.");
  }
};
