import json
import re
import sys

import sortedcontainers


class NodeState:

    def __init__(self, json):
        self.json = json

    def get_digest(self):
        return self.json['routing_info']['digest']

    def get_finger_digests(self):
        return [finger['digest'] for finger in self.json['fingers']]

    def assert_fingers(self, digests):
        errors = []
        for i, actual in enumerate(self.get_finger_digests()):
            expected = self.get_id(i, self.get_digest(), digests)
            if actual != expected:
                errors.append((self.get_digest(), i, actual, expected))

        return errors

    @staticmethod
    def get_id(idx, node_id, ids):
        search_id = (node_id + pow(2, idx)) % 255

        for curr_id in ids:
            if curr_id >= search_id:
                return curr_id

        return ids[0]


def parse_file(filename):
    file = open(filename)

    # TODO use more robust regex
    # For some reason, if I try to concat this with another string, nothing prints
    node_state = re.compile('[^\n]+\[node.py:372\] ([^\n]+)')

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

    return data


def main():
    filename = sys.argv[1]
    expected_num = int(sys.argv[2])

    nodes_map = parse_file(filename)
    print(f'Evaluating {len(nodes_map)} nodes out of {expected_num}')

    errors = []
    for node in nodes_map.values():
        errors += node.assert_fingers(nodes_map.keys())

    print(f'{len({elt[0] for elt in errors})} nodes contain errors')
    for digest, idx, actual, expected in errors:
        print(f'Node {digest} has incorrect finger[{idx}]. Actual: {actual} Expected: {expected}')

    print(f'Result: Log {filename} contains {(expected_num - len(nodes_map)) + len(errors)} errors')


if __name__ == '__main__':
    main()