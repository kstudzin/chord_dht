import argparse
import logging
import pprint
import statistics

from sortedcontainers import SortedDict

from util import generate_keys, open_closed, open_open
from hash import hash_value, NUM_BITS

pp = pprint.PrettyPrinter()


class Node:

    def __init__(self, node_name, node_id):
        self.name = node_name
        self.digest_id = node_id
        self.successor = self
        self.fingers = []

    def get_name(self):
        return self.name

    def get_successor(self):
        return self.successor

    def get_id(self):
        return self.digest_id

    def set_successor(self, successor):
        self.successor = successor
        self.init_fingers(3)

    def init_fingers(self, propagate):
        # print(f"Propagate {propagate}")
        # def fix_fingers(self):
        self.fingers = []

        logging.info(f"Building finger table for {self.name} (Digest: {self.digest_id})")
        i = 0
        next_key = (self.digest_id + pow(2, i)) % (pow(2, NUM_BITS) - 1)
        while i < NUM_BITS:
            next_finger = self.find_successor(next_key, 0)[0]

            self.fingers.append(next_finger)
            logging.info(f"  Found finger {i} is successor({next_key}) = {next_finger.get_id()}")

            i += 1
            next_key = (self.digest_id + pow(2, i)) % (pow(2, NUM_BITS) - 1)

        if propagate > 0:
            for finger in self.fingers:
                finger.init_fingers(propagate - 1)

    def find_successor(self, digest, hops):
        next_id = self.successor.get_id()
        if open_closed(self.digest_id, next_id, digest):
            return self.successor, hops + 1
        else:
            return self.successor.find_successor(digest, hops + 1)


class ChordNode(Node):

    def __init__(self, node_name, node_id):
        super().__init__(node_name, node_id)

    def find_successor(self, digest, hops):
        if digest == self.digest_id:
            return self, hops

        next_id = self.successor.get_id()

        logging.debug(f"    Is id {digest} contained in ({self.digest_id}, {next_id}]?")
        if open_closed(self.digest_id, next_id, digest):
            logging.debug(f"      Yes, returning successor {next_id} hops: {hops}")
            return self.successor, hops + 1
        else:
            logging.debug(f"      No, finding closest preceding node")
            next_node = self.closest_preceding_node(digest)
            return next_node.find_successor(digest, hops + 1)

    def closest_preceding_node(self, digest):

        for finger in reversed(self.fingers):

            logging.debug(f"      Is {finger.get_id()} in ({self.digest_id, digest})?")
            if open_open(self.digest_id, digest, finger.get_id()):
                logging.debug(f"        Yes, returning finger {finger.get_id()}")
                return finger

        logging.debug(f"      Finger not found. Returning successor {self.successor.get_id()}")
        return self.successor


def build_nodes(num_nodes, node_type, node_name_prefix="node"):
    node_name_fmt = "{prefix}_{id}"
    node_ids = SortedDict()

    # Node names may hash to the same value. Check that the actual number of
    # nodes we are looking for has been created before exiting
    i = 0
    while len(node_ids) < num_nodes:
        name = node_name_fmt.format(prefix=node_name_prefix, id=str(i))
        digest = hash_value(name)
        node_ids[digest] = name
        i += 1

    # List of nodes to return
    nodes = []

    # Create the last node first and set it to prev_node so that successor
    # is set correctly
    last_digest = node_ids.keys()[-1]
    last_name = node_ids.values()[-1]
    last_node = node_type(last_name, last_digest)
    prev_node = last_node

    first_node = last_node
    # Iterate through sorted node ids to create nodes and set the successors
    for node_id in node_ids.keys()[:-1]:
        next_node = node_type(node_ids[node_id], node_id)
        nodes.append(next_node)
        logging.debug(node_table(nodes))

        # New node always points to the first node added
        next_node.set_successor(first_node)
        logging.info(finger_table(next_node))

        # Update the previous node to point to the new node
        prev_node.set_successor(next_node)
        logging.debug(finger_table(prev_node))

        # Set new prev node for next iteration
        prev_node = next_node

    # next_node.set_successor(last_node)
    nodes.append(last_node)

    # for node in nodes:
    #     node.fix_fingers()

    return nodes


def run_experiment(nodes, keys):
    hops_tracker = []
    starting_node = nodes[0]
    for key in keys:
        logging.debug(f"Testing key {key}")

        node, hops = starting_node.find_successor(hash_value(key), 0)
        hops_tracker.append(hops)

    return statistics.mean(hops_tracker)


def node_table(nodes):
    table = [{"id": node.get_id(), "name": node.get_name()} for node in nodes]
    return {"network": table}


def finger_table(node):
    fingers = node.fingers
    table = [{"position": i, "id": finger.get_id(), "name": finger.get_name()}
             for i, finger in enumerate(fingers)]
    return {"name": node.get_name(), "id": node.get_id(), "fingers": table}


def config_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('num_nodes', type=int, help='number of nodes to use for tests')
    parser.add_argument('num_keys', type=int, help='number of keys to run tests on')
    parser.add_argument('--naive-nodes', action='store_const', const=Node,
                        help='Build naive nodes')
    parser.add_argument('--chord-nodes', action='store_const', const=ChordNode,
                        help='Build chord nodes')
    parser.add_argument('--key-prefix', '-k', type=str, default='data',
                        help='prefix of key name')
    parser.add_argument('--node_prefix', '-n', type=str, default='node',
                        help='prefix of node name')
    parser.add_argument('--action', '-a', choices=['hops', 'network', 'fingers'], nargs='+', default='hops',
                        help='')
    parser.add_argument('--finger-tables', '-f', choices=['all', 'sample'], nargs='+', default=['sample'],
                        help='which finger tables to print')
    parser.add_argument('--no-formatting', action='store_const', const=print, default=pp.pprint,
                        help='print raw data without formatting')

    return parser


def main():
    parser = config_parser()
    args = parser.parse_args()

    num_nodes = args.num_nodes
    num_keys = args.num_keys
    key_prefix = args.key_prefix
    node_prefix = args.node_prefix
    action = args.action
    finger_tables = args.finger_tables
    printer = args.no_formatting

    # Retrieve first non None value
    node_type = next(node_type
                     for node_type in [args.chord_nodes, args.naive_nodes, ChordNode]
                     if node_type is not None)

    nodes = build_nodes(num_nodes, node_type, node_name_prefix=node_prefix)
    keys = generate_keys(num_keys, key_prefix=key_prefix)

    if 'hops' in action:
        avg_hops = run_experiment(nodes, keys)
        print(f"Average hops with {len(nodes)} nodes is {avg_hops}")

    if 'network' in action:
        print("Nodes in the network: ")
        printer(node_table(nodes))

    if 'fingers' in action:
        tables_list = nodes if 'all' in finger_tables else [nodes[0], nodes[-1]]

        for i, table in enumerate(tables_list):
            print(f"Finger table for node {i}: ")
            printer(finger_table(table))


if __name__ == "__main__":
    main()
