"""Command-line interface for CodeSentry."""

import argparse
import fnmatch
import os
import sys
from typing import List

from . import __version__
from .analyzer import analyze_file
from .models import Issue, Severity
from .report import filter_by_severity, to_json, to_text


def _collect_python_files(path: str, exclude: List[str]) -> List[str]:
    if os.path.isfile(path):
        return [path] if path.endswith(".py") else []

    matched = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not _is_excluded(d, exclude)]
        for filename in files:
            if filename.endswith(".py") and not _is_excluded(filename, exclude):
                matched.append(os.path.join(root, filename))
    return sorted(matched)


def _is_excluded(name: str, patterns: List[str]) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codesentry",
        description="A lightweight static analysis CLI for Python codebases.",
    )
    parser.add_argument("--version", action="version", version=f"codesentry {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Scan a file or directory for issues.")
    scan.add_argument("path", help="File or directory to scan.")
    scan.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    scan.add_argument(
        "--severity",
        choices=["info", "warning", "error"],
        default="info",
        help="Minimum severity to report (default: info, i.e. show everything).",
    )
    scan.add_argument(
        "--exclude",
        action="append",
        default=["__pycache__", ".git", ".venv", "venv", "*.egg-info"],
        help="Glob pattern(s) of files/dirs to skip. Can be passed multiple times.",
    )
    scan.add_argument(
        "--fail-on",
        choices=["never", "warning", "error"],
        default="error",
        help="Exit with a non-zero status if issues at/above this severity are found "
        "(default: error). Use 'never' to always exit 0 -- useful for CI dry runs.",
    )
    return parser


def _exit_code(issues: List[Issue], fail_on: str) -> int:
    if fail_on == "never":
        return 0
    threshold = Severity(fail_on)
    return 1 if any(i.severity.rank() >= threshold.rank() for i in issues) else 0


def run_scan(args) -> int:
    files = _collect_python_files(args.path, args.exclude)
    if not files:
        print(f"No Python files found at '{args.path}'.", file=sys.stderr)
        return 0

    all_issues: List[Issue] = []
    for file_path in files:
        try:
            all_issues.extend(analyze_file(file_path))
        except SyntaxError as exc:
            all_issues.append(
                Issue(file_path, exc.lineno or 1, "CS000", Severity.ERROR, f"Syntax error: {exc.msg}")
            )

    filtered = filter_by_severity(all_issues, Severity(args.severity))
    filtered.sort(key=lambda i: (i.file, i.line))

    output = to_json(filtered) if args.format == "json" else to_text(filtered)
    print(output)

    return _exit_code(filtered, args.fail_on)


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        return run_scan(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
