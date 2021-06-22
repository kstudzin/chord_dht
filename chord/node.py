import logging
import pprint
import struct
import threading
import time

import zmq

import chord
from util import open_closed, open_open
from hash import NUM_BITS, hash_value


class Node:

    def __init__(self, node_name, node_id, address, external_port=None, internal_port=None):
        endpoint_fmt = '{0}:{1}'

        # Node identification
        self.name = node_name
        self.digest_id = node_id

        # ZMQ sockets
        self.context = zmq.Context()
        self.router = self.context.socket(zmq.ROUTER)

        if external_port:
            self.external_endpoint = endpoint_fmt.format(address, external_port)
            self.router.bind(self.external_endpoint)
        else:
            port = self.router.bind_to_random_port(address)
            self.external_endpoint = endpoint_fmt.format(address, port)

        identity = struct.pack('i', self.digest_id)
        self.receiver = self.context.socket(zmq.DEALER)
        self.receiver.setsockopt(zmq.IDENTITY, identity)

        if internal_port:
            self.internal_endpoint = endpoint_fmt.format(address, internal_port)
            self.receiver.bind(self.internal_endpoint)
        else:
            port = self.receiver.bind_to_random_port(address)
            self.internal_endpoint = endpoint_fmt.format(address, port)

        self.stabilize_address = f'inproc://stabilize_{self.digest_id}'
        self.fix_fingers_address = f'inproc://fix_fingers_{self.digest_id}'

        self.connected = set()

        # Pointers to network nodes
        self.successor = self.digest_id
        self.successor_address = self.internal_endpoint
        self.predecessor = None
        self.predecessor_address = None
        self.fingers = [None] * NUM_BITS
        self.finger_addresses = [None] * NUM_BITS

    def get_name(self):
        return self.name

    def get_successor(self):
        return self.successor

    def get_id(self):
        return self.digest_id

    def set_successor(self, successor):
        self.successor = successor

    def _init_fingers(self, pair):
        logging.info(f"Building finger table for {self.name} (Digest: {self.digest_id})")

        i = 0
        next_key = (self.digest_id + pow(2, i)) % (pow(2, NUM_BITS) - 1)
        while i < NUM_BITS:
            finger, finger_address = self._find_successor(pair, next_key)
            self.fingers[i] = finger
            self.finger_addresses[i] = finger_address
            logging.info(f"  Found finger {i} is successor({next_key}) = {self.fingers[i]}")

            i += 1
            next_key = (self.digest_id + pow(2, i)) % (pow(2, NUM_BITS) - 1)

    def _find_successor(self, pair, digest):
        cmd = FindSuccessorCommand()
        cmd.return_id = self.digest_id
        cmd.return_address = self.internal_endpoint
        cmd.return_type = FindSuccessorCommand.RETURN_TYPE_NODE
        cmd.digest = digest

        pair.send(Command.FIND_SUCCESSOR, zmq.SNDMORE)
        pair.send_json(vars(cmd))

        recv_cmd = pair.recv()
        found = pair.recv_json()
        found_cmd = FindSuccessorCommand.parse(found)
        return found_cmd.successor, found_cmd.address

    def find_successor(self, digest, hops):
        if digest == self.digest_id:
            return True, self.digest_id, self.internal_endpoint, hops

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
        logging.debug(f'Node {self.digest_id} initialized successor {self.successor} at {self.successor_address}')

    def notify(self, other, other_address):
        logging.debug(f'Node {self.digest_id} notified by node {other}')
        if not self.predecessor \
                or open_open(self.predecessor, self.digest_id, other):
            logging.debug(f'Node {self.digest_id} updating predecessor')
            self.predecessor = other
            self.predecessor_address = other_address

            # Set successor if there are only 2 nodes in the system
            if open_open(self.digest_id, self.successor, self.predecessor):
                self.successor = self.predecessor
                self.successor_address = self.predecessor_address

    def fix_fingers(self, context):
        pair = context.socket(zmq.PAIR)
        pair.connect(self.fix_fingers_address)

        while True:
            time.sleep(5)
            self._init_fingers(pair)

    def stabilize_loop(self, context: zmq.Context):
        pair = context.socket(zmq.PAIR)
        pair.connect(self.stabilize_address)

        while True:
            time.sleep(5)
            self._stabilize(pair)

    def _stabilize(self, pair):
        logging.debug(f'Node {self.digest_id} running stabilize')

        pred_id, pred_addr = self._get_predecessor(pair)
        if pred_id and open_open(self.digest_id, self.successor, pred_id):
            logging.debug(f'Node {self.digest_id} found new successor {pred_id}')
            self.successor = pred_id
            self.successor_address = pred_addr

        logging.debug(f'Node {self.digest_id} notifying successor {self.successor}')
        self._notify_successor(pair)

    @staticmethod
    def _notify_successor(pair):
        notify_cmd = vars(NotifyCommand())
        pair.send(Command.NOTIFY, zmq.SNDMORE)
        pair.send_json(notify_cmd)

    @staticmethod
    def _get_predecessor(pair):
        predecessor_cmd = vars(PredecessorCommand())
        pair.send(Command.GET_SUCCESSOR_PREDECESSOR, zmq.SNDMORE)
        pair.send_json(predecessor_cmd)

        cmd_id = pair.recv()
        message = pair.recv_json()
        cmd = PredecessorCommand.parse(message)
        return cmd.succ_pred, cmd.succ_pred_address

    def run(self):
        logging.info(f'Starting loop for node {self.digest_id}')

        stability = self.context.socket(zmq.PAIR)
        stability.bind(self.stabilize_address)

        fix_fingers = self.context.socket(zmq.PAIR)
        fix_fingers.bind(self.fix_fingers_address)

        poller = zmq.Poller()
        poller.register(self.receiver, zmq.POLLIN)
        poller.register(stability, zmq.POLLIN)
        poller.register(fix_fingers, zmq.POLLIN)

        while True:

            socks = dict(poller.poll())

            for sock in socks:
                # Receive the message
                cmd = sock.recv()
                message = sock.recv_json()
                logging.debug(f'Node {self.digest_id} received {cmd} message {message}')

                # Process the message
                command = parsers[cmd](message)
                result = command.execute(self)

                # Process results
                if result:
                    address = result[0]
                    identity = result[1]
                    next_cmd = result[2]
                    parameters = result[3]

                    if address == self.stabilize_address and not identity:
                        stability.send(next_cmd, zmq.SNDMORE)
                        stability.send_json(parameters)
                    elif address == self.fix_fingers_address and not identity:
                        fix_fingers.send(next_cmd, zmq.SNDMORE)
                        fix_fingers.send_json(parameters)
                    else:
                        self.route_result(address, identity, next_cmd, parameters)

    def route_result(self, address, identity, next_cmd, parameters):
        logging.info(f'Node {self.digest_id} sending {next_cmd} with {parameters} to node {identity} at {address}')
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
    FIND_SUCCESSOR = b'FIND_SUCCESSOR'
    GET_SUCCESSOR_PREDECESSOR = b'GET_PREDECESSOR'
    NOTIFY = b'NOTIFY'

    def execute(self, node):
        pass

    @staticmethod
    def parse(cmd, parameters):
        for key in parameters:
            setattr(cmd, key, parameters[key])
        return cmd


class NotifyCommand(Command):

    def __init__(self):
        self.initiator_id = None
        self.initiator_address = None

    def execute(self, node):
        if not self.initiator_id and not self.initiator_address:
            self.initiator_id = node.digest_id
            self.initiator_address = node.internal_endpoint
            return node.successor_address, node.successor, Command.NOTIFY, vars(self)
        else:
            node.notify(self.initiator_id, self.initiator_address)

    @staticmethod
    def parse(parameters):
        cmd = NotifyCommand()
        return  Command.parse(cmd, parameters)


class PredecessorCommand(Command):

    def __init__(self):
        self.return_id = None
        self.return_address = None
        self.succ_pred = None
        self.succ_pred_address = None

    def execute(self, node):
        if not self.return_id and not self.return_address:
            self.return_id = node.digest_id
            self.return_address = node.internal_endpoint
            return node.successor_address, node.successor, Command.GET_SUCCESSOR_PREDECESSOR, vars(self)
        elif not self.succ_pred:
            self.succ_pred = node.successor
            self.succ_pred_address = node.successor_address
            return self.return_address, self.return_id, Command.GET_SUCCESSOR_PREDECESSOR, vars(self)
        else:
            return node.stabilize_address, None, Command.GET_SUCCESSOR_PREDECESSOR, vars(self)

    @staticmethod
    def parse(parameters):
        cmd = PredecessorCommand()
        return Command.parse(cmd, parameters)


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
                node.router.connect(self.address)
                node.connected.add(self.address)
                return node.fix_fingers_address, None, Command.FIND_SUCCESSOR, vars(self)
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


parsers = {Command.FIND_SUCCESSOR: FindSuccessorCommand.parse,
           Command.GET_SUCCESSOR_PREDECESSOR: PredecessorCommand.parse,
           Command.NOTIFY: NotifyCommand.parse}


def main():
    print('Creating node 1')
    name1 = 'node_0'
    digest1 = hash_value(name1)
    node1 = Node(name1, digest1, 'tcp://127.0.0.1', '5500', '5501')

    print('Creating node 2')
    name2 = 'node_1'
    digest2 = hash_value(name2)
    node2 = Node(name2, digest2, 'tcp://127.0.0.1', '5502', '5503')

    print('Staring node 1')
    node1_t = threading.Thread(target=node1.run, daemon=True)
    node1_t.start()

    print('Node 2 joins Node 1')
    node2.join(node1.digest_id, node1.internal_endpoint)

    print('Result:')
    print(chord.finger_table_links(node1))
    print(chord.finger_table_links(node2))

    print('Starting node 2')
    node2_t = threading.Thread(target=node2.run, daemon=True)
    node2_t.start()

    print('Stabilize Node 2')
    pair = node2.context.socket(zmq.PAIR)
    pair.connect(node2.stabilize_address)
    node2._stabilize(pair)

    print('Wait for execution to complete')
    time.sleep(5)

    print('Result:')
    print(chord.finger_table_links(node1))
    print(chord.finger_table_links(node2))

    print('Stabilize Node 1')
    pair = node1.context.socket(zmq.PAIR)
    pair.connect(node1.stabilize_address)
    node1._stabilize(pair)

    print('Wait for execution to complete')
    time.sleep(5)

    print('Result:')
    print(chord.finger_table_links(node1))
    print(chord.finger_table_links(node2))

    print('Fixing fingers')
    fix_pair1 = node1.context.socket(zmq.PAIR)
    fix_pair1.connect(node1.fix_fingers_address)
    node1._init_fingers(fix_pair1)

    fix_pair2 = node2.context.socket(zmq.PAIR)
    fix_pair2.connect(node2.fix_fingers_address)
    node2._init_fingers(fix_pair2)

    print('Result:')
    pp = pprint.PrettyPrinter()
    pp.pprint(chord.finger_table_links(node1))
    pp.pprint(chord.finger_table_links(node2))


if __name__ == '__main__':
    main()
