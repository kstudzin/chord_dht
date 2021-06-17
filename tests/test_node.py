import math

from chord.node import run_experiment, Node, ChordNode, build_nodes
from chord.util import generate_keys


def test_naive_hops():
    keys = generate_keys(100, 'data')

    nodes = build_nodes(50, Node, 'node')
    avg_hops = run_experiment(nodes, keys)
    assert math.isclose(avg_hops, 26.48, abs_tol=0.01)

    nodes = build_nodes(100, Node, 'node')
    avg_hops = run_experiment(nodes, keys)
    assert math.isclose(avg_hops, 48.43, abs_tol=0.01)


def test_chord_hops():
    keys = generate_keys(100, 'data')

    nodes = build_nodes(50, ChordNode, 'node')
    avg_hops = run_experiment(nodes, keys)
    assert math.isclose(avg_hops, 3.69, abs_tol=0.01)

    nodes = build_nodes(100, ChordNode, 'node')
    avg_hops = run_experiment(nodes, keys)
    assert math.isclose(avg_hops, 4.12, abs_tol=0.01)


def test_node_creation():
    nodes = build_nodes(10, Node)

    assert len(nodes) == 10
    assert nodes[0].get_id() == 24 and nodes[0].get_name() == "node_3"
    assert nodes[1].get_id() == 32 and nodes[1].get_name() == "node_2"
    assert nodes[2].get_id() == 46 and nodes[2].get_name() == "node_6"
    assert nodes[3].get_id() == 109 and nodes[3].get_name() == "node_4"
    assert nodes[4].get_id() == 145 and nodes[4].get_name() == "node_8"
    assert nodes[5].get_id() == 150 and nodes[5].get_name() == "node_7"
    assert nodes[6].get_id() == 160 and nodes[6].get_name() == "node_0"
    assert nodes[7].get_id() == 163 and nodes[7].get_name() == "node_1"
    assert nodes[8].get_id() == 241 and nodes[8].get_name() == "node_9"
    assert nodes[9].get_id() == 244 and nodes[9].get_name() == "node_5"

    verify_successors(nodes)


def test_chord_node_creation():
    nodes = build_nodes(10, ChordNode)

    assert len(nodes) == 10
    assert nodes[0].get_id() == 24 and nodes[0].get_name() == "node_3"
    assert nodes[1].get_id() == 32 and nodes[1].get_name() == "node_2"
    assert nodes[2].get_id() == 46 and nodes[2].get_name() == "node_6"
    assert nodes[3].get_id() == 109 and nodes[3].get_name() == "node_4"
    assert nodes[4].get_id() == 145 and nodes[4].get_name() == "node_8"
    assert nodes[5].get_id() == 150 and nodes[5].get_name() == "node_7"
    assert nodes[6].get_id() == 160 and nodes[6].get_name() == "node_0"
    assert nodes[7].get_id() == 163 and nodes[7].get_name() == "node_1"
    assert nodes[8].get_id() == 241 and nodes[8].get_name() == "node_9"
    assert nodes[9].get_id() == 244 and nodes[9].get_name() == "node_5"

    verify_successors(nodes)


def test_all_fingers():
    nodes = build_nodes(20, Node)
    node_ids = [node.get_id() for node in nodes]

    for node in nodes:
        print(f"{node.get_id()}")
        fingers = node.fingers

        assert len(fingers) == 8
        assert fingers[0].get_id() == get_id(0, node.get_id(), node_ids)
        assert fingers[1].get_id() == get_id(1, node.get_id(), node_ids)
        assert fingers[2].get_id() == get_id(2, node.get_id(), node_ids)
        assert fingers[3].get_id() == get_id(3, node.get_id(), node_ids)
        assert fingers[4].get_id() == get_id(4, node.get_id(), node_ids)
        assert fingers[5].get_id() == get_id(5, node.get_id(), node_ids)
        assert fingers[6].get_id() == get_id(6, node.get_id(), node_ids)
        assert fingers[7].get_id() == get_id(7, node.get_id(), node_ids)


def get_id(idx, node_id, ids):
    search_id = (node_id + pow(2, idx)) % 255

    for curr_id in ids:
        if curr_id >= search_id:
            return curr_id

    return ids[0]


def test_fingers_first_node():
    nodes = build_nodes(10, Node)
    fingers = nodes[0].fingers

    assert len(fingers) == 8
    assert fingers[0].get_id() == 32 and fingers[0].get_name() == "node_2"
    assert fingers[1].get_id() == 32 and fingers[1].get_name() == "node_2"
    assert fingers[2].get_id() == 32 and fingers[2].get_name() == "node_2"
    assert fingers[3].get_id() == 32 and fingers[3].get_name() == "node_2"
    assert fingers[4].get_id() == 46 and fingers[4].get_name() == "node_6"
    assert fingers[5].get_id() == 109 and fingers[5].get_name() == "node_4"
    assert fingers[6].get_id() == 109 and fingers[6].get_name() == "node_4"
    assert fingers[7].get_id() == 160 and fingers[7].get_name() == "node_0"


def test_fingers_last_node():
    nodes = build_nodes(10, Node)
    fingers = nodes[-1].fingers

    assert len(fingers) == 8
    assert fingers[0].get_id() == 24 and fingers[0].get_name() == "node_3"
    assert fingers[1].get_id() == 24 and fingers[1].get_name() == "node_3"
    assert fingers[2].get_id() == 24 and fingers[2].get_name() == "node_3"
    assert fingers[3].get_id() == 24 and fingers[3].get_name() == "node_3"
    assert fingers[4].get_id() == 24 and fingers[4].get_name() == "node_3"
    assert fingers[5].get_id() == 24 and fingers[5].get_name() == "node_3"
    assert fingers[6].get_id() == 109 and fingers[6].get_name() == "node_4"
    assert fingers[7].get_id() == 145 and fingers[7].get_name() == "node_8"


def test_fingers_first_chord_node():
    nodes = build_nodes(10, ChordNode)
    fingers = nodes[0].fingers

    assert len(fingers) == 8
    assert fingers[0].get_id() == 32 and fingers[0].get_name() == "node_2"
    assert fingers[1].get_id() == 32 and fingers[1].get_name() == "node_2"
    assert fingers[2].get_id() == 32 and fingers[2].get_name() == "node_2"
    assert fingers[3].get_id() == 32 and fingers[3].get_name() == "node_2"
    assert fingers[4].get_id() == 46 and fingers[4].get_name() == "node_6"
    assert fingers[5].get_id() == 109 and fingers[5].get_name() == "node_4"
    assert fingers[6].get_id() == 109 and fingers[6].get_name() == "node_4"
    assert fingers[7].get_id() == 160 and fingers[7].get_name() == "node_0"


def test_fingers_last_chord_node():
    nodes = build_nodes(10, ChordNode)
    fingers = nodes[-1].fingers

    assert len(fingers) == 8
    assert fingers[0].get_id() == 24 and fingers[0].get_name() == "node_3"
    assert fingers[1].get_id() == 24 and fingers[1].get_name() == "node_3"
    assert fingers[2].get_id() == 24 and fingers[2].get_name() == "node_3"
    assert fingers[3].get_id() == 24 and fingers[3].get_name() == "node_3"
    assert fingers[4].get_id() == 24 and fingers[4].get_name() == "node_3"
    assert fingers[5].get_id() == 24 and fingers[5].get_name() == "node_3"
    assert fingers[6].get_id() == 109 and fingers[6].get_name() == "node_4"
    assert fingers[7].get_id() == 145 and fingers[7].get_name() == "node_8"


def verify_successors(nodes):
    assert nodes[0].successor == nodes[1]
    assert nodes[1].successor == nodes[2]
    assert nodes[2].successor == nodes[3]
    assert nodes[3].successor == nodes[4]
    assert nodes[4].successor == nodes[5]
    assert nodes[5].successor == nodes[6]
    assert nodes[6].successor == nodes[7]
    assert nodes[7].successor == nodes[8]
    assert nodes[8].successor == nodes[9]
    assert nodes[9].successor == nodes[0]