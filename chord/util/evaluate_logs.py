import json
import re
import statistics
import sys
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


def calculate_loads(nodes_map):
    load = defaultdict(int)
    last_digest = 0
    for i, (digest, node) in enumerate(nodes_map.items()):
        if i == 0:
            first_node = node
        load[node.get_parent()] += digest - last_digest
        last_digest = digest
    load[first_node.get_parent()] += pow(2, NUM_BITS) - last_digest

    return load


def parse_file(filename):
    file = open(filename)

    # TODO use more robust regex
    # For some reason, if I try to concat this with another string, nothing prints
    node_state = re.compile('[^\n]+\[node.py:376\] ([^\n]+)')

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

    return data


def main():
    filename = sys.argv[1]
    expected_num = int(sys.argv[2])

    # Parse log
    nodes_map = parse_file(filename)
    print(f'Evaluating {len(nodes_map)} nodes out of {expected_num}')

    # Calculate load for each node
    load = calculate_loads(nodes_map)
    print(f'Average load: {statistics.mean(load.values())}')
    print(f'Standard deviation: {statistics.stdev(load.values())}')

    # Calculate errors
    errors = calculate_errors(nodes_map)
    print(f'{len({elt[0] for elt in errors})} nodes contain errors')
    for digest, idx, actual, expected in errors:
        print(f'Node {digest} has incorrect finger[{idx}]. Actual: {actual} Expected: {expected}')

    print(f'Result: Log {filename} contains {(expected_num - len(nodes_map)) + len(errors)} errors')


if __name__ == '__main__':
    main()