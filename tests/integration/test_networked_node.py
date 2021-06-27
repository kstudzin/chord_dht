import logging
import threading
import time

import zmq

from chord.hash import hash_value, NUM_BITS
from chord.node import Node, RoutingInfo


def test_join():
    name1 = 'node_0'
    digest1 = hash_value(name1)
    node1 = Node(name1, digest1, 'tcp://127.0.0.1', '5500', '5501')

    name2 = 'node_1'
    digest2 = hash_value(name2)
    node2 = Node(name2, digest2, 'tcp://127.0.0.1', '5502', '5503')

    node1_t = threading.Thread(target=node1.run, args=[None, None], daemon=True)
    node1_t.start()

    joined = node2.join(node1.digest_id, node1.internal_endpoint)
    assert joined == 1

    v_node1 = node1.virtual_nodes[digest1]
    v_node2 = node2.virtual_nodes[digest2]

    logging.info('Test join')
    assert v_node1.fingers == [None] * NUM_BITS
    assert v_node1.successor == RoutingInfo(160, 160, 'tcp://127.0.0.1:5501')
    assert v_node1.predecessor == RoutingInfo(160, 160, 'tcp://127.0.0.1:5501')

    assert v_node2.fingers == [None] * NUM_BITS
    assert v_node2.successor == RoutingInfo(160, 160, 'tcp://127.0.0.1:5501')
    assert v_node2.predecessor == RoutingInfo(163, 163, 'tcp://127.0.0.1:5503')

    node2_t = threading.Thread(target=node2.run, args=[None, None], daemon=True)
    node2_t.start()

    logging.info('Running stabilize for node 2')
    stabilize_pair2 = node2.context.socket(zmq.PAIR)
    stabilize_pair2.connect(node2.stabilize_address)
    node2._stabilize(stabilize_pair2)

    # The last step of stabilize finishes asynchronously,
    # so wait until it is likely complete
    time.sleep(.5)

    logging.info('Test stabilize node 2')
    assert v_node1.successor == RoutingInfo(160, 160, 'tcp://127.0.0.1:5501')
    assert v_node1.predecessor == RoutingInfo(163, 163, 'tcp://127.0.0.1:5503')

    assert v_node2.successor == RoutingInfo(160, 160, 'tcp://127.0.0.1:5501')
    assert v_node2.predecessor == RoutingInfo(163, 163, 'tcp://127.0.0.1:5503')

    stabilize_pair1 = node1.context.socket(zmq.PAIR)
    stabilize_pair1.connect(node1.stabilize_address)
    node1._stabilize(stabilize_pair1)

    # The last step of stabilize finishes asynchronously,
    # so wait until it is likely complete
    time.sleep(.5)

    logging.info('Test stabilize node 1')
    assert v_node1.successor == RoutingInfo(163, 163, 'tcp://127.0.0.1:5503')
    assert v_node1.predecessor == RoutingInfo(163, 163, 'tcp://127.0.0.1:5503')

    assert v_node2.successor == RoutingInfo(160, 160, 'tcp://127.0.0.1:5501')
    assert v_node2.predecessor == RoutingInfo(160, 160, 'tcp://127.0.0.1:5501')

    fix_pair1 = node1.context.socket(zmq.PAIR)
    fix_pair1.connect(node1.fix_fingers_address)
    node1._init_fingers(fix_pair1)

    fix_pair2 = node2.context.socket(zmq.PAIR)
    fix_pair2.connect(node2.fix_fingers_address)
    node2._init_fingers(fix_pair2)

    logging.info('Test final state')
    assert v_node1.fingers == [RoutingInfo(163, 163, 'tcp://127.0.0.1:5503'),
                               RoutingInfo(163, 163, 'tcp://127.0.0.1:5503'),
                               RoutingInfo(160, 160, 'tcp://127.0.0.1:5501'),
                               RoutingInfo(160, 160, 'tcp://127.0.0.1:5501'),
                               RoutingInfo(160, 160, 'tcp://127.0.0.1:5501'),
                               RoutingInfo(160, 160, 'tcp://127.0.0.1:5501'),
                               RoutingInfo(160, 160, 'tcp://127.0.0.1:5501'),
                               RoutingInfo(160, 160, 'tcp://127.0.0.1:5501')]

    assert v_node2.fingers == [RoutingInfo(160, 160, 'tcp://127.0.0.1:5501'),
                               RoutingInfo(160, 160, 'tcp://127.0.0.1:5501'),
                               RoutingInfo(160, 160, 'tcp://127.0.0.1:5501'),
                               RoutingInfo(160, 160, 'tcp://127.0.0.1:5501'),
                               RoutingInfo(160, 160, 'tcp://127.0.0.1:5501'),
                               RoutingInfo(160, 160, 'tcp://127.0.0.1:5501'),
                               RoutingInfo(160, 160, 'tcp://127.0.0.1:5501'),
                               RoutingInfo(160, 160, 'tcp://127.0.0.1:5501')]

    name3 = 'node_2'
    digest3 = hash_value(name3)
    node3 = Node(name3, digest3, 'tcp://127.0.0.1', '5504', '5505')

    joined = node3.join(node1.digest_id, node1.internal_endpoint)
    assert joined == 1

    v_node3 = node3.virtual_nodes[digest3]
    assert v_node3.fingers == [None] * NUM_BITS
    assert v_node3.successor == RoutingInfo(160, 160, 'tcp://127.0.0.1:5501')
    assert v_node3.predecessor == RoutingInfo(32, 32, 'tcp://127.0.0.1:5505')

    node3_t = threading.Thread(target=node3.run, args=[None, None], daemon=True)
    node3_t.start()

    logging.info('Running stabilize for node 3')
    stabilize_pair3 = node3.context.socket(zmq.PAIR)
    stabilize_pair3.connect(node3.stabilize_address)
    node3._stabilize(stabilize_pair3)

    # The last step of stabilize finishes asynchronously,
    # so wait until it is likely complete
    time.sleep(.5)

    assert v_node1.successor == RoutingInfo(163, 163, 'tcp://127.0.0.1:5503')
    assert v_node1.predecessor == RoutingInfo(32, 32, 'tcp://127.0.0.1:5505')
    assert v_node2.successor == RoutingInfo(160, 160, 'tcp://127.0.0.1:5501')
    assert v_node2.predecessor == RoutingInfo(160, 160, 'tcp://127.0.0.1:5501')
    assert v_node3.successor == RoutingInfo(160, 160, 'tcp://127.0.0.1:5501')
    assert v_node3.predecessor == RoutingInfo(32, 32, 'tcp://127.0.0.1:5505')

    logging.info('Calling stabilize')
    node2._stabilize(stabilize_pair2)

    # The last step of stabilize finishes asynchronously,
    # so wait until it is likely complete
    time.sleep(.5)

    assert v_node1.successor == RoutingInfo(163, 163, 'tcp://127.0.0.1:5503')
    assert v_node1.predecessor == RoutingInfo(32, 32, 'tcp://127.0.0.1:5505')
    assert v_node2.successor == RoutingInfo(32, 32, 'tcp://127.0.0.1:5505')
    assert v_node2.predecessor == RoutingInfo(160, 160, 'tcp://127.0.0.1:5501')
    assert v_node3.successor == RoutingInfo(160, 160, 'tcp://127.0.0.1:5501')
    assert v_node3.predecessor == RoutingInfo(163, 163, 'tcp://127.0.0.1:5503')


def test_stabilize():
    # TODO - verify this runs the same in other environments
    # Unclear if the dependencies between the dict and the order in which the stabilization
    # happens will be the same in another environemnt

    v_nodes = {'v_node_53': 53,
               'v_node_234': 234,
               'v_node_172': 172}
    node = Node('node_0', 160, 'tcp://127.0.0.1', '5556', '5555', v_nodes)
    node.create()

    node1_t = threading.Thread(target=node.run, args=[None, None], daemon=True)
    node1_t.start()

    stabilize_pair = node.context.socket(zmq.PAIR)
    stabilize_pair.connect(node.stabilize_address)
    node._stabilize(stabilize_pair)
    time.sleep(.5)

    v_node = node.virtual_nodes[160]
    assert v_node.successor.digest == 172
    assert v_node.predecessor.digest == 160

    v_node = node.virtual_nodes[172]
    assert v_node.successor.digest == 234
    assert v_node.predecessor.digest == 160

    v_node = node.virtual_nodes[234]
    assert v_node.successor.digest == 53
    assert v_node.predecessor.digest == 172

    v_node = node.virtual_nodes[53]
    assert v_node.successor.digest == 234
    assert v_node.predecessor.digest == 234

    node._stabilize(stabilize_pair)
    time.sleep(.5)

    v_node = node.virtual_nodes[160]
    assert v_node.successor.digest == 172
    assert v_node.predecessor.digest == 160

    v_node = node.virtual_nodes[172]
    assert v_node.successor.digest == 234
    assert v_node.predecessor.digest == 160

    v_node = node.virtual_nodes[234]
    assert v_node.successor.digest == 53
    assert v_node.predecessor.digest == 172

    v_node = node.virtual_nodes[53]
    assert v_node.successor.digest == 172       # changed
    assert v_node.predecessor.digest == 234

    node._stabilize(stabilize_pair)
    time.sleep(.5)

    v_node = node.virtual_nodes[160]
    assert v_node.successor.digest == 172
    assert v_node.predecessor.digest == 53      # changed

    v_node = node.virtual_nodes[172]
    assert v_node.successor.digest == 234
    assert v_node.predecessor.digest == 160

    v_node = node.virtual_nodes[234]
    assert v_node.successor.digest == 53
    assert v_node.predecessor.digest == 172

    v_node = node.virtual_nodes[53]
    assert v_node.successor.digest == 160       # changed
    assert v_node.predecessor.digest == 234

    # Ensure nothing changes
    node._stabilize(stabilize_pair)
    time.sleep(.5)

    v_node = node.virtual_nodes[160]
    assert v_node.successor.digest == 172
    assert v_node.predecessor.digest == 53

    v_node = node.virtual_nodes[172]
    assert v_node.successor.digest == 234
    assert v_node.predecessor.digest == 160

    v_node = node.virtual_nodes[234]
    assert v_node.successor.digest == 53
    assert v_node.predecessor.digest == 172

    v_node = node.virtual_nodes[53]
    assert v_node.successor.digest == 160
    assert v_node.predecessor.digest == 234
