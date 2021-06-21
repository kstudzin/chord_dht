import logging
import struct
import threading
import time

import zmq

import chord
from util import open_closed, open_open
from hash import NUM_BITS, hash_value


class Node:

    def __init__(self, node_name, node_id, address1, address2):
        self.name = node_name
        self.digest_id = node_id
        self.internal_endpoint = address2

        self.successor = self.digest_id
        self.successor_address = self.internal_endpoint
        self.predecessor = None
        self.fingers = [None] * NUM_BITS
        self.finger_addresses = [None] * NUM_BITS

        self.context = zmq.Context()
        self.router = self.context.socket(zmq.ROUTER)
        self.router.bind(address1)

        identity = struct.pack('i', self.digest_id)
        self.receiver = self.context.socket(zmq.DEALER)
        self.receiver.setsockopt(zmq.IDENTITY, identity)
        self.receiver.bind(self.internal_endpoint)

        self.connected = set()

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

        next_id = self.successor

        logging.debug(f"    Is id {digest} contained in ({self.digest_id}, {next_id}]?")

        if open_closed(self.digest_id, next_id, digest):

            logging.debug(f"      Yes, returning successor {next_id} hops: {hops}")
            return True, self.successor, self.successor_address, hops + 1
        else:

            logging.debug(f"      No, finding closest preceding node")
            next_node, next_address = self.find_next_node(digest)
            return False, next_node, next_address, hops + 1

    def find_next_node(self, digest):
        return self.successor, self.successor_address

    def join(self, known_id, known_address):
        logging.debug(f'Node {self.digest_id} at {self.internal_endpoint} joining '
                      f'known node {known_id} at {known_address}')

        params = {'digest': self.digest_id,
                  'return_id': self.digest_id,
                  'return_address': self.internal_endpoint}
        self.route_result(known_address, known_id, Command.FIND_SUCCESSOR, params)

        # Block waiting for result. We can't start execution without know our successor
        # Because loop has not started, we can wait for the message here
        cmd = self.receiver.recv()
        result = self.receiver.recv_json()

        found_successor = FindSuccessorCommand.parse(result)
        self.successor = found_successor.successor
        self.successor_address = found_successor.address

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

    def run(self):
        logging.info(f'Starting loop for node {self.digest_id}')

        while True:

            # Receive the message
            cmd = self.receiver.recv()
            message = self.receiver.recv_json()
            logging.debug(f'Node {self.digest_id} received message {message}')

            # Process the message
            command = parsers[cmd](message)
            result = command.execute(self)

            # Process results
            if result:
                self.route_result(result[0], result[1], result[2], result[3])

    def route_result(self, address, identity, next_cmd, parameters):
        logging.info(f'Node {self.digest_id} sending {parameters} to node {identity}')
        if address not in self.connected:
            self.connected.add(address)
            self.router.connect(address)
            time.sleep(.5)

        identity_b = struct.pack('i', identity)
        self.router.send(identity_b, zmq.SNDMORE)
        self.router.send(next_cmd, zmq.SNDMORE)
        self.router.send_json(parameters)


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


class Command:
    FIND_SUCCESSOR = struct.pack('i', 0)

    def execute(self, node):
        pass

    @staticmethod
    def parse(cmd, parameters):
        for key in parameters:
            setattr(cmd, key, parameters[key])
        return cmd


class FindSuccessorCommand(Command):

    RETURN_TYPE_NODE = 0
    RETURN_TYPE_CLIENT = 1

    def __init__(self):
        self.digest = None
        self.hops = 0
        self.return_id = None
        self.return_address = None
        self.return_type = None
        self.return_data = None
        self.found = False
        self.successor = None
        self.address = None

    def execute(self, node):
        if self.found:
            if self.return_type == self.RETURN_TYPE_NODE:
                node.fingers[self.return_data] = self.successor
                node.finger_addresses[self.return_data] = self.address
                node.router.connect(self.address)
            elif self.return_type == self.RETURN_TYPE_CLIENT:
                pass
        else:
            self.found, self.successor, self.address, self.hops = node.find_successor(self.digest, self.hops)
            if self.found:
                return self.return_address, self.return_id, Command.FIND_SUCCESSOR, vars(self)
            return self.address, self.successor, Command.FIND_SUCCESSOR, vars(self)

    @staticmethod
    def parse(parameters):
        cmd = FindSuccessorCommand()
        return Command.parse(cmd, parameters)


parsers = {Command.FIND_SUCCESSOR: FindSuccessorCommand.parse}


def main():
    print('Creating node 1')
    name1 = 'node_0'
    digest1 = hash_value(name1)
    node1 = Node(name1, digest1, 'tcp://127.0.0.1:5500', 'tcp://127.0.0.1:5501')

    print('Creating node 2')
    name2 = 'node_1'
    digest2 = hash_value(name2)
    node2 = Node(name2, digest2, 'tcp://127.0.0.1:5502', 'tcp://127.0.0.1:5503')

    print('Staring node 1')
    node1_t = threading.Thread(target=node1.run, daemon=True)
    node1_t.start()

    print('Node 2 joins node1')
    node2.join(node1.digest_id, node1.internal_endpoint)

    print('Result:')
    print(chord.finger_table_links(node1))
    print(chord.finger_table_links(node2))


if __name__ == '__main__':
    main()
