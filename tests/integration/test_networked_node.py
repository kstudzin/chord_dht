import logging
import threading
import time

import zmq

from chord.hash import hash_value, NUM_BITS
from chord.node import Node


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
    assert joined

    logging.info('Test join')
    assert node1.fingers == [None] * NUM_BITS
    assert node1.finger_addresses == [None] * NUM_BITS
    assert node1.successor == 160
    assert node1.successor_address == 'tcp://127.0.0.1:5501'
    assert node1.predecessor is None
    assert node1.predecessor_address is None

    assert node2.fingers == [None] * NUM_BITS
    assert node2.finger_addresses == [None] * NUM_BITS
    assert node2.successor == 160
    assert node2.successor_address == 'tcp://127.0.0.1:5501'
    assert node2.predecessor is None
    assert node2.predecessor_address is None

    node2_t = threading.Thread(target=node2.run, args=[None, None], daemon=True)
    node2_t.start()

    logging.info('Running stabilize for node 2')
    pair = node2.context.socket(zmq.PAIR)
    pair.connect(node2.stabilize_address)
    node2._stabilize(pair)

    # The last step of stabilize finishes asynchronously,
    # so wait until it is likely complete
    time.sleep(.5)

    logging.info('Test stabilize node 2')
    assert node1.fingers == [None] * NUM_BITS
    assert node1.finger_addresses == [None] * NUM_BITS
    assert node1.successor == 163
    assert node1.successor_address == 'tcp://127.0.0.1:5503'
    assert node1.predecessor == 163
    assert node1.predecessor_address == 'tcp://127.0.0.1:5503'

    assert node2.fingers == [None] * NUM_BITS
    assert node2.finger_addresses == [None] * NUM_BITS
    assert node2.successor == 160
    assert node2.successor_address == 'tcp://127.0.0.1:5501'
    assert node2.predecessor is None
    assert node2.predecessor_address is None

    pair = node1.context.socket(zmq.PAIR)
    pair.connect(node1.stabilize_address)
    node1._stabilize(pair)

    # The last step of stabilize finishes asynchronously,
    # so wait until it is likely complete
    time.sleep(.5)

    logging.info('Test stabilize node3')
    assert node1.fingers == [None] * NUM_BITS
    assert node1.finger_addresses == [None] * NUM_BITS
    assert node1.successor == 163
    assert node1.successor_address == 'tcp://127.0.0.1:5503'
    assert node1.predecessor == 163
    assert node1.predecessor_address == 'tcp://127.0.0.1:5503'

    assert node2.fingers == [None] * NUM_BITS
    assert node2.finger_addresses == [None] * NUM_BITS
    assert node2.successor == 160
    assert node2.successor_address == 'tcp://127.0.0.1:5501'
    assert node2.predecessor == 160
    assert node2.predecessor_address == 'tcp://127.0.0.1:5501'

    fix_pair1 = node1.context.socket(zmq.PAIR)
    fix_pair1.connect(node1.fix_fingers_address)
    node1._init_fingers(fix_pair1)

    fix_pair2 = node2.context.socket(zmq.PAIR)
    fix_pair2.connect(node2.fix_fingers_address)
    node2._init_fingers(fix_pair2)

    logging.info('Test final state')
    assert node1.fingers == [163, 163, 160, 160, 160, 160, 160, 160]
    assert node1.finger_addresses == ['tcp://127.0.0.1:5503',
                                      'tcp://127.0.0.1:5503',
                                      'tcp://127.0.0.1:5501',
                                      'tcp://127.0.0.1:5501',
                                      'tcp://127.0.0.1:5501',
                                      'tcp://127.0.0.1:5501',
                                      'tcp://127.0.0.1:5501',
                                      'tcp://127.0.0.1:5501']
    assert node1.successor == 163
    assert node1.successor_address == 'tcp://127.0.0.1:5503'
    assert node1.predecessor == 163
    assert node1.predecessor_address == 'tcp://127.0.0.1:5503'

    assert node2.fingers == [160, 160, 160, 160, 160, 160, 160, 160]
    assert node2.finger_addresses == ['tcp://127.0.0.1:5501',
                                      'tcp://127.0.0.1:5501',
                                      'tcp://127.0.0.1:5501',
                                      'tcp://127.0.0.1:5501',
                                      'tcp://127.0.0.1:5501',
                                      'tcp://127.0.0.1:5501',
                                      'tcp://127.0.0.1:5501',
                                      'tcp://127.0.0.1:5501']
    assert node2.successor == 160
    assert node2.successor_address == 'tcp://127.0.0.1:5501'
    assert node2.predecessor == 160
    assert node2.predecessor_address == 'tcp://127.0.0.1:5501'
