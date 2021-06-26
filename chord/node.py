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


class VirtualNode:

    def __init__(self, name, digest, parent_digest, endpoint):
        self.name = name
        self.routing_info = RoutingInfo(digest, parent_digest, endpoint)
        self.successor = self.routing_info
        self.predecessor = self.routing_info
        self.fingers = [None] * NUM_BITS

    def get_digest(self):
        return self.routing_info.get_digest()

    def get_parent(self):
        return self.routing_info.get_parent()

    def get_address(self):
        return self.routing_info.get_address()

    def find_successor(self, digest, hops):
        if digest == self.routing_info.digest:
            return True, self.routing_info, hops

        logging.debug(f"    Is id {digest} contained in ({self.get_digest()}, {self.successor.get_digest()}]?")
        if open_closed(self.get_digest(), self.successor.get_digest(), digest):

            # We have found the successor and will return it to the requester
            logging.debug(f"      Yes, returning successor {self.successor.get_digest()} hops: {hops}")
            return True, self.successor, hops + 1
        else:

            # We have not found the successor of the digest. Return the next node
            # to advance to. For the naive nodes, this is also the successor. For
            # chord nodes, this is either a node from the finger table or the successor
            logging.debug(f"      No, finding closest preceding node")
            next_node = self.find_next_node(digest)
            return False, next_node, hops + 1

    def find_next_node(self, digest):
        return self.successor

    def notify(self, other):
        logging.debug(f'Node {self.routing_info.digest} notified by node {other.digest}')
        if not self.predecessor \
                or open_open(self.predecessor.digest, self.routing_info.digest, other.digest):
            logging.debug(f'Node {self.routing_info.digest} updating predecessor')
            self.predecessor = other

    def update_successor(self, other):
        if other.digest and \
                open_open(self.routing_info.digest, self.successor.digest, other.digest):
            self.successor = other


class ChordVirtualNode(VirtualNode):

    def find_next_node(self, digest):
        return self.closest_preceding_node(digest)

    def closest_preceding_node(self, digest):

        for finger in reversed(self.fingers):
            if not finger:
                continue

            logging.debug(f"      Is {finger.digest} in ({self.routing_info.digest, digest})?")
            if open_open(self.routing_info.digest, digest, finger.digest):
                logging.debug(f"        Yes, returning finger {finger.digest}")
                return finger

        logging.debug(f"      Finger not found. Returning successor {self.successor.digest}")
        return self.successor


class RoutingInfo:

    def __init__(self, digest=None, parent_digest=None, address=None):
        self.digest = digest
        self.parent_digest = parent_digest
        self.address = address

    def get_digest(self):
        return self.digest

    def get_parent(self):
        return self.parent_digest

    def get_address(self):
        return self.address

    def to_dict(self):
        return vars(self)

    def __str__(self):
        return f'RoutingInfo: digest: {self.digest}, parent_digest: {self.parent_digest}, address: {self.address}'

    def __repr__(self):
        return f'RoutingInfo: {vars(self)}'

    def __eq__(self, other):
        return other and \
               self.digest == other.digest and \
               self.parent_digest == other.parent_digest and \
               self.address == other.address


class Node:

    def __init__(self, node_name, node_id, address, external_port=None, internal_port=None, virtual={}):
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

        self.virtual_nodes = self.create_virtual_nodes(virtual)

    def create_virtual_nodes(self, virtual):
        virtual_node_type = self.get_virtual_node_type()

        virtual_nodes = {digest: virtual_node_type(name, digest, self.digest_id, self.internal_endpoint)
                         for name, digest in virtual.items()}
        virtual_nodes[self.digest_id] = virtual_node_type(self.name, self.digest_id, self.digest_id, self.internal_endpoint)

        return virtual_nodes

    @staticmethod
    def get_virtual_node_type():
        return VirtualNode

    def get_name(self):
        return self.name

    def get_id(self):
        return self.digest_id

    def get_virtual_node(self, virtual_node_digest: int) -> VirtualNode:
        return self.virtual_nodes[virtual_node_digest]

    def fix_fingers_loop(self, context, interval):
        pair = context.socket(zmq.PAIR)
        pair.connect(self.fix_fingers_address)

        try:
            while True:
                self._init_fingers(pair)
                time.sleep(interval)
        finally:
            pair.close()

    def _init_fingers(self, pair):
        for v_node in self.virtual_nodes.values():
            logging.debug(f"Building finger table for {v_node.name} (Digest: {v_node.get_digest()})")

            i = 0
            next_key = (v_node.get_digest() + pow(2, i)) % (pow(2, NUM_BITS) - 1)
            while i < NUM_BITS:
                self._find_successor(pair, next_key, v_node.routing_info, i)
                logging.debug(f"  Found finger {i} is successor({next_key}) = {v_node.fingers[i]}")

                i += 1
                next_key = (v_node.get_digest() + pow(2, i)) % (pow(2, NUM_BITS) - 1)

    @staticmethod
    def _find_successor(pair: zmq.Socket, digest: int, initiator: RoutingInfo, index: int):
        cmd = FindSuccessorCommand()
        cmd.initiator = initiator
        cmd.recipient = initiator
        cmd.return_data = index
        cmd.search_digest = digest

        pair.send(Command.FIND_SUCCESSOR, zmq.SNDMORE)
        pair.send_json(cmd.to_dict())

        recv_cmd = pair.recv()
        found = pair.recv_json()
        return recv_cmd, found

    def join(self, known_id, known_address):
        logging.debug(f'Node {self.digest_id} at {self.internal_endpoint} joining '
                      f'known node {known_id} at {known_address}')

        for v_node in self.virtual_nodes.values():
            success = self.join_vnode(known_id, known_address, v_node)
            if not success:
                self.virtual_nodes.pop(v_node.get_digest())

        return len(self.virtual_nodes)

    def join_vnode(self, known_id: int, known_address: str, virtual_node: VirtualNode):
        recipient = RoutingInfo(known_id, known_id, known_address)
        cmd = FindSuccessorCommand(search_digest=virtual_node.get_digest(),
                                   initiator=virtual_node.routing_info.to_dict(),
                                   recipient=recipient.to_dict())
        logging.debug(f'Virtual node {virtual_node.get_digest()} is sending command: {cmd.to_dict()}')
        self.route_result(known_address, known_id, Command.FIND_SUCCESSOR, cmd.to_dict())

        # Block waiting for result. We can't start execution without know our successor
        # Because loop has not started, we can wait for the message here
        cmd_id = self.receiver.recv()
        result = self.receiver.recv_json()
        logging.debug(f'Virtual node {virtual_node.get_digest()} received response: {result}')

        result_cmd = FindSuccessorCommand(**result)
        virtual_node.successor = result_cmd.recipient

        # If the found successor has the same id as we do, there is already
        # a node the same value in the network and we cannot join with that id
        if virtual_node.successor.get_digest() == virtual_node.get_digest():
            return False

        logging.debug(f'Node {virtual_node.get_digest()} initialized successor '
                      f'{virtual_node.successor.get_digest()} at {virtual_node.successor.get_address()}')
        return True

    def stabilize_loop(self, context, interval):
        pair = context.socket(zmq.PAIR)
        pair.connect(self.stabilize_address)

        try:
            while True:
                self._stabilize(pair)
                time.sleep(interval)
        finally:
            pair.close()

    def _stabilize(self, pair):
        logging.debug(f'Node {self.digest_id} running stabilize')

        for v_node in self.virtual_nodes.values():
            logging.debug(f'Node {v_node.get_digest()} updating successor {v_node.successor.get_digest()}')
            self._get_predecessor(pair, v_node)

            logging.debug(f'Node {v_node.get_digest()} notifying successor {v_node.successor.get_digest()}')
            self._notify_successor(pair, v_node)

    @staticmethod
    def _get_predecessor(pair, v_node):
        cmd = PredecessorCommand(v_node, 0)
        pair.send(Command.GET_SUCCESSOR_PREDECESSOR, zmq.SNDMORE)
        pair.send_json(cmd.to_dict())

        # While we don't use the results received, it is important to acknowledge that the successor
        # has been updated before continuing with the stabilization protocol because the next step
        # involves notifying the new successor of the current nodes existence. If we don't wait for this
        # acknowledgement, we may end up notifying the old successor
        cmd_id = pair.recv()
        message = pair.recv_json()
        return cmd_id, message

    @staticmethod
    def _notify_successor(pair, v_node):
        cmd = NotifyCommand(v_node)
        pair.send(Command.NOTIFY, zmq.SNDMORE)
        pair.send_json(cmd.to_dict())

        # Note that other synchronization processes (updating successor, fixing fingers) wait for a response.
        # Those protocols require information to be sent back to the initiating node for processing. Once that
        # processing is done, the node sends a message to the thread the task is complete and the task movies on.
        # In other words, those are processed synchronously. Notify is different from the other synchronization
        # processes because it does not send information back to the initiating node. We make notify asynchronous
        # because we don't want to add network traffic just for the purpose of being synchronous.

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

                logging.debug(f'Node {self.digest_id} waiting for messages')
                socks = dict(poller.poll())
                received_exit = self.process_input(socks, stability, fix_fingers)
                if received_exit:
                    break

            logging.info(f'Node {self.digest_id} shutting down...')
            logging.info(finger_table_links(self))

        finally:
            logging.debug(f'Node {self.digest_id} destroying context...')
            self.context.destroy()
            self.shutdown = True

        logging.info(f'Node {self.digest_id} says Goodbye!')

    def process_input(self, socks, stability, fix_fingers):
        logging.debug(f'Node {self.digest_id} processing {len(socks)} messages')
        for sock in socks:
            # Receive the message
            cmd = sock.recv()
            if cmd == Command.EXIT:
                logging.debug(f'Node {self.digest_id} received EXIT message. Node shutting down.')
                return True

            message = sock.recv_json()
            logging.debug(f'Node {self.digest_id} received {cmd} message {message}')

            # Process the message
            command = parsers[cmd](**message)
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
        logging.debug(f'Node {self.digest_id} sending {next_cmd} with {parameters} to node {identity} at {address}')
        if address not in self.connected:
            self.connected.add(address)
            self.router.connect(address)
            time.sleep(.5)

        identity_b = struct.pack('i', identity)
        self.router.send(identity_b, zmq.SNDMORE)
        self.router.send(next_cmd, zmq.SNDMORE)
        self.router.send_json(parameters)


class ChordNode(Node):

    def __init__(self, node_name, node_id, address, external_port=None, internal_port=None, virtual={}):
        super().__init__(node_name, node_id, address, external_port, internal_port, virtual)

    @staticmethod
    def get_virtual_node_type():
        return ChordVirtualNode


class Command:
    FIND_SUCCESSOR = b'FIND_SUCCESSOR'
    GET_SUCCESSOR_PREDECESSOR = b'GET_PREDECESSOR'
    NOTIFY = b'NOTIFY'
    EXIT = b'EXIT'

    def execute(self, node):
        pass

    def to_dict(self):
        data = {}
        for attr, value in vars(self).items():
            if type(value) is RoutingInfo:
                data[attr] = vars(value)
            else:
                data[attr] = value
        return data


class NotifyCommand(Command):

    def __init__(self, *args, initiator={}, recipient={}):
        if args:
            self.initiator = args[0].routing_info
            self.recipient = args[0].successor
        else:
            self.initiator = RoutingInfo(**initiator)
            self.recipient = RoutingInfo(**recipient)

    def execute(self, node):
        if self.recipient.digest in node.virtual_nodes:
            node.virtual_nodes[self.recipient.digest].notify(self.initiator)
        else:
            self.recipient = node.virtual_nodes[self.initiator.digest].successor
            return self.recipient.address, self.recipient.parent_digest, Command.NOTIFY, self.to_dict()


class PredecessorCommand(Command):

    def __init__(self, *args, initiator={}, recipient={}, successors_predecessor={}, step=0):
        if args:
            self.initiator = args[0].routing_info
            self.recipient = args[0].successor
            self.successors_predecessor = RoutingInfo()
            self.step = args[1]
        else:
            self.initiator = RoutingInfo(**initiator)
            self.recipient = RoutingInfo(**recipient)
            self.successors_predecessor = RoutingInfo(**successors_predecessor)
            self.step = step

    def execute(self, node):
        if self.step == 0:
            # Send to successor
            self.step += 1
            return self.recipient.address, self.recipient.parent_digest, Command.GET_SUCCESSOR_PREDECESSOR, self.to_dict()
        elif not self.successors_predecessor.digest:
            # Return to initiator
            self.successors_predecessor = node.virtual_nodes[self.recipient.digest].predecessor
            return self.initiator.address, self.initiator.parent_digest, Command.GET_SUCCESSOR_PREDECESSOR, self.to_dict()
        else:
            # Initiator updates successor
            node.virtual_nodes[self.initiator.digest].update_successor(self.successors_predecessor)
            return node.stabilize_address, None, Command.GET_SUCCESSOR_PREDECESSOR, self.to_dict()


class FindSuccessorCommand(Command):

    # TODO handle get/put requests from clients
    # set recipient to receiving node so it calls find_successor first
    # set initiator parent digest and address to client id and address
    #   do not set initiator digest

    def __init__(self, initiator={}, recipient={}, hops=0, found=False,
                 search_digest=None, return_data=None):
        self.initiator = RoutingInfo(**initiator)
        self.recipient = RoutingInfo(**recipient)

        self.hops = hops
        self.found = found

        self.search_digest = search_digest
        self.return_data = return_data

    def execute(self, node):
        logging.debug(f'Node {node.digest_id} executing command: {self.to_dict()}')

        if self.found:
            if not self.initiator.digest:
                return self.client_response()
            else:
                logging.debug(f'Node {node.digest_id} received response')

                # If the current node is the initiator, then it has received its response and must
                # process/store the information appropriately
                v_node = node.get_virtual_node(self.initiator.digest)
                index = self.return_data
                v_node.fingers[index] = self.recipient
                node.router.connect(self.recipient.address)
                node.connected.add(self.recipient.address)
                return node.fix_fingers_address, None, Command.FIND_SUCCESSOR, self.to_dict()
        else:
            v_node = node.get_virtual_node(self.recipient.digest)
            self.found, self.recipient, self.hops = v_node.find_successor(self.search_digest, self.hops)
            return self.forward_result()

    def client_response(self):
        # if return_data has value put
        # else get
        message = None
        return self.initiator.address, self.initiator.parent_digest, Command.FIND_SUCCESSOR, message

    def forward_result(self):
        if self.found and self.initiator.digest:
            # If successor is found and the initiator has a digest set, the result
            # is sent to another node in the network
            return self.initiator.address, self.initiator.parent_digest, Command.FIND_SUCCESSOR, self.to_dict()
        else:
            # If the successor is found and the initiator does not have a digest set,
            # we have a client request. This result needs to be forwarded to the found successor
            # which will handle the response to the client
            #
            # If the successor is not found, the search for the successor is forwarded to the result
            # found on this node
            return self.recipient.address, self.recipient.parent_digest, Command.FIND_SUCCESSOR, self.to_dict()


# def to_dict(obj):
#     data = {}
#     for key, value in vars(object).items():
#         try:
#             data[key] = to_dict(value)
#         except AttributeError:
#             data[key] = value
#
#     logging.debug(f'to_dict() output: {data}')
#     return data


parsers = {Command.FIND_SUCCESSOR: FindSuccessorCommand,
           Command.GET_SUCCESSOR_PREDECESSOR: PredecessorCommand,
           Command.NOTIFY: NotifyCommand}


# -----------------------------------------------------------------------------
# CLI Helpers
# -----------------------------------------------------------------------------

def finger_table(node):
    fingers = node.fingers
    addresses = node.finger_addresses
    table = [{"position": i, "id": finger, "endpoint": address}
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
