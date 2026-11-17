import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_account_cli_modules_import_without_prompting():
    script = r'''
import builtins
import getpass

def unexpected_prompt(*args, **kwargs):
    raise AssertionError("import unexpectedly prompted for credentials")

builtins.input = unexpected_prompt
getpass.getpass = unexpected_prompt
import create_admin
import create_staff
'''
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
