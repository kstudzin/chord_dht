import statistics

from sortedcontainers import SortedDict

from util import generate_keys
from hash import hash_value


class Node:

    def __init__(self, name, id):
        self.name = name
        self.digest_id = id
        self.successor = None

    def get_name(self):
        return self.name

    def successor(self):
        return self.successor

    def get_id(self):
        return self.digest_id

    def set_successor(self, successor):
        self.successor = successor

    def find_successor(self, digest, hops):
        next_id = self.successor.get_id()
        if next_id > self.digest_id:
            if self.digest_id < digest <= next_id:
                return self.successor, hops
            else:
                return self.successor.find_successor(digest, hops + 1)
        else:
            # Handle the case where this node has the highest digest
            if digest > self.digest_id or digest <= next_id:
                return self.successor, hops
            else:
                return self.successor.find_successor(digest, hops + 1)


def build_nodes(num_nodes):
    node_name_fmt = "node_{id}"
    nodes = SortedDict()

    for i in range(num_nodes):
        name = node_name_fmt.format(id=str(i))
        digest = hash_value(name)
        nodes[digest] = Node(name, digest)

    # Use a separate iterator over the nodes to set the successors
    successors_list = list(nodes.values())
    successors = iter(successors_list)

    # Last node successor needs to be set to the first node
    first_node = next(successors)
    last_node = successors_list[-1]
    last_node.set_successor(first_node)

    # We have already set successor on the last node. Now set successor
    # on n-1 earlier nodes
    for node_digest in nodes.keys()[:-1]:
        next_node = next(successors)
        nodes[node_digest].set_successor(next_node)

    return nodes


def run_experiment(num_nodes, num_keys):
    nodes = build_nodes(num_nodes)
    keys = generate_keys(num_keys)

    hops_tracker = []
    starting_node = nodes.values()[0]
    for key in keys:
        node, hops = starting_node.find_successor(hash_value(key), 0)
        hops_tracker.append(hops)

    return statistics.mean(hops_tracker)


def main():
    num_nodes = 50
    num_keys = 100
    avg_hops = run_experiment(num_nodes, num_keys)
    print(f"Average hops with {num_nodes} nodes is {avg_hops}")

    num_nodes = 100
    avg_hops = run_experiment(num_nodes, num_keys)
    print(f"Average hops with {num_nodes} nodes is {avg_hops}")

    # The number of hops to find a key using naive routing should be
    # proportional to the number of nodes in the network. Specifically
    # it should be close to n/2 which is what we see here


if __name__ == "__main__":
    main()
