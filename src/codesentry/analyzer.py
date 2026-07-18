"""AST-based static analysis rules for CodeSentry."""

import ast
import tokenize
from io import StringIO
from typing import List

from .models import Issue, Severity

MAX_FUNCTION_LINES = 50
TODO_KEYWORDS = ("TODO", "FIXME", "XXX", "HACK")


class _Visitor(ast.NodeVisitor):
    """Walks a module's AST and collects issues."""

    def __init__(self, filename: str, source_lines: List[str]):
        self.filename = filename
        self.source_lines = source_lines
        self.issues: List[Issue] = []
        self.imported_names = {}
        self.used_names = set()

    # -- helpers ---------------------------------------------------------
    def _add(self, node: ast.AST, rule_id: str, severity: Severity, message: str):
        line = getattr(node, "lineno", 1)
        self.issues.append(Issue(self.filename, line, rule_id, severity, message))

    # -- imports -----------------------------------------------------------
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            self.imported_names[name] = node
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            if alias.name == "*":
                continue
            name = alias.asname or alias.name
            self.imported_names[name] = node
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        # e.g. `os.path` -> mark `os` as used even though it appears as Name too,
        # this branch mainly exists for clarity / future extension.
        self.generic_visit(node)

    # -- functions ---------------------------------------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._check_mutable_defaults(node)
        self._check_function_length(node)
        self._check_missing_docstring(node)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def _check_mutable_defaults(self, node):
        mutable_types = (ast.List, ast.Dict, ast.Set)
        for default in list(node.args.defaults) + [
            d for d in node.args.kw_defaults if d is not None
        ]:
            if isinstance(default, mutable_types):
                self._add(
                    node,
                    "CS001",
                    Severity.ERROR,
                    f"Function '{node.name}' uses a mutable default argument.",
                )
                break

    def _check_function_length(self, node):
        if not node.body:
            return
        start = node.lineno
        end = max(
            getattr(n, "end_lineno", start) or start for n in ast.walk(node)
        )
        length = end - start
        if length > MAX_FUNCTION_LINES:
            self._add(
                node,
                "CS002",
                Severity.WARNING,
                f"Function '{node.name}' is {length} lines long "
                f"(limit {MAX_FUNCTION_LINES}); consider splitting it up.",
            )

    def _check_missing_docstring(self, node):
        if node.name.startswith("_"):
            return  # private/internal helpers are exempt
        if ast.get_docstring(node) is None:
            self._add(
                node,
                "CS003",
                Severity.INFO,
                f"Public function '{node.name}' is missing a docstring.",
            )

    # -- exception handling --------------------------------------------------
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.type is None:
            self._add(
                node,
                "CS004",
                Severity.ERROR,
                "Bare 'except:' clause catches all exceptions, including "
                "KeyboardInterrupt/SystemExit; catch a specific exception instead.",
            )
        elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
            self._add(
                node,
                "CS005",
                Severity.WARNING,
                "Catching the broad 'Exception' class can hide real bugs; "
                "prefer catching a specific exception type.",
            )
        self.generic_visit(node)

    # -- security-sensitive builtins ------------------------------------------
    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
            self._add(
                node,
                "CS006",
                Severity.ERROR,
                f"Use of '{node.func.id}()' can execute arbitrary code; "
                "avoid it or sandbox the input carefully.",
            )
        self.generic_visit(node)

    def unused_import_issues(self) -> List[Issue]:
        issues = []
        for name, node in self.imported_names.items():
            if name not in self.used_names:
                issues.append(
                    Issue(
                        self.filename,
                        node.lineno,
                        "CS007",
                        Severity.WARNING,
                        f"Imported name '{name}' appears unused.",
                    )
                )
        return issues


def _todo_comment_issues(filename: str, source: str) -> List[Issue]:
    issues = []
    try:
        tokens = tokenize.generate_tokens(StringIO(source).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                text = tok.string.lstrip("#").strip()
                for keyword in TODO_KEYWORDS:
                    if text.upper().startswith(keyword):
                        issues.append(
                            Issue(
                                filename,
                                tok.start[0],
                                "CS008",
                                Severity.INFO,
                                f"Unresolved '{keyword}' comment: {text}",
                            )
                        )
                        break
    except tokenize.TokenError:
        pass  # malformed source; ast.parse will already have raised for real syntax errors
    return issues


def analyze_source(filename: str, source: str) -> List[Issue]:
    """Run all rules against a single file's source and return found issues."""
    tree = ast.parse(source, filename=filename)
    visitor = _Visitor(filename, source.splitlines())
    visitor.visit(tree)
    issues = visitor.issues + visitor.unused_import_issues()
    issues += _todo_comment_issues(filename, source)
    return sorted(issues, key=lambda i: (i.line, i.rule_id))


def analyze_file(path: str) -> List[Issue]:
    with open(path, "r", encoding="utf-8") as fh:
        source = fh.read()
    return analyze_source(path, source)
