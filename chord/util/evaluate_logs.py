import argparse
import json
import re
import statistics
import sortedcontainers

from collections import defaultdict
from chord.hash import NUM_BITS


class NodeState:

    def __init__(self, node_dict):
        self.node_dict = node_dict

    def get_digest(self):
        return self.node_dict['routing_info']['digest']

    def get_parent(self):
        return self.node_dict['routing_info']['parent_digest']

    def get_finger_digests(self):
        return [finger['digest'] for finger in self.node_dict['fingers']]

    def assert_fingers(self, digests):
        errors = []
        for i, actual in enumerate(self.get_finger_digests()):
            expected = self.get_id(i, self.get_digest(), digests)
            if actual != expected:
                errors.append((self.get_digest(), i, actual, expected))

        return errors

    def calculate_load(self, digests):
        # not using predecessor because network may not have stabilized
        for i, digest in enumerate(digests):
            if digest == self.get_digest():
                return digests[i - 1] - digest


    @staticmethod
    def get_id(idx, node_id, ids):
        search_id = (node_id + pow(2, idx)) % 255

        for curr_id in ids:
            if curr_id >= search_id:
                return curr_id

        return ids[0]


def calculate_errors(nodes_map):
    errors = []
    for node in nodes_map.values():
        errors += node.assert_fingers(nodes_map.keys())
    return errors


def calculate_loads(digests):
    load = defaultdict(int)
    last_digest = 0
    for i, (digest, parent) in enumerate(digests):
        if i == 0:
            first_node = parent
        load[parent] += digest - last_digest
        last_digest = digest
    load[first_node] += pow(2, NUM_BITS) - last_digest

    return load


def parse_file(filename):
    file = open(filename)

    # TODO use more robust regex
    # For some reason, if I try to concat this with another string, nothing prints
    node_state = re.compile('.*Node state: (.*)')
    node_list = re.compile('.*Node (\d+) managing.* dict_keys\(\[(.*)\]\)')

    digests = sortedcontainers.SortedList()
    data = sortedcontainers.SortedDict()
    for line in file.readlines():

        match = node_state.match(line)
        if match:
            node_str = match.group(1).replace('\'', '"')
            if 'None' in node_str:
                continue
            vnode_json = json.loads(node_str)
            for node_json in vnode_json:
                node = NodeState(node_json)
                digest = node.get_digest()
                data[digest] = node
            continue

        match = node_list.match(line)
        if match:
            parent = int(match.group(1))
            children = [int(digest) for digest in match.group(2).split(', ')]
            digests.update([(child, parent) for child in children])

    return data, digests


def config_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('filename', type=str, help='name of log to evaluate')
    parser.add_argument('--load-statistics', '-l', action='store_true',
                        help='calculate mean and std dev of number of keys each physical node is responsible for')
    parser.add_argument('--finger-errors', '-f', action='store_true',
                        help='calculate which fingers are incorrect, i.e. had not stabilized when the servers stopped')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='summarize finger errors')

    return parser


def main():
    parser = config_parser()
    args = parser.parse_args()

    filename = args.filename
    load_statistics = args.load_statistics
    finger_errors = args.finger_errors
    verbose = args.verbose

    # Parse log
    nodes_map, digests = parse_file(filename)
    if not nodes_map and not digests:
        print('No data found. Check that log level set to INFO.')
        exit(1)

    # Calculate load for each node
    if load_statistics:
        print(f'Evaluating {len(digests)} nodes')
        if digests:
            load = calculate_loads(digests)
            print(f'Average load: {statistics.mean(load.values())}')
            print(f'Standard deviation: {statistics.stdev(load.values())}')

    # Calculate errors
    if finger_errors:
        print(f'Evaluating {len(nodes_map)} nodes out of {len(digests)} nodes started')
        errors = calculate_errors(nodes_map)
        print(f'{len({elt[0] for elt in errors})} nodes contain {len(errors)} errors')

        if verbose:
            for digest, idx, actual, expected in errors:
                print(f'Node {digest} has incorrect finger[{idx}]. Actual: {actual} Expected: {expected}')


if __name__ == '__main__':
    main()