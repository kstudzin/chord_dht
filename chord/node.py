import statistics

from sortedcontainers import SortedDict

from util import generate_keys
from hash import hash_value, NUM_BITS


class Node:

    def __init__(self, name, id):
        self.name = name
        self.digest_id = id
        self.successor = None
        self.fingers = []

    def get_name(self):
        return self.name

    def successor(self):
        return self.successor

    def get_id(self):
        return self.digest_id

    def set_successor(self, successor):
        self.successor = successor

    def fix_fingers(self):
        i = 0
        next_key = self.digest_id + pow(2, i)
        while i < NUM_BITS:
            next_finger = self.find_successor(next_key, 0)[0]
            self.fingers.append(next_finger)

            i += 1
            next_key = self.digest_id + pow(2, i)

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
    node_ids = SortedDict()

    for i in range(num_nodes):
        name = node_name_fmt.format(id=str(i))
        digest = hash_value(name)
        node_ids[digest] = name

    # List of nodes to return
    nodes = []

    # Create the last node first and set it to prev_node so that successor
    # is set correctly
    last_digest = node_ids.keys()[-1]
    last_name = node_ids.values()[-1]
    last_node = Node(last_name, last_digest)
    prev_node = last_node

    # Iterate through sorted node ids to create nodes and set the successors
    for node_id in node_ids.keys()[:-1]:
        next_node = Node(node_ids[node_id], node_id)
        prev_node.set_successor(next_node)
        prev_node = next_node
        nodes.append(next_node)

    next_node.set_successor(last_node)
    nodes.append(last_node)

    for node in nodes:
        node.fix_fingers()

    return nodes


def run_experiment(num_nodes, num_keys):
    nodes = build_nodes(num_nodes)
    keys = generate_keys(num_keys)

    hops_tracker = []
    starting_node = nodes[0]
    for key in keys:
        node, hops = starting_node.find_successor(hash_value(key), 0)
        hops_tracker.append(hops)

    return statistics.mean(hops_tracker)


def main():
    # ----------------------------------------------------
    # Test naive routing
    # ----------------------------------------------------
    print("\nCalculating average hops for naive routing...\n")
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

    # ----------------------------------------------------
    # Test finger table
    # ----------------------------------------------------
    print("\nDisplaying nodes and sample finger table...")
    nodes = build_nodes(10)
    print("\nNodes in the network: ")
    node_table = ["    Id: {0:>5}   Name: {1:<10}".format(node.get_id(), node.get_name()) for node in nodes]
    print(*node_table, sep='\n')

    test_node = nodes[0]
    print(f"\nFinger table for node \"{test_node.get_name()}\" with id {test_node.get_id()}: ")
    finger_table = ["{0:>5} | {1:>5} | {2:<10}".format(i + 1, finger.get_id(), finger.get_name())
                    for i, finger in enumerate(test_node.fingers)]
    print(*finger_table, sep='\n')


if __name__ == "__main__":
    main()
