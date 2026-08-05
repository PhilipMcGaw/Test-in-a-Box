# Relay Blockly Blocks

The Blockly toolbox now includes a **Relays** category.

Available blocks:

- **set relay** — turns one selected relay ON or OFF;
- **read relay state** — returns `true` for ON and `false` for OFF;
- **set relay bank** — turns every relay channel on a selected bank ON
  or OFF.

The lists are generated from connected-device capabilities, so the same
blocks work with the serial Seeit USB-RELAY08 driver, the native USBB
driver and future relay-controller drivers that expose positions named
`relay1`, `relay2`, and so on.

After applying the patch, restart Test in a Box and refresh the browser.
Use **Refresh devices** if relay choices are not immediately populated.
