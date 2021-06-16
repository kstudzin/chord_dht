from chord import modn_load_balancer, server


def test_adding_server():
    keys = modn_load_balancer.generate_keys(10)

    modn_load_balancer.build_server_list(50)
    assert len(modn_load_balancer.server_list) == 50

    keys_to_servers1 = modn_load_balancer.get_servers(keys)
    assert len(keys_to_servers1) == 10

    assert keys_to_servers1["cached_data_0"] == modn_load_balancer.server_list[36]
    assert keys_to_servers1["cached_data_1"] == modn_load_balancer.server_list[5]
    assert keys_to_servers1["cached_data_2"] == modn_load_balancer.server_list[6]
    assert keys_to_servers1["cached_data_3"] == modn_load_balancer.server_list[41]
    assert keys_to_servers1["cached_data_4"] == modn_load_balancer.server_list[39]
    assert keys_to_servers1["cached_data_5"] == modn_load_balancer.server_list[49]
    assert keys_to_servers1["cached_data_6"] == modn_load_balancer.server_list[12]
    assert keys_to_servers1["cached_data_7"] == modn_load_balancer.server_list[29]
    assert keys_to_servers1["cached_data_8"] == modn_load_balancer.server_list[22]
    assert keys_to_servers1["cached_data_9"] == modn_load_balancer.server_list[49]

    name = modn_load_balancer.server_name_fmt.format(id="51")
    modn_load_balancer.server_list.append(server.Server(name))
    assert len(modn_load_balancer.server_list) == 51

    keys_to_servers2 = modn_load_balancer.get_servers(keys)
    assert len(keys_to_servers2) == 10

    assert keys_to_servers2["cached_data_0"] == modn_load_balancer.server_list[35]
    assert keys_to_servers2["cached_data_1"] == modn_load_balancer.server_list[4]
    assert keys_to_servers2["cached_data_2"] == modn_load_balancer.server_list[6]
    assert keys_to_servers2["cached_data_3"] == modn_load_balancer.server_list[39]
    assert keys_to_servers2["cached_data_4"] == modn_load_balancer.server_list[35]
    assert keys_to_servers2["cached_data_5"] == modn_load_balancer.server_list[46]
    assert keys_to_servers2["cached_data_6"] == modn_load_balancer.server_list[10]
    assert keys_to_servers2["cached_data_7"] == modn_load_balancer.server_list[26]
    assert keys_to_servers2["cached_data_8"] == modn_load_balancer.server_list[21]
    assert keys_to_servers2["cached_data_9"] == modn_load_balancer.server_list[45]

    changes = modn_load_balancer.calculate_change(keys_to_servers1, keys_to_servers2)
    assert len(changes) == 9

    assert changes[0] == "cached_data_0"
    assert changes[1] == "cached_data_1"
    assert changes[2] == "cached_data_3"
    assert changes[3] == "cached_data_4"
    assert changes[4] == "cached_data_5"
    assert changes[5] == "cached_data_6"
    assert changes[6] == "cached_data_7"
    assert changes[7] == "cached_data_8"
    assert changes[8] == "cached_data_9"
