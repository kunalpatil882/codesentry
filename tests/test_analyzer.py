import os

import pytest

from codesentry.analyzer import analyze_file
from codesentry.models import Severity

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def bad_issues():
    return analyze_file(os.path.join(FIXTURES, "sample_bad.py"))


def test_detects_mutable_default(bad_issues):
    assert any(i.rule_id == "CS001" for i in bad_issues)


def test_detects_bare_except(bad_issues):
    assert any(i.rule_id == "CS004" for i in bad_issues)


def test_detects_eval_usage(bad_issues):
    assert any(i.rule_id == "CS006" for i in bad_issues)


def test_detects_unused_import(bad_issues):
    unused = [i for i in bad_issues if i.rule_id == "CS007"]
    assert any("sys" in i.message for i in unused)


def test_detects_todo_comment(bad_issues):
    assert any(i.rule_id == "CS008" for i in bad_issues)


def test_detects_missing_docstring(bad_issues):
    missing = [i for i in bad_issues if i.rule_id == "CS003"]
    assert any("public_helper" in i.message for i in missing)


def test_clean_file_has_no_errors():
    issues = analyze_file(os.path.join(FIXTURES, "sample_clean.py"))
    errors = [i for i in issues if i.severity == Severity.ERROR]
    assert errors == []


def test_syntax_error_raises():
    with pytest.raises(SyntaxError):
        analyze_file_from_source_should_raise()


def analyze_file_from_source_should_raise():
    from codesentry.analyzer import analyze_source

    analyze_source("bad.py", "def f(:\n    pass")
  
