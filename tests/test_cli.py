from typer.testing import CliRunner
from laya_api.cli import app

runner = CliRunner()

def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout

def test_cli_doctor():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "System & Hardware Diagnostic" in result.stdout
    assert "Platform" in result.stdout
    assert "Detected Backend" in result.stdout
