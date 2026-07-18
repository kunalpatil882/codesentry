import json
import os

from codesentry.cli import main

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_scan_text_output(capsys):
    exit_code = main(["scan", os.path.join(FIXTURES, "sample_bad.py"), "--fail-on", "never"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "CS001" in captured.out


def test_scan_json_output_is_valid(capsys):
    main(["scan", os.path.join(FIXTURES, "sample_bad.py"), "--format", "json", "--fail-on", "never"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert any(issue["rule_id"] == "CS006" for issue in data)


def test_fail_on_error_sets_exit_code():
    exit_code = main(["scan", os.path.join(FIXTURES, "sample_bad.py"), "--fail-on", "error"])
    assert exit_code == 1


def test_clean_file_exits_zero():
    exit_code = main(["scan", os.path.join(FIXTURES, "sample_clean.py"), "--fail-on", "error"])
    assert exit_code == 0


def test_missing_path_does_not_crash(capsys):
    exit_code = main(["scan", "/no/such/path.py", "--fail-on", "never"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "No Python files found" in captured.err
