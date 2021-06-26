import logging
from unittest import mock
from unittest.mock import Mock, patch

import pytest
import zmq
from pytest_mock import mocker

from chord.hash import NUM_BITS
from chord.node import Node, Command, FindSuccessorCommand, ChordNode, RoutingInfo


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
    pair.send_pyobj.return_value = None
    pair.recv_pyobj.return_value = {'successor': 163, 'address': 'tcp://127.0.0.1:5555'}

    node._init_fingers(pair)
    assert node.virtual_nodes[160].fingers == [None] * NUM_BITS


@mock.patch('chord.node.zmq')
def test_find_successor_node(mock_zmq):
    node = Node('node_0', 160, 'tcp://127.0.0.1', None, '5555')
    v_node = node.virtual_nodes[160]
    v_node.successor = RoutingInfo(30, 45, 'tcp://127.0.0.1:5556')

    actual_found, actual_successor, actual_hops = v_node.find_successor(0, 0)
    assert actual_found
    assert actual_successor == RoutingInfo(30, 45, 'tcp://127.0.0.1:5556')
    assert actual_hops == 1

    actual_found, actual_successor, actual_hops = v_node.find_successor(50, 0)
    assert not actual_found
    assert actual_successor == RoutingInfo(30, 45, 'tcp://127.0.0.1:5556')
    assert actual_hops == 1

    actual_found, actual_successor, actual_hops = v_node.find_successor(30, 0)
    assert actual_found
    assert actual_successor == RoutingInfo(30, 45, 'tcp://127.0.0.1:5556')
    assert actual_hops == 1

    actual_found, actual_successor, actual_hops = v_node.find_successor(160, 0)
    assert actual_found
    assert actual_successor == RoutingInfo(160, 160, 'tcp://127.0.0.1:5555')
    assert actual_hops == 0


@mock.patch('chord.node.zmq')
def test_find_successor_chord_node(mock_zmq):
    digest = 20
    node = ChordNode('node_0', digest, 'tcp://127.0.0.1', None, '5555')
    v_node = node.virtual_nodes[digest]
    v_node.successor = RoutingInfo(30, 45, 'tcp://127.0.0.1:5556')
    v_node.fingers[0] = RoutingInfo(30, 45, 'tcp://127.0.0.1:5556')
    v_node.fingers[1] = RoutingInfo(30, 45, 'tcp://127.0.0.1:5556')
    v_node.fingers[2] = RoutingInfo(30, 45, 'tcp://127.0.0.1:5556')
    v_node.fingers[3] = RoutingInfo(30, 45, 'tcp://127.0.0.1:5556')
    v_node.fingers[4] = RoutingInfo(35, 200, 'tcp://127.0.0.1:5556')
    v_node.fingers[5] = RoutingInfo(40, 13, 'tcp://127.0.0.1:5556')
    v_node.fingers[6] = RoutingInfo(100, 100, 'tcp://127.0.0.1:5556')
    v_node.fingers[7] = RoutingInfo(140, 45, 'tcp://127.0.0.1:5556')


    actual_found, actual_successor, actual_hops = v_node.find_successor(0, 0)
    assert not actual_found
    assert actual_successor == RoutingInfo(140, 45, 'tcp://127.0.0.1:5556')
    assert actual_hops == 1

    actual_found, actual_successor, actual_hops = v_node.find_successor(50, 0)
    assert not actual_found
    assert actual_successor == RoutingInfo(40, 13, 'tcp://127.0.0.1:5556')
    assert actual_hops == 1

    actual_found, actual_successor, actual_hops = v_node.find_successor(30, 0)
    assert actual_found
    assert actual_successor == RoutingInfo(30, 45, 'tcp://127.0.0.1:5556')
    assert actual_hops == 1

    actual_found, actual_successor, actual_hops = v_node.find_successor(20, 0)
    assert actual_found
    assert actual_successor == v_node.routing_info
    assert actual_hops == 0
