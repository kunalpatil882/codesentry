# CodeSentry

A lightweight, **dependency-free** static analysis CLI for Python codebases.
CodeSentry walks your source tree, parses each file's AST, and flags common
bugs and code-smells — no external linters required to run the core engine.

## Why

Most linters are heavyweight or opinionated about style. CodeSentry focuses
on a small set of rules that catch *real bugs*, not formatting nits, so it's
fast to run in CI and easy to extend with your own rules.

## Features

- Pure standard-library analysis engine (`ast` + `tokenize`) — no third-party
  runtime dependencies
- Detects:
  - `CS001` mutable default arguments
  - `CS002` overly long functions
  - `CS003` missing docstrings on public functions
  - `CS004` bare `except:` clauses
  - `CS005` overly broad `except Exception:` clauses
  - `CS006` use of `eval()` / `exec()`
  - `CS007` unused imports
  - `CS008` unresolved `TODO` / `FIXME` / `HACK` comments
- Text or JSON output (`--format`)
- Configurable severity threshold and CI-friendly exit codes (`--fail-on`)
- Exclude patterns for vendored/generated code
- Fully tested with `pytest`
- Ships with a `Dockerfile` and a GitHub Actions CI workflow

## Installation

```bash
git clone https://github.com/<your-username>/codesentry.git
cd codesentry
pip install -e .
```

For running the test suite as well:

```bash
pip install -e ".[dev]"
```

## Usage

Scan a file or a whole directory:

```bash
codesentry scan ./my_project
```

Example output:

```
my_project/utils.py:12: [ERROR] CS001 - Function 'add_items' uses a mutable default argument.
my_project/utils.py:20: [ERROR] CS004 - Bare 'except:' clause catches all exceptions...
my_project/api.py:5: [WARNING] CS007 - Imported name 'sys' appears unused.

Total: 3  (errors=2, warnings=1, info=0)
```

Other options:

```bash
# JSON output, e.g. for feeding into another tool
codesentry scan ./my_project --format json

# only show warnings and errors
codesentry scan ./my_project --severity warning

# skip test fixtures and migrations
codesentry scan . --exclude "test_*" --exclude "migrations"

# CI dry-run: never fail the build, just print findings
codesentry scan . --fail-on never
```

By default, `codesentry` exits with status `1` if any **error**-level issue is
found, which makes it easy to drop into a CI pipeline:

```yaml
- name: Static analysis
  run: codesentry scan src --fail-on error
```

## Running with Docker

```bash
docker build -t codesentry .
docker run --rm -v "$(pwd)":/workspace codesentry scan .
```

## Running the tests

```bash
pytest -v
```

## Project layout

```
codesentry/
├── src/codesentry/
│   ├── analyzer.py   # AST visitor + all detection rules
│   ├── cli.py        # argparse-based CLI, file discovery, exit codes
│   ├── models.py      # Issue / Severity data model
│   └── report.py      # text / JSON formatting
├── tests/
│   ├── fixtures/       # sample "bad" and "clean" Python files
│   ├── test_analyzer.py
│   └── test_cli.py
├── Dockerfile
└── .github/workflows/ci.yml
```

## Extending

Each rule is a small, independent method on the `_Visitor` class in
`analyzer.py`. To add a new rule:

1. Add a new `visit_<NodeType>` method (or extend an existing one).
2. Append an `Issue` with a new `CS0XX` rule ID and a `Severity`.
3. Add a fixture + test case in `tests/`.

## License

MIT — see [LICENSE](LICENSE).
