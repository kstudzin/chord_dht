import os.path
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


def test_100_naive_hops():
    cmd = ["python", "node.py", "100", "100", '--naive', '--action', 'hops']
    expected = "Average hops with 100 nodes is 48.43"

    actual = run_cmd(cmd, expected)
    assert actual == expected


def test_50_naive_hops():
    cmd = ["python", "node.py", "50", "100", '--naive', '--action', 'hops']
    expected = "Average hops with 50 nodes is 26.48"

    actual = run_cmd(cmd, expected)
    assert actual == expected


def test_100_chord_hops():
    cmd = ["python", "node.py", "100", "100", '--chord', '--action', 'hops']
    expected = "Average hops with 100 nodes is 4.12"

    actual = run_cmd(cmd, expected)
    assert actual == expected


def test_50_chord_hops():
    cmd = ["python", "node.py", "50", "100", '--chord', '--action', 'hops']
    expected = "Average hops with 50 nodes is 3.69"

    actual = run_cmd(cmd, expected)
    assert actual == expected


def test_naive_network():
    cmd = ["python", "node.py", "10", "100", '--naive', '--action', 'network', '--no-formatting']
    expected = "Nodes in the network: \n" \
               "{'network': [{'id': 24, 'name': 'node_3'}, {'id': 32, 'name': 'node_2'}, " \
               "{'id': 46, 'name': 'node_6'}, {'id': 109, 'name': 'node_4'}, {'id': 145, 'name': 'node_8'}, " \
               "{'id': 150, 'name': 'node_7'}, {'id': 160, 'name': 'node_0'}, {'id': 163, 'name': 'node_1'}, " \
               "{'id': 241, 'name': 'node_9'}, {'id': 244, 'name': 'node_5'}]}"

    actual = run_cmd(cmd, expected)
    assert actual == expected


def test_chord_network():
    cmd = ["python", "node.py", "10", "100", '--chord', '--action', 'network', '--no-formatting']
    expected = "Nodes in the network: \n" \
               "{'network': [{'id': 24, 'name': 'node_3'}, {'id': 32, 'name': 'node_2'}, " \
               "{'id': 46, 'name': 'node_6'}, {'id': 109, 'name': 'node_4'}, {'id': 145, 'name': 'node_8'}, " \
               "{'id': 150, 'name': 'node_7'}, {'id': 160, 'name': 'node_0'}, {'id': 163, 'name': 'node_1'}, " \
               "{'id': 241, 'name': 'node_9'}, {'id': 244, 'name': 'node_5'}]}"

    actual = run_cmd(cmd, expected)
    assert actual == expected


def test_naive_fingers():
    cmd = ["python", "node.py", "10", "100", '--naive', '--action', 'fingers', '--no-formatting']
    expected = "Finger table for node \"node_3\": \n" \
               "{'name': 'node_3', 'id': 24, 'fingers': [{'position': 0, 'id': 32, " \
               "'name': 'node_2'}, {'position': 1, 'id': 32, 'name': 'node_2'}, {'position': 2, 'id': 32, " \
               "'name': 'node_2'}, {'position': 3, 'id': 32, 'name': 'node_2'}, {'position': 4, 'id': 46, " \
               "'name': 'node_6'}, {'position': 5, 'id': 109, 'name': 'node_4'}, {'position': 6, 'id': 109, " \
               "'name': 'node_4'}, {'position': 7, 'id': 160, 'name': 'node_0'}]}\n" \
               "Finger table for node \"node_5\": \n" \
               "{" \
               "'name': 'node_5', 'id': 244, 'fingers': [{'position': 0, 'id': 24, 'name': 'node_3'}, {'position': 1, " \
               "'id': 24, 'name': 'node_3'}, {'position': 2, 'id': 24, 'name': 'node_3'}, {'position': 3, 'id': 24, " \
               "'name': 'node_3'}, {'position': 4, 'id': 24, 'name': 'node_3'}, {'position': 5, 'id': 24, " \
               "'name': 'node_3'}, {'position': 6, 'id': 109, 'name': 'node_4'}, {'position': 7, 'id': 145, " \
               "'name': 'node_8'}]}"

    actual = run_cmd(cmd, expected)
    assert actual == expected


def test_chord_fingers():
    cmd = ["python", "node.py", "10", "100", '--chord', '--action', 'fingers', '--no-formatting']
    expected = "Finger table for node \"node_3\": \n" \
               "{'name': 'node_3', 'id': 24, 'fingers': [{'position': 0, 'id': 32, " \
               "'name': 'node_2'}, {'position': 1, 'id': 32, 'name': 'node_2'}, {'position': 2, 'id': 32, " \
               "'name': 'node_2'}, {'position': 3, 'id': 32, 'name': 'node_2'}, {'position': 4, 'id': 46, " \
               "'name': 'node_6'}, {'position': 5, 'id': 109, 'name': 'node_4'}, {'position': 6, 'id': 109, " \
               "'name': 'node_4'}, {'position': 7, 'id': 160, 'name': 'node_0'}]}\n" \
               "Finger table for node \"node_5\": \n" \
               "{" \
               "'name': 'node_5', 'id': 244, 'fingers': [{'position': 0, 'id': 24, 'name': 'node_3'}, {'position': 1, " \
               "'id': 24, 'name': 'node_3'}, {'position': 2, 'id': 24, 'name': 'node_3'}, {'position': 3, 'id': 24, " \
               "'name': 'node_3'}, {'position': 4, 'id': 24, 'name': 'node_3'}, {'position': 5, 'id': 24, " \
               "'name': 'node_3'}, {'position': 6, 'id': 109, 'name': 'node_4'}, {'position': 7, 'id': 145, " \
               "'name': 'node_8'}]}"

    actual = run_cmd(cmd, expected)
    assert actual == expected
