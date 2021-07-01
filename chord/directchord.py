''' Non-networked Chord nodes

This file contains the code for chord nodes before adding ZMQ.

'''
import argparse
import json
import statistics
import logging
import sys

from sortedcontainers import SortedDict
from hash import hash_value, NUM_BITS
from util import generate_keys, open_closed, open_open


class DirectNode:

    def __init__(self, node_name, node_id):
        self.name = node_name
        self.digest_id = node_id
        self.successor = self
        self.predecessor = None
        self.fingers = [None] * NUM_BITS

    def get_name(self):
        return self.name

    def get_successor(self):
        return self.successor

    def get_id(self):
        return self.digest_id

    def set_successor(self, successor):
        self.successor = successor

    def init_fingers(self):
        logging.info(f"Building finger table for {self.name} (Digest: {self.digest_id})")

        i = 0
        next_key = (self.digest_id + pow(2, i)) % (pow(2, NUM_BITS) - 1)
        while i < NUM_BITS:
            self.fingers[i] = self.find_successor(next_key, 0)[0]
            logging.info(f"  Found finger {i} is successor({next_key}) = {self.fingers[i].get_id()}")

            i += 1
            next_key = (self.digest_id + pow(2, i)) % (pow(2, NUM_BITS) - 1)

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
            next_node = self.find_next_node(digest)
            return next_node.find_successor(digest, hops + 1)

    def find_next_node(self, digest):
        return self.successor

    def join(self, known):
        self.successor = known.find_successor(self.get_id(), 0)[0]

    def stabilize(self):
        me = self.successor.predecessor
        if me and open_open(self.digest_id, self.successor.digest_id, me.digest_id):
            self.successor = me

        self.successor.notify(self)

    def notify(self, other):
        if not self.predecessor \
                or open_open(self.predecessor.digest_id, self.digest_id, other.digest_id):
            self.predecessor = other

    def fix_fingers(self):
        self.init_fingers()


class DirectChordNode(DirectNode):

    def __init__(self, node_name, node_id):
        super().__init__(node_name, node_id)

    def find_next_node(self, digest):
        return self.closest_preceding_node(digest)

    def closest_preceding_node(self, digest):

        for finger in reversed(self.fingers):
            if not finger:
                continue

            logging.debug(f"      Is {finger.get_id()} in ({self.digest_id, digest})?")
            if open_open(self.digest_id, digest, finger.get_id()):
                logging.debug(f"        Yes, returning finger {finger.get_id()}")
                return finger

        logging.debug(f"      Finger not found. Returning successor {self.successor.get_id()}")
        return self.successor


def build_nodes(num_nodes, node_type, node_name_prefix="node"):
    node_name_fmt = "{prefix}_{id}"
    nodes = SortedDict()

    # Node names may hash to the same value. Check that the actual number of
    # nodes we are looking for has been created before exiting
    i = 0
    while len(nodes) < num_nodes:
        name = node_name_fmt.format(prefix=node_name_prefix, id=str(i))
        digest = hash_value(name)
        node = node_type(name, digest)
        nodes[digest] = node
        i += 1

    # Create the last node first and set it to prev_node so that successor
    # is set correctly
    last_node = nodes.values()[-1]
    prev_node = last_node

    first_node = last_node
    # Iterate through sorted node ids to create nodes and set the successors
    for next_node in nodes.values()[:-1]:
        # New node always points to the first node added
        next_node.set_successor(first_node)

        # Update the previous node to point to the new node
        prev_node.set_successor(next_node)

        # Set new prev node for next iteration
        prev_node = next_node

    for node in nodes.values():
        node.init_fingers()
        node.stabilize()

    return nodes


def add_nodes(nodes_map, num_new, node_type):
    name_format = 'node_added_{id}'
    hashes = nodes_map.keys()
    nodes = nodes_map.values()

    i = 0
    new_nodes = []
    prev_nodes = []
    while len(new_nodes) < num_new:
        # Create the node
        new_name = name_format.format(id=str(i))
        new_digest = hash_value(new_name)
        new_node = node_type(new_name, new_digest)
        new_nodes.append(new_node)
        nodes_map[new_digest] = new_node

        # Join the network
        new_node.join(nodes[0])
        new_node.stabilize()

        # Find previous node to stabilize
        prev_digest = next(prev_digest
                           for prev_digest in reversed(hashes)
                           if prev_digest < new_digest)
        prev_node = nodes_map[prev_digest]
        prev_node.stabilize()
        prev_nodes.append(prev_node)

    for node in nodes:
        node.fix_fingers()

    return new_nodes, prev_nodes


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
    table = [{"k": i + 1, "id": finger.get_id(), "name": finger.get_name()}
             for i, finger in enumerate(fingers)]
    return {"name": node.get_name(), "id": node.get_id(), "fingers": table}


def finger_table_links(node):
    table = finger_table(node)
    table['successor'] = node.get_successor().get_id()
    table['predecessor'] = node.predecessor.get_id()

    return table


def config_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('num_nodes', type=int, help='number of nodes to use for tests')
    parser.add_argument('num_keys', type=int, help='number of keys to run tests on')
    parser.add_argument('--key-prefix', '-k', type=str, default='data',
                        help='prefix of key name')
    parser.add_argument('--node_prefix', '-n', type=str, default='node',
                        help='prefix of node name')
    parser.add_argument('--action', '-a', choices=['hops', 'network', 'fingers', 'join'], nargs='+', default='hops',
                        help='actions to perform. \'hops\' calculates the average hops to find keys in the network. '
                             '\'network\' creates a network and outputs summary. \'fingers\' creates a network and '
                             'outputs finger tables. \'join\' creates a network, adds a new node, and runs '
                             'synchronization protocol methods')
    parser.add_argument('--finger-tables', '-f', choices=['all', 'sample'], nargs=1, default=['sample'],
                        help='determines which finger tables to print if \'fingers\' is an action')
    parser.add_argument('--joining', '-j', type=int, default=1, metavar='NUM_JOINING',
                        help='number of servers to join original network if \'join\' is an action')
    parser.add_argument('--no-formatting', action='store_true',
                        help='print raw data without formatting')

    node_type_group = parser.add_mutually_exclusive_group()
    node_type_group.add_argument('--naive-nodes', action='store_const', const=DirectNode,
                                 help='Build naive nodes. Only useful with \'hops\' action. Cannot be used with '
                                      'another node type')
    node_type_group.add_argument('--chord-nodes', action='store_const', const=DirectChordNode,
                                 help='Build chord nodes. Cannot be used with another node type')

    return parser


def main(output, args):
    parser = config_parser()
    args = parser.parse_args(args)

    num_nodes = args.num_nodes
    num_keys = args.num_keys
    key_prefix = args.key_prefix
    node_prefix = args.node_prefix
    action = args.action
    finger_tables = args.finger_tables
    num_joining = args.joining
    indent = None if args.no_formatting else 4

    # Retrieve first non None value
    node_type = next(node_type
                     for node_type in [args.chord_nodes, args.naive_nodes, DirectChordNode]
                     if node_type is not None)

    # Create data
    nodes_map = build_nodes(num_nodes, node_type, node_name_prefix=node_prefix)
    hashes = list(nodes_map.keys())
    nodes = nodes_map.values()
    keys = generate_keys(num_keys, key_prefix=key_prefix)

    # Perform actions
    if 'hops' in action:
        avg_hops = run_experiment(nodes, keys)
        print(f"Average hops with {len(nodes)} nodes is {avg_hops}", file=output)

    if 'network' in action:
        print("Nodes in the network: ", file=output)
        print(json.dumps(node_table(nodes), indent=indent), file=output)

    if 'fingers' in action:
        tables_list = nodes if 'all' == finger_tables else [nodes[0], nodes[-1]]

        for i, table in enumerate(tables_list):
            print(f"Finger table for node \"{table.get_name()}\": ", file=output)
            print(json.dumps(finger_table(table), indent=indent), file=output)

    if 'join' in action:
        print(f'Original node ids: {hashes}', file=output)
        new, updated = add_nodes(nodes_map, num_joining, node_type)

        print(f"\nFinger table(s) for new nodes:", file=output)
        for new_node in new:
            print(json.dumps(finger_table_links(new_node), indent=indent), file=output)

        print(f'\nFinger table(s) for key updated nodes:', file=output)
        for updated_node in updated:
            print(json.dumps(finger_table_links(updated_node), indent=indent), file=output)


if __name__ == "__main__":
    main(sys.stdout, sys.argv[1:])
