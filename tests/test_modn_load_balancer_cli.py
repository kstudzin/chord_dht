import io

import pytest

from chord import modn_load_balancer


@pytest.fixture(autouse=True)
def clear_server_list():
    modn_load_balancer.server_list = []


def test_50_orig_1_addtl():
    cmd = ['50', '10', '--additional', '1', '--no-formatting']
    expected = 'Mapping of keys to server hosting key with 50 servers:\n{"cached_data_0": {"name": "server_36"}, ' \
               '"cached_data_1": {"name": "server_5"}, "cached_data_2": {"name": "server_6"}, "cached_data_3": {' \
               '"name": "server_41"}, "cached_data_4": {"name": "server_39"}, "cached_data_5": {"name": "server_49"}, ' \
               '"cached_data_6": {"name": "server_12"}, "cached_data_7": {"name": "server_29"}, "cached_data_8": {' \
               '"name": "server_22"}, "cached_data_9": {"name": "server_49"}}\n\nMapping of keys to server hosting ' \
               'key with 51 servers:\n{"cached_data_0": {"name": "server_35"}, "cached_data_1": {"name": "server_4"}, ' \
               '"cached_data_2": {"name": "server_6"}, "cached_data_3": {"name": "server_39"}, "cached_data_4": {' \
               '"name": "server_35"}, "cached_data_5": {"name": "server_46"}, "cached_data_6": {"name": "server_10"}, ' \
               '"cached_data_7": {"name": "server_26"}, "cached_data_8": {"name": "server_21"}, "cached_data_9": {' \
               '"name": "server_45"}}\n\n A total of 9 out of 10 keys have changed hosts:\n["cached_data_0", ' \
               '"cached_data_1", "cached_data_3", "cached_data_4", "cached_data_5", "cached_data_6", "cached_data_7", ' \
               '"cached_data_8", "cached_data_9"]'
    actual = io.StringIO()

    modn_load_balancer.main(actual, cmd)
    assert actual.getvalue().strip() == expected
