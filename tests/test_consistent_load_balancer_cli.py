import os
import pathlib
import subprocess

import pytest


@pytest.fixture(autouse=True)
def chdir():
    parent = pathlib.Path(__file__).parent.parent.absolute()
    chord = os.path.join(parent, 'chord')
    os.chdir(chord)


def run_cmd(cmd):
    actual = subprocess.check_output(cmd)
    return actual.decode('utf-8').strip()


def test_50_orig_1_addtl():
    cmd = ['python', 'consistent_load_balancer.py', '50', '10', '--additional', '1', '--no-formatting']
    expected = "Mapping of keys to server hosting key with 50 servers:\n{'cached_data_0': server_51, 'cached_data_1': " \
               "server_30, 'cached_data_2': server_46, 'cached_data_3': server_19, 'cached_data_4': server_44, " \
               "'cached_data_5': server_6, 'cached_data_6': server_27, 'cached_data_7': server_15, 'cached_data_8': " \
               "server_24, 'cached_data_9': server_45}\n\nMapping of keys to server hosting key with 51 servers:\n{" \
               "'cached_data_0': server_51, 'cached_data_1': server_30, 'cached_data_2': server_46, 'cached_data_3': " \
               "server_58, 'cached_data_4': server_44, 'cached_data_5': server_6, 'cached_data_6': server_27, " \
               "'cached_data_7': server_15, 'cached_data_8': server_24, 'cached_data_9': server_45}\n\n A total of 1 " \
               "out of 10 keys have changed hosts:\n['cached_data_3']"

    actual = run_cmd(cmd)
    print(actual)
    assert actual == expected
