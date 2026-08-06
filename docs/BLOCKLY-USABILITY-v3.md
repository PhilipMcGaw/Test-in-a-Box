# Blockly Usability v3

Blockly procedures support fast block duplication.

## Right-click duplication

Blockly's standard **Duplicate** context-menu action remains available for
duplicatable blocks and connected stacks.

## Keyboard shortcut

Press:

```text
Ctrl+D
```

On macOS, use:

```text
Command+D
```

The selected block or connected stack is duplicated. Values, child blocks,
comments, collapsed state and disabled state are preserved by Blockly's
native copy/paste representation.

The duplicated block is selected and appears offset from the original.

When no suitable block is selected, the shortcut deliberately does
nothing. It does not show a dialog, write to the console or play an error.
The shortcut is also ignored while typing in text boxes, selects or
editable fields.
