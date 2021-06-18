import logging

from util import open_closed, open_open
from hash import NUM_BITS


class Node:

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


class ChordNode(Node):

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
