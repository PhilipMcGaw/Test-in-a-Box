# ADR 0002: Use capability-based hardware abstraction

**Status:** Accepted

Blockly requests capabilities from logical roles. Drivers translate them into
SCPI, serial, USB, DLL or other operations. Tests do not contain vendor commands.
