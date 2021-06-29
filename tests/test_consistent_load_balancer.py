import pytest
import sortedcontainers
from sortedcontainers import SortedDict

from chord import consistent_load_balancer


@pytest.fixture(autouse=True)
def clear_server_list():
    consistent_load_balancer.servers = SortedDict()


def test_adding_server():
    keys = consistent_load_balancer.generate_keys(10)

    consistent_load_balancer.build_server_list(50)
    assert len(consistent_load_balancer.servers) == 50

    keys_to_servers1 = consistent_load_balancer.get_servers(keys)
    assert len(keys_to_servers1) == 10

    assert keys_to_servers1['cached_data_0'].name == 'server_51'
    assert keys_to_servers1['cached_data_1'].name == 'server_30'
    assert keys_to_servers1['cached_data_2'].name == 'server_46'
    assert keys_to_servers1['cached_data_3'].name == 'server_19'
    assert keys_to_servers1['cached_data_4'].name == 'server_44'
    assert keys_to_servers1['cached_data_5'].name == 'server_6'
    assert keys_to_servers1['cached_data_6'].name == 'server_27'
    assert keys_to_servers1['cached_data_7'].name == 'server_15'
    assert keys_to_servers1['cached_data_8'].name == 'server_24'
    assert keys_to_servers1['cached_data_9'].name == 'server_45'

    consistent_load_balancer.build_server_list(1)
    assert len(consistent_load_balancer.servers) == 51

    keys_to_servers2 = consistent_load_balancer.get_servers(keys)
    assert len(keys_to_servers2) == 10

    assert keys_to_servers2['cached_data_0'].name == 'server_51'
    assert keys_to_servers2['cached_data_1'].name == 'server_30'
    assert keys_to_servers2['cached_data_2'].name == 'server_46'
    assert keys_to_servers2['cached_data_3'].name == 'server_58'
    assert keys_to_servers2['cached_data_4'].name == 'server_44'
    assert keys_to_servers2['cached_data_5'].name == 'server_6'
    assert keys_to_servers2['cached_data_6'].name == 'server_27'
    assert keys_to_servers2['cached_data_7'].name == 'server_15'
    assert keys_to_servers2['cached_data_8'].name == 'server_24'
    assert keys_to_servers2['cached_data_9'].name == 'server_45'

    changes = consistent_load_balancer.calculate_change(keys_to_servers1, keys_to_servers2)
    assert len(changes) == 1
    assert changes[0] == 'cached_data_3'
