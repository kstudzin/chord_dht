import pytest

from unittest import mock
from unittest.mock import Mock, patch

from chord.hash import NUM_BITS
from chord.node import Node, ChordNode, RoutingInfo, VirtualNode


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

    node._fix_fingers(pair)
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


@mock.patch('chord.node.zmq')
def test_virtual_nodes(mock_zmq):
    v_nodes = {'v_node_0': 1,
               'v_node_1': 2}
    node = Node('node_0', 160, 'tcp://127.0.0.1', '5556', '5555', v_nodes)

    assert node.digest_id == 160
    assert len(node.virtual_nodes) == 3

    v_node = node.virtual_nodes[160]
    assert v_node.get_digest() == 160
    assert v_node.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.get_parent() == 160
    assert v_node.successor.get_digest() == 160
    assert v_node.successor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.successor.get_parent() == 160
    assert v_node.predecessor.get_digest() == 160
    assert v_node.predecessor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.predecessor.get_parent() == 160

    v_node = node.virtual_nodes[1]
    assert v_node.get_digest() == 1
    assert v_node.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.get_parent() == 160
    assert v_node.successor.get_digest() == 1
    assert v_node.successor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.successor.get_parent() == 160
    assert v_node.predecessor.get_digest() == 1
    assert v_node.predecessor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.predecessor.get_parent() == 160

    v_node = node.virtual_nodes[2]
    assert v_node.get_digest() == 2
    assert v_node.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.get_parent() == 160
    assert v_node.successor.get_digest() == 2
    assert v_node.successor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.successor.get_parent() == 160
    assert v_node.predecessor.get_digest() == 2
    assert v_node.predecessor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.predecessor.get_parent() == 160

@mock.patch('chord.node.zmq')
def test_virtual_nodes(mock_zmq):
    v_nodes = {'v_node_0': 1,
               'v_node_1': 2}
    node = Node('node_0', 160, 'tcp://127.0.0.1', '5556', '5555', v_nodes)

    assert node.digest_id == 160
    assert len(node.virtual_nodes) == 3

    v_node = node.virtual_nodes[160]
    assert v_node.get_digest() == 160
    assert v_node.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.get_parent() == 160
    assert v_node.successor.get_digest() == 160
    assert v_node.successor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.successor.get_parent() == 160
    assert v_node.predecessor.get_digest() == 160
    assert v_node.predecessor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.predecessor.get_parent() == 160

    v_node = node.virtual_nodes[1]
    assert v_node.get_digest() == 1
    assert v_node.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.get_parent() == 160
    assert v_node.successor.get_digest() == 1
    assert v_node.successor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.successor.get_parent() == 160
    assert v_node.predecessor.get_digest() == 1
    assert v_node.predecessor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.predecessor.get_parent() == 160

    v_node = node.virtual_nodes[2]
    assert v_node.get_digest() == 2
    assert v_node.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.get_parent() == 160
    assert v_node.successor.get_digest() == 2
    assert v_node.successor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.successor.get_parent() == 160
    assert v_node.predecessor.get_digest() == 2
    assert v_node.predecessor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.predecessor.get_parent() == 160


@mock.patch('chord.node.zmq')
def test_chord_virtual_nodes(mock_zmq):
    v_nodes = {'v_node_0': 1,
               'v_node_1': 2}
    node = ChordNode('node_0', 160, 'tcp://127.0.0.1', '5556', '5555', v_nodes)

    assert node.digest_id == 160
    assert len(node.virtual_nodes) == 3

    v_node = node.virtual_nodes[160]
    assert v_node.get_digest() == 160
    assert v_node.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.get_parent() == 160
    assert v_node.successor.get_digest() == 160
    assert v_node.successor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.successor.get_parent() == 160
    assert v_node.predecessor.get_digest() == 160
    assert v_node.predecessor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.predecessor.get_parent() == 160

    v_node = node.virtual_nodes[1]
    assert v_node.get_digest() == 1
    assert v_node.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.get_parent() == 160
    assert v_node.successor.get_digest() == 1
    assert v_node.successor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.successor.get_parent() == 160
    assert v_node.predecessor.get_digest() == 1
    assert v_node.predecessor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.predecessor.get_parent() == 160

    v_node = node.virtual_nodes[2]
    assert v_node.get_digest() == 2
    assert v_node.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.get_parent() == 160
    assert v_node.successor.get_digest() == 2
    assert v_node.successor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.successor.get_parent() == 160
    assert v_node.predecessor.get_digest() == 2
    assert v_node.predecessor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.predecessor.get_parent() == 160


@mock.patch('chord.node.zmq')
def test_create(mock_zmq):
    v_nodes = {'v_node_53': 53,
               'v_node_234': 234,
               'v_node_172': 172}
    node = Node('node_0', 160, 'tcp://127.0.0.1', '5556', '5555', v_nodes)
    node.create()

    assert node.digest_id == 160
    assert len(node.virtual_nodes) == 4

    v_node = node.virtual_nodes[160]
    assert v_node.get_digest() == 160
    assert v_node.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.get_parent() == 160
    assert v_node.successor.get_digest() == 234
    assert v_node.successor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.successor.get_parent() == 160
    assert v_node.predecessor.get_digest() == 160
    assert v_node.predecessor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.predecessor.get_parent() == 160

    v_node = node.virtual_nodes[53]
    assert v_node.get_digest() == 53
    assert v_node.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.get_parent() == 160
    assert v_node.successor.get_digest() == 234
    assert v_node.successor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.successor.get_parent() == 160
    assert v_node.predecessor.get_digest() == 53
    assert v_node.predecessor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.predecessor.get_parent() == 160

    v_node = node.virtual_nodes[172]
    assert v_node.get_digest() == 172
    assert v_node.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.get_parent() == 160
    assert v_node.successor.get_digest() == 234
    assert v_node.successor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.successor.get_parent() == 160
    assert v_node.predecessor.get_digest() == 172
    assert v_node.predecessor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.predecessor.get_parent() == 160

    v_node = node.virtual_nodes[234]
    assert v_node.get_digest() == 234
    assert v_node.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.get_parent() == 160
    assert v_node.successor.get_digest() == 53
    assert v_node.successor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.successor.get_parent() == 160
    assert v_node.predecessor.get_digest() == 234
    assert v_node.predecessor.get_address() == 'tcp://127.0.0.1:5555'
    assert v_node.predecessor.get_parent() == 160


def test_next_finger_key():
    v_node = VirtualNode('vnode_1', 10, 235, 'tcp://127.0.0.1:5555')

    next_key = v_node.next_finger_key()
    assert next(next_key) == 11
    assert next(next_key) == 12
    assert next(next_key) == 14
    assert next(next_key) == 18
    assert next(next_key) == 26
    assert next(next_key) == 42
    assert next(next_key) == 74
    assert next(next_key) == 138

    with pytest.raises(StopIteration):
        next(next_key)


