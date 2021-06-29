import io
import pytest

from sortedcontainers import SortedDict
from chord import consistent_load_balancer


@pytest.fixture(autouse=True)
def clear_server_list():
    consistent_load_balancer.servers = SortedDict()
    consistent_load_balancer.max_server_id = 0


def test_50_orig_1_addtl():
    cmd = ['50', '10', '--additional', '1', '--no-formatting']
    expected = 'Mapping of keys to server hosting key with 50 servers:\n{"cached_data_0": {"name": "server_51"}, ' \
               '"cached_data_1": {"name": "server_30"}, "cached_data_2": {"name": "server_46"}, "cached_data_3": {' \
               '"name": "server_19"}, "cached_data_4": {"name": "server_44"}, "cached_data_5": {"name": "server_6"}, ' \
               '"cached_data_6": {"name": "server_27"}, "cached_data_7": {"name": "server_15"}, "cached_data_8": {' \
               '"name": "server_24"}, "cached_data_9": {"name": "server_45"}}\n\nMapping of keys to server hosting ' \
               'key with 51 servers:\n{"cached_data_0": {"name": "server_51"}, "cached_data_1": {"name": ' \
               '"server_30"}, "cached_data_2": {"name": "server_46"}, "cached_data_3": {"name": "server_58"}, ' \
               '"cached_data_4": {"name": "server_44"}, "cached_data_5": {"name": "server_6"}, "cached_data_6": {' \
               '"name": "server_27"}, "cached_data_7": {"name": "server_15"}, "cached_data_8": {"name": "server_24"}, ' \
               '"cached_data_9": {"name": "server_45"}}\n\n A total of 1 out of 10 keys have changed hosts:\n[' \
               '"cached_data_3"]'
    actual = io.StringIO()

    consistent_load_balancer.main(actual, cmd)
    assert actual.getvalue().strip() == expected
