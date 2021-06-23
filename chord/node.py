import argparse
import logging
import pprint
import struct
import sys
import threading
import time
from random import randrange
from urllib.parse import urlparse

import zmq

from util import open_closed, open_open
from hash import NUM_BITS, hash_value


# -----------------------------------------------------------------------------
# Networked Chord Implementation
# -----------------------------------------------------------------------------


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
        self.shutdown = False

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

        logging.debug(f"    Is id {digest} contained in ({self.digest_id}, {self.successor}]?")
        if open_closed(self.digest_id, self.successor, digest):

            # We have found the successor and will return it to the requester
            logging.debug(f"      Yes, returning successor {self.successor} hops: {hops}")
            return True, self.successor, self.successor_address, hops + 1
        else:

            # We have not found the successor of the digest. Return the next node
            # to advance to. For the naive nodes, this is also the successor. For
            # chord nodes, this is either a node from the finger table or the successor
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

        # If the found successor has the same id as we do, there is already
        # a node the same value in the network and we cannot join with that id
        if self.successor == self.digest_id:
            self.context.destroy()
            return False

        logging.debug(f'Node {self.digest_id} initialized successor {self.successor} at {self.successor_address}')
        return True

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

    def fix_fingers_loop(self, context, interval):
        pair = context.socket(zmq.PAIR)
        pair.connect(self.fix_fingers_address)

        try:
            while True:
                time.sleep(interval)
                self._init_fingers(pair)
        finally:
            pair.disconnect(self.fix_fingers_address)

    def stabilize_loop(self, context, interval):
        pair = context.socket(zmq.PAIR)
        pair.connect(self.stabilize_address)

        try:
            while True:
                time.sleep(interval)
                self._stabilize(pair)
        finally:
            pair.disconnect(self.stabilize_address)

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

    def run(self, stabilize_interval=5, fix_fingers_interval=7):
        logging.info(f'Starting loop for node {self.digest_id}')

        stability = self.context.socket(zmq.PAIR)
        stability.bind(self.stabilize_address)

        fix_fingers = self.context.socket(zmq.PAIR)
        fix_fingers.bind(self.fix_fingers_address)

        poller = zmq.Poller()
        poller.register(self.receiver, zmq.POLLIN)
        poller.register(stability, zmq.POLLIN)
        poller.register(fix_fingers, zmq.POLLIN)

        if stabilize_interval:
            stability_t = threading.Thread(target=self.stabilize_loop,
                                           args=[self.context, stabilize_interval],
                                           daemon=True)
            stability_t.start()

        if fix_fingers_interval:
            fix_fingers_t = threading.Thread(target=self.fix_fingers_loop,
                                             args=[self.context, fix_fingers_interval],
                                             daemon=True)
            fix_fingers_t.start()

        try:
            while True:

                logging.info(f'Node {self.digest_id} waiting for messages')
                socks = dict(poller.poll())
                received_exit = self.process_input(socks, stability, fix_fingers)
                if received_exit:
                    break

        finally:
            self.context.destroy()
            self.shutdown = True

        logging.info('Goodbye!')

    def process_input(self, socks, stability, fix_fingers):
        logging.info(f'Node {self.digest_id} processing {len(socks)} messages')
        for sock in socks:
            # Receive the message
            cmd = sock.recv()
            if cmd == Command.EXIT:
                logging.info(f'Node {self.digest_id} received EXIT message. Node shutting down.')
                return True

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

            return False

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

    def __init__(self, node_name, node_id, address, external_port=None, internal_port=None):
        super().__init__(node_name, node_id, address, external_port, internal_port)

    def find_next_node(self, digest):
        return self.closest_preceding_node(digest)

    def closest_preceding_node(self, digest):

        for finger, address in zip(reversed(self.fingers), reversed(self.finger_addresses)):
            if not finger:
                continue

            logging.debug(f"      Is {finger} in ({self.digest_id, digest})?")
            if open_open(self.digest_id, digest, finger):
                logging.debug(f"        Yes, returning finger {finger}")
                return finger, address

        logging.debug(f"      Finger not found. Returning successor {self.successor}")
        return self.successor, self.successor_address


class Command:
    FIND_SUCCESSOR = b'FIND_SUCCESSOR'
    GET_SUCCESSOR_PREDECESSOR = b'GET_PREDECESSOR'
    NOTIFY = b'NOTIFY'
    EXIT = b'EXIT'

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
        return Command.parse(cmd, parameters)


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


# -----------------------------------------------------------------------------
# CLI Helpers
# -----------------------------------------------------------------------------

def finger_table(node):
    fingers = node.fingers
    addresses = node.finger_addresses
    table = [{"position": i, "id": finger, "name": address}
             for i, (finger, address) in enumerate(zip(fingers, addresses)) if finger and address]
    return {"name": node.get_name(), "id": node.get_id(), "fingers": table}


def finger_table_links(node):
    table = finger_table(node)
    table['successor'] = node.successor
    table['predecessor'] = node.predecessor

    return table


def handle_shutdown(name, address, internal_port):
    endpoint = f'{address}:{internal_port}'
    digest = hash_value(name)

    try:
        context = zmq.Context()
        shutdown_socket = context.socket(zmq.ROUTER)
        shutdown_socket.connect(endpoint)
        time.sleep(0.5)

        identity = struct.pack('i', digest)
        shutdown_socket.send(identity, zmq.SNDMORE)
        shutdown_socket.send(Command.EXIT)
    finally:
        shutdown_socket.disconnect(endpoint)
        context.destroy()


def handle_new_node(name, address, external_port, internal_port, action, max_retries,
                    known_endpoint, known_name, stabilize_interval, fix_fingers_interval):
    node = Node(name, hash_value(name), address, external_port, internal_port)
    if action == 'join':
        if not known_endpoint or not known_name:
            return 1, 'Error: Could not join network. Must have known name and known address to join network'

        joined = node.join(hash_value(known_name), known_endpoint)
        for i in range(max_retries):
            if joined:
                break
            name = f'node_{randrange(999)}'
            node = Node(name, hash_value(name), address, external_port, internal_port)
            joined = node.join(hash_value(known_name), known_endpoint)

        if not joined:
            return 2, 'Error: Unable to join network. Max retries reached.'

    node_t = threading.Thread(target=node.run, args=[stabilize_interval, fix_fingers_interval])
    node_t.start()

    return 0, node


def port(port_val):
    url = urlparse(f"//:{port_val}")
    if url.port:
        return port_val


def config_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('action', choices=['create', 'join', 'shutdown'],
                        help='create to create a network, i.e. this node is the first to join.\n'
                             'join to join an existing network')
    parser.add_argument('name', type=str, help='Name of node to create')
    parser.add_argument('address', type=str, help='Address of node')

    parser.add_argument('--known-endpoint', '-ke', type=str,
                        help='Endpoint of node in network. Required to join an existing network.')
    parser.add_argument('--known-name', '-kn', type=str,
                        help='Name of a node in network. Required to join an existing network.')

    parser.add_argument('--internal-port', '-i', type=port, default=None,
                        help='port for chord node to receive messages from other chord nodes')
    parser.add_argument('--external-port', '-e', type=port, default=None,
                        help='port for clients to communicate with chord node')
    parser.add_argument('--stabilize-interval', '-s', type=int, default=60,
                        help='seconds between stabilize executions')
    parser.add_argument('--fix-fingers-interval', '-f', type=int, default=50,
                        help='seconds between fix fingers executions')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Print less log info')

    parser.add_argument('--max-retries', '-r', type=int, default=0,
                        help='number of times to retry joining the network with new, generated name')

    return parser


def main():
    pp = pprint.PrettyPrinter()

    parser = config_parser()
    args = parser.parse_args()

    action = args.action
    name = args.name
    address = args.address

    known_endpoint = args.known_endpoint
    known_name = args.known_name

    external_port = args.external_port
    internal_port = args.internal_port
    stabilize_interval = args.stabilize_interval
    fix_fingers_interval = args.fix_fingers_interval
    quiet = args.quiet

    max_retries = args.max_retries

    if action == 'create' or action == 'join':
        result = handle_new_node(name, address, external_port, internal_port, action,
                                 max_retries, known_endpoint, known_name, stabilize_interval,
                                 fix_fingers_interval)
        if result[0] != 0:
            print(result[1], file=sys.stderr)
            exit(result[0])

        node = result[1]
        print(f'Node {node.name} joined network')

        while not quiet:
            pp.pprint(finger_table_links(node))
            if node.shutdown:
                break
            time.sleep(30)

    elif action == 'shutdown':
        print('Shutting down...')
        handle_shutdown(name, address, internal_port)
        print(f'Shutdown node {name}')


if __name__ == '__main__':
    main()
