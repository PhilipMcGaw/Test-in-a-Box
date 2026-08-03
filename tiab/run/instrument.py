"""
Instrument Blockly-generated Python with pause, step and stop checkpoints.

A ``_checkpoint("<statement>")`` call is inserted before every generated
statement, including statements inside loops and conditional branches. This
allows Pause, Step and Stop requests to take effect between Blockly blocks
without requiring every Blockly generator to implement control handling.

Loop counters and progress reports are also inserted so the execution console
can show which iteration is currently running.
"""

from __future__ import annotations

import ast


class _CheckpointInserter(ast.NodeTransformer):
    """Insert execution checkpoints and loop-iteration reporting."""

    def __init__(self) -> None:
        self._loop_counter = 0

    def _instrument(self, body: list[ast.stmt]) -> list[ast.stmt]:
        """Insert a checkpoint immediately before each statement."""
        instrumented: list[ast.stmt] = []

        for statement in body:
            instrumented.append(self._make_checkpoint(statement))
            instrumented.append(statement)

        return instrumented

    @staticmethod
    def _statement_label(statement: ast.stmt) -> str:
        """Create a short, readable label for a generated statement."""
        try:
            label = ast.unparse(statement).strip().splitlines()[0]
            label = label.rstrip(":").strip()
        except Exception:
            label = f"statement at line {getattr(statement, 'lineno', '?')}"

        if len(label) > 80:
            label = label[:77] + "..."

        return label

    @classmethod
    def _make_checkpoint(cls, statement: ast.stmt) -> ast.stmt:
        checkpoint = ast.Expr(
            value=ast.Call(
                func=ast.Name(id="_checkpoint", ctx=ast.Load()),
                args=[ast.Constant(value=cls._statement_label(statement))],
                keywords=[],
            )
        )
        ast.copy_location(checkpoint, statement)
        return checkpoint

    def _next_counter_name(self) -> str:
        """
        Return a generated counter name unlikely to clash with Blockly variables.

        A single leading underscore is used because the generated-code validator
        reserves double-underscore names.
        """
        self._loop_counter += 1
        return f"_tiab_iter_{self._loop_counter}"

    @staticmethod
    def _loop_label(node: ast.AST) -> str:
        """Create a short, readable label for a loop."""
        try:
            label = ast.unparse(node).splitlines()[0].rstrip(":").strip()
        except Exception:
            label = f"loop at line {getattr(node, 'lineno', '?')}"

        if len(label) > 60:
            label = label[:57] + "..."

        return label

    def _wrap_loop_with_counter(
        self,
        node: ast.For | ast.While,
    ) -> list[ast.stmt]:
        """
        Add a counter initialisation before a loop and an iteration report at
        the beginning of each loop body.
        """
        counter_name = self._next_counter_name()
        label = self._loop_label(node)

        initialise = ast.Assign(
            targets=[ast.Name(id=counter_name, ctx=ast.Store())],
            value=ast.Constant(value=0),
        )

        increment = ast.AugAssign(
            target=ast.Name(id=counter_name, ctx=ast.Store()),
            op=ast.Add(),
            value=ast.Constant(value=1),
        )

        report = ast.Expr(
            value=ast.Call(
                func=ast.Name(
                    id="_report_iteration",
                    ctx=ast.Load(),
                ),
                args=[
                    ast.Constant(value=label),
                    ast.Name(id=counter_name, ctx=ast.Load()),
                ],
                keywords=[],
            )
        )

        for statement in (initialise, increment, report):
            ast.copy_location(statement, node)

        # The loop body has already been recursively instrumented.
        node.body = [increment, report, *node.body]

        return [initialise, node]

    def visit_Module(self, node: ast.Module) -> ast.Module:
        self.generic_visit(node)
        node.body = self._instrument(node.body)
        return node

    def visit_For(self, node: ast.For) -> list[ast.stmt]:
        self.generic_visit(node)
        node.body = self._instrument(node.body)
        return self._wrap_loop_with_counter(node)

    def visit_While(self, node: ast.While) -> list[ast.stmt]:
        self.generic_visit(node)
        node.body = self._instrument(node.body)
        return self._wrap_loop_with_counter(node)

    def visit_If(self, node: ast.If) -> ast.If:
        self.generic_visit(node)
        node.body = self._instrument(node.body)

        if node.orelse:
            node.orelse = self._instrument(node.orelse)

        return node


def instrument_source(source: str) -> ast.Module:
    """
    Parse generated Python and return an AST instrumented for run control.

    Syntax validation and restriction of permitted operations are handled by
    the server before execution.
    """
    tree = ast.parse(source, mode="exec")
    instrumented = _CheckpointInserter().visit(tree)
    ast.fix_missing_locations(instrumented)

    if not isinstance(instrumented, ast.Module):
        raise TypeError("instrumented source did not produce a module")

    return instrumented
