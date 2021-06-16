import os
import pathlib
import subprocess

import pytest


@pytest.fixture(autouse=True)
def chdir():
    parent = pathlib.Path(__file__).parent.parent.absolute()
    chord = os.path.join(parent, 'chord')
    os.chdir(chord)


def run_cmd(cmd, expected):
    actual = subprocess.check_output(cmd)
    return actual.decode('utf-8').strip()


def test_50_orig_1_addtl():
    cmd = ['python', 'modn_load_balancer.py', '50', '10', '--additional', '1', '--no-formatting']
    expected = "Mapping of keys to server hosting key with 50 servers:\n{'cached_data_0': server_36, 'cached_data_1': " \
               "server_5, 'cached_data_2': server_6, 'cached_data_3': server_41, 'cached_data_4': server_39, " \
               "'cached_data_5': server_49, 'cached_data_6': server_12, 'cached_data_7': server_29, 'cached_data_8': " \
               "server_22, 'cached_data_9': server_49}\n\nMapping of keys to server hosting key with 51 servers:\n{" \
               "'cached_data_0': server_35, 'cached_data_1': server_4, 'cached_data_2': server_6, 'cached_data_3': " \
               "server_39, 'cached_data_4': server_35, 'cached_data_5': server_46, 'cached_data_6': server_10, " \
               "'cached_data_7': server_26, 'cached_data_8': server_21, 'cached_data_9': server_45}\n\n A total of 9 " \
               "out of 10 keys have changed hosts:\n['cached_data_0', 'cached_data_1', 'cached_data_3', " \
               "'cached_data_4', 'cached_data_5', 'cached_data_6', 'cached_data_7', 'cached_data_8', 'cached_data_9']"

    actual = run_cmd(cmd, expected)
    assert actual == expected
