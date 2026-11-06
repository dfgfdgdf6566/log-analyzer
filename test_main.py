import pytest
import json
import os
from main import parse_line, main
import sys

# Тесты для парсера
def test_valid_line():
    line = "2024-05-01T12:00:00Z | INFO | auth | 200 | User logged in"
    event, err = parse_line(line, 1)
    assert err is None
    assert event["level"] == "INFO"

def test_invalid_format():
    line = "just a broken line"
    event, err = parse_line(line, 1)
    assert event is None
    assert "invalid format" in err

def test_invalid_timestamp():
    line = "2024-13-99T99:99:99Z | INFO | auth | 200 | Message"
    event, err = parse_line(line, 1)
    assert event is None
    assert "invalid timestamp" in err

def test_invalid_level():
    line = "2024-05-01T12:00:00Z | SUPER | auth | 200 | Message"
    event, err = parse_line(line, 1)
    assert event is None
    assert "invalid level" in err

def test_empty_fields():
    line = "2024-05-01T12:00:00Z | INFO |  | 200 | Message"
    event, err = parse_line(line, 1)
    assert event is None
    assert "empty fields" in err

# Тесты для CLI (создаем временный файл)
@pytest.fixture
def temp_log(tmp_path):
    log_file = tmp_path / "test.log"
    log_file.write_text(
        "2024-05-01T12:00:00Z | INFO | auth | 200 | Msg\n"
        "2024-05-01T12:10:00Z | ERROR | auth | 5001 | Err\n"
        "Broken line\n"
    )
    return str(log_file)

def test_cli_run(temp_log, capsys):
    sys.argv = ["main.py", "--input", temp_log]
    try:
        main()
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "Total lines: 3" in captured.out
    assert "Valid: 2, Invalid: 1" in captured.out

def test_cli_output_json(temp_log, tmp_path):
    out_file = tmp_path / "out.json"
    sys.argv = ["main.py", "--input", temp_log, "--output", str(out_file)]
    try:
        main()
    except SystemExit:
        pass
    assert os.path.exists(out_file)
    with open(out_file, 'r') as f:
        data = json.load(f)
        assert data["total_lines"] == 3
