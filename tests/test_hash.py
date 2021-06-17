import os
import pathlib
import subprocess

import pytest

from chord.hash import hash_value


@pytest.fixture(autouse=True)
def chdir():
    parent = pathlib.Path(__file__).parent.parent.absolute()
    chord = os.path.join(parent, 'chord')
    os.chdir(chord)


def run_cmd(cmd):
    actual = subprocess.check_output(cmd)
    return actual.decode('utf-8').strip()


def test_hash():
    assert hash_value("Hello, world!") == 108
    assert hash_value("FOO BAR 1234566789") == 129
    assert hash_value("Portland, OR") == 175
    assert hash_value("555-123-4567") == 202


def test_hash_cli():
    cmd = ["python", "hash.py", "Hello, world!"]
    expected = "Value \"Hello, world!\" has digest \"108\""

    actual = run_cmd(cmd)
    assert actual == expected
