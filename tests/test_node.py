import logging
from unittest import mock
from unittest.mock import Mock, patch

import pytest
import zmq
from pytest_mock import mocker

from chord.node import Node, Command, FindSuccessorCommand, ChordNode


@mock.patch('chord.node.zmq')
def test_init(mock_zmq):
    node = Node('node_0', 160, 'tcp://127.0.0.1')

    node.context.socket.assert_called()
    node.context.socket.assert_called()

    node.router.bind_to_random_port.assert_called_with('tcp://127.0.0.1')
    node.receiver.bind_to_random_port.assert_called_with('tcp://127.0.0.1')


@mock.patch('chord.node.zmq')
def test_init_fingers(mock_zmq):
    node = Node('node_0', 160, 'tcp://127.0.0.1')

    pair = Mock()
    pair.send.return_value = None
    pair.send_json.return_value = None
    pair.recv.return_value = Command.FIND_SUCCESSOR
    pair.recv_json.return_value = {'successor': 163, 'address': 'tcp://127.0.0.1:5555'}

    node._init_fingers(pair)

    results = zip(node.fingers, node.finger_addresses)
    for actual in results:
        assert actual == (163, 'tcp://127.0.0.1:5555')


@mock.patch('chord.node.zmq')
def test_find_successor_node(mock_zmq):
    node = Node('node_0', 160, 'tcp://127.0.0.1', None, '5555')
    node.successor = 30
    node.successor_address = 'tcp://127.0.0.1:5556'

    actual_found, actual_successor, actual_address, actual_hops = node.find_successor(0, 0)
    assert actual_found
    assert actual_successor == 30
    assert actual_address == 'tcp://127.0.0.1:5556'
    assert actual_hops == 1

    actual_found, actual_successor, actual_address, actual_hops = node.find_successor(50, 0)
    assert not actual_found
    assert actual_successor == 30
    assert actual_address == 'tcp://127.0.0.1:5556'
    assert actual_hops == 1

    actual_found, actual_successor, actual_address, actual_hops = node.find_successor(30, 0)
    assert actual_found
    assert actual_successor == 30
    assert actual_address == 'tcp://127.0.0.1:5556'
    assert actual_hops == 1

    actual_found, actual_successor, actual_address, actual_hops = node.find_successor(160, 0)
    assert actual_found
    assert actual_successor == 160
    assert actual_address == 'tcp://127.0.0.1:5555'
    assert actual_hops == 0


@mock.patch('chord.node.zmq')
def test_find_successor_chord_node(mock_zmq):
    node = ChordNode('node_0', 20, 'tcp://127.0.0.1', None, '5555')
    node.successor = 30
    node.successor_address = 'tcp://127.0.0.1:5556'
    node.fingers[0] = 30
    node.finger_addresses[0] = 'tcp://127.0.0.1:5556'
    node.fingers[1] = 30
    node.finger_addresses[1] = 'tcp://127.0.0.1:5556'
    node.fingers[2] = 30
    node.finger_addresses[2] = 'tcp://127.0.0.1:5556'
    node.fingers[3] = 30
    node.finger_addresses[3] = 'tcp://127.0.0.1:5556'
    node.fingers[4] = 35
    node.finger_addresses[4] = 'tcp://127.0.0.1:5557'
    node.fingers[5] = 40
    node.finger_addresses[5] = 'tcp://127.0.0.1:5558'
    node.fingers[6] = 100
    node.finger_addresses[6] = 'tcp://127.0.0.1:5559'
    node.fingers[7] = 140
    node.finger_addresses[7] = 'tcp://127.0.0.1:5510'

    actual_found, actual_successor, actual_address, actual_hops = node.find_successor(0, 0)
    assert not actual_found
    assert actual_successor == 140
    assert actual_address == 'tcp://127.0.0.1:5510'
    assert actual_hops == 1

    actual_found, actual_successor, actual_address, actual_hops = node.find_successor(50, 0)
    assert not actual_found
    assert actual_successor == 40
    assert actual_address == 'tcp://127.0.0.1:5558'
    assert actual_hops == 1

    actual_found, actual_successor, actual_address, actual_hops = node.find_successor(30, 0)
    assert actual_found
    assert actual_successor == 30
    assert actual_address == 'tcp://127.0.0.1:5556'
    assert actual_hops == 1

    actual_found, actual_successor, actual_address, actual_hops = node.find_successor(20, 0)
    assert actual_found
    assert actual_successor == 20
    assert actual_address == 'tcp://127.0.0.1:5555'
    assert actual_hops == 0
