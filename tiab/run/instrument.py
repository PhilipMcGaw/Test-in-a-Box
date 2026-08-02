"""
Inserts a `_checkpoint("<statement>")` call before every statement in the
generated script — including inside for/while loops and if-blocks — so
Pause/Step/Stop can take effect between any two Blockly blocks, not just
at the top level.

This works on the generated Python's AST rather than touching the Blockly
code generators, so it applies uniformly no matter what block shapes get
added to the toolbox later.
"""

from __future__ import annotations

import ast


class _CheckpointInserter(ast.NodeTransformer):
    def __init__(self):
        self._loop_counter = 0

    def _instrument(self, body: list[ast.stmt]) -> list[ast.stmt]:
        new_body = []
        for stmt in body:
            new_body.append(self._make_checkpoint(stmt))
            new_body.append(stmt)
        return new_body

    @staticmethod
    def _make_checkpoint(stmt: ast.stmt) -> ast.stmt:
        try:
            label = ast.unparse(stmt).strip().splitlines()[0].rstrip(":").strip()
        except Exception:
            label = f"line {getattr(stmt, 'lineno', '?')}"
        if len(label) > 80:
            label = label[:77] + "..."
        call = ast.Expr(value=ast.Call(
            func=ast.Name(id="_checkpoint", ctx=ast.Load()),
            args=[ast.Constant(value=label)],
            keywords=[],
        ))
        ast.copy_location(call, stmt)
        ast.fix_missing_locations(call)
        return call

    def _next_counter_name(self) -> str:
        self._loop_counter += 1
        return f"_iter_{self._loop_counter}"

    @staticmethod
    def _loop_label(node: ast.AST) -> str:
        try:
            label = ast.unparse(node).splitlines()[0].rstrip(":").strip()
        except Exception:
            label = f"loop at line {getattr(node, 'lineno', '?')}"
        if len(label) > 60:
            label = label[:57] + "..."
        return label

    def _wrap_loop_with_counter(self, node) -> list[ast.stmt]:
        """
        Prepends a counter init before the loop and an increment + progress
        report as the very first thing inside the loop body, so Pause/Step/
        the console can show which iteration is currently running.
        """
        counter_name = self._next_counter_name()
        label = self._loop_label(node)

        init_stmt = ast.Assign(
            targets=[ast.Name(id=counter_name, ctx=ast.Store())],
            value=ast.Constant(value=0),
        )
        increment_stmt = ast.AugAssign(
            target=ast.Name(id=counter_name, ctx=ast.Store()),
            op=ast.Add(),
            value=ast.Constant(value=1),
        )
        report_stmt = ast.Expr(value=ast.Call(
            func=ast.Name(id="_report_iteration", ctx=ast.Load()),
            args=[ast.Constant(value=label), ast.Name(id=counter_name, ctx=ast.Load())],
            keywords=[],
        ))
        for stmt in (init_stmt, increment_stmt, report_stmt):
            ast.copy_location(stmt, node)
        ast.fix_missing_locations(init_stmt)
        ast.fix_missing_locations(increment_stmt)
        ast.fix_missing_locations(report_stmt)

        # increment + report go before the (already-instrumented) body statements
        node.body = [increment_stmt, report_stmt] + node.body
        return [init_stmt, node]

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
    """Parse `source` and return an AST with checkpoints inserted throughout."""
    tree = ast.parse(source)
    tree = _CheckpointInserter().visit(tree)
    ast.fix_missing_locations(tree)
    return tree
