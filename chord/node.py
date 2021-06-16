import math
import pprint
import statistics

from sortedcontainers import SortedDict

from util import generate_keys
from hash import hash_value, NUM_BITS

pp = pprint.PrettyPrinter()


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
        next_key = self.digest_id + pow(2, i) % pow(2, NUM_BITS)
        while i < NUM_BITS:
            next_finger = self.find_successor(next_key, 0)[0]
            self.fingers.append(next_finger)

            i += 1
            next_key = self.digest_id + pow(2, i) % pow(2, NUM_BITS)

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


class ChordNode:

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
        self.fingers.append(successor)

    def fix_fingers(self):
        print(f"Calling fix_fingers on {self.digest_id}. modulus: {pow(2, NUM_BITS) - 1}")
        i = 0
        next_key = self.digest_id + pow(2, i) % (pow(2, NUM_BITS) - 1)
        while i < NUM_BITS:
            print(f"  Finding successor of {next_key}")
            next_finger = self.find_successor(next_key, 0)[0]
            self.fingers.append(next_finger)
            print(f"  Found finger {i} is {next_finger.get_id()}")

            i += 1
            next_key = (self.digest_id + pow(2, i)) % (pow(2, NUM_BITS) - 1)
            # print(next_key) if self.digest_id == 244 else 0

    def find_successor(self, digest, hops):
        # print(f"    Current node: {self.digest_id}")
        if digest == self.digest_id:
            return self, hops

        next_id = self.successor.get_id()

        print(f"    Is id {digest} contained in ({self.digest_id}, {next_id}]?")
        if next_id > self.digest_id:
            if self.digest_id < digest <= next_id:
                print(f"      Yes, returning successor {next_id} (1) hops: {hops}")
                return self.successor, hops + 1
            else:
                print(f"      No, finding closest preceding node (1)")
                next_node = self.closest_preceding_node(digest)
                return next_node.find_successor(digest, hops + 1)
        else:
            # Handle the case where this node has the highest digest
            if digest > self.digest_id or digest <= next_id:
                print(f"      Yes, returning successor {next_id} (2)")
                return self.successor, hops + 1
            else:
                print(f"      No, finding closest preceding node (2)")
                next_node = self.closest_preceding_node(digest)
                return next_node.find_successor(digest, hops + 1)

    def closest_preceding_node(self, digest):
        print(f"      No fingers") if not self.fingers else print(f"      {len(self.fingers)} fingers")
        for finger in reversed(self.fingers):
            print(f"      Is {finger.get_id()} in ({self.digest_id, digest})?")
            if self.digest_id < digest:
                if self.digest_id < finger.get_id() < digest:
                    print(f"        Yes, returning finger {finger.get_id()} (3)")
                    return finger
            elif self.digest_id > digest:
                if (self.digest_id < finger.get_id()
                        or finger.get_id() < digest):
                    print(f"        Yes, returning finger {finger.get_id()} (4)")
                    return finger

        print(f"      Returning current {self.successor.digest_id}")
        # return self.successor


def build_nodes(num_nodes, node_type):
    node_name_fmt = "node_{id}"
    node_ids = SortedDict()

    for i in range(num_nodes):
        name = node_name_fmt.format(id=str(i))
        digest = hash_value(name)
        node_ids[digest] = name

    pp.pprint(node_ids.keys())

    # List of nodes to return
    nodes = []

    # Create the last node first and set it to prev_node so that successor
    # is set correctly
    last_digest = node_ids.keys()[-1]
    last_name = node_ids.values()[-1]
    last_node = node_type(last_name, last_digest)
    prev_node = last_node

    # Iterate through sorted node ids to create nodes and set the successors
    for node_id in node_ids.keys()[:-1]:
        next_node = node_type(node_ids[node_id], node_id)
        prev_node.set_successor(next_node)
        prev_node = next_node
        nodes.append(next_node)

    next_node.set_successor(last_node)
    nodes.append(last_node)

    # print(f"Number of nodes: {len(nodes)}")
    for node in nodes:
        # print(f"Calling fix_fingers for {node.get_id()} ({type(node)})")
        node.fix_fingers()

    return nodes


def run_experiment(num_nodes, num_keys, node_type):
    nodes = build_nodes(num_nodes, node_type)
    keys = generate_keys(num_keys)

    hops_tracker = []
    starting_node = nodes[0]
    for key in keys:
        print(f"Testing key {key}")
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
    avg_hops = run_experiment(num_nodes, num_keys, Node)
    print(f"Average hops with {num_nodes} nodes is {avg_hops}")

    assert math.isclose(avg_hops, 22.38, abs_tol=0.01)

    num_nodes = 100
    avg_hops = run_experiment(num_nodes, num_keys, Node)
    print(f"Average hops with {num_nodes} nodes is {avg_hops}")

    assert avg_hops == 40

    # The number of hops to find a key using naive routing should be
    # proportional to the number of nodes in the network. Specifically
    # it should be close to n/2 which is what we see here

    # ----------------------------------------------------
    # Test finger table
    # ----------------------------------------------------
    print("\nBuild network...\n")
    nodes = build_nodes(10, ChordNode)
    node_table = [{"id": node.get_id(), "name": node.get_name()} for node in nodes]
    pp.pprint({"network": node_table})

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

    print("\nRetrieve finger table...\n")
    test_node = nodes[-1]
    fingers = test_node.fingers
    finger_table = [{"position": i, "id": finger.get_id(), "name": finger.get_name()}
                    for i, finger in enumerate(fingers)]
    pp.pprint({"name": test_node.get_name(), "id": test_node.get_id(), "fingers": finger_table})
    #
    # assert fingers[0].get_id() == 32 and fingers[0].get_name() == "node_2"
    # assert fingers[1].get_id() == 32 and fingers[1].get_name() == "node_2"
    # assert fingers[2].get_id() == 32 and fingers[2].get_name() == "node_2"
    # assert fingers[3].get_id() == 32 and fingers[3].get_name() == "node_2"
    # assert fingers[4].get_id() == 46 and fingers[4].get_name() == "node_6"
    # assert fingers[5].get_id() == 109 and fingers[5].get_name() == "node_4"
    # assert fingers[6].get_id() == 109 and fingers[6].get_name() == "node_4"
    # assert fingers[7].get_id() == 160 and fingers[7].get_name() == "node_0"

    # ----------------------------------------------------
    # Test chord routing
    # ----------------------------------------------------
    print("\nCalculating average hops for chord routing...\n")
    num_nodes = 50
    num_keys = 100
    avg_hops = run_experiment(num_nodes, num_keys, ChordNode)
    print(f"Average hops with {num_nodes} nodes is {avg_hops}")

    # assert math.isclose(avg_hops, 22.38, abs_tol=0.01)

    num_nodes = 100
    avg_hops = run_experiment(num_nodes, num_keys, ChordNode)
    print(f"Average hops with {num_nodes} nodes is {avg_hops}")

    # assert avg_hops == 40

    # nodes = build_nodes(100, ChordNode)
    # for test_node in nodes:
    #     if test_node.get_id() == 159:
    #         fingers = test_node.fingers
    #         finger_table = [{"position": i, "id": finger.get_id(), "name": finger.get_name()}
    #                         for i, finger in enumerate(fingers)]
    #         pp.pprint({"name": test_node.get_name(), "id": test_node.get_id(), "fingers": finger_table})


if __name__ == "__main__":
    main()
