import argparse
import logging
import pprint
import socket
import struct
import threading
import time
import random
from urllib.parse import urlparse

import zmq

from util import open_closed, open_open, request
from hash import NUM_BITS, hash_value

# -----------------------------------------------------------------------------
# Networked Chord Implementation
# -----------------------------------------------------------------------------

# Define milliseconds PAIR sockets should wait for main thread to acknowledge
# command is complete
STABILIZE_WAIT = 1000
FIX_FINGERS_WAIT = 1000


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

    def __str__(self):
        return f'digest: {self.digest}, parent_digest: {self.parent_digest}, address: {self.address}'

    def __repr__(self):
        return f'{vars(self)}'

    def __eq__(self, other):
        return other and \
               self.digest == other.digest and \
               self.parent_digest == other.parent_digest and \
               self.address == other.address


class Node:

    def __init__(self, node_name, node_id, address, external_port=None, internal_port=None, virtual={}):
        endpoint_fmt = 'tcp://{0}:{1}'

        # Node identification
        self.name = node_name
        self.digest_id = node_id

        # ZMQ sockets
        self.context = zmq.Context()
        self.router = self.context.socket(zmq.ROUTER)
        self.router.setsockopt(zmq.LINGER, 0)

        print(f'External endpoint: {address}:{external_port}')
        if external_port:
            self.external_endpoint = endpoint_fmt.format(address, external_port)
            self.router.bind(self.external_endpoint)
        else:
            port = self.router.bind_to_random_port(address)
            self.external_endpoint = endpoint_fmt.format(address, port)

        identity = struct.pack('i', self.digest_id)
        self.receiver = self.context.socket(zmq.DEALER)
        self.receiver.setsockopt(zmq.LINGER, 0)
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

        request.debug(f'Node created: [name: {self.name}, id: {self.digest_id}, external address: {self.external_endpoint}, internal  address: {self.internal_endpoint}]')

    def create_virtual_nodes(self, virtual):
        virtual_node_type = self.get_virtual_node_type()

        virtual_nodes = {digest: virtual_node_type(name, digest, self.digest_id, self.internal_endpoint)
                         for name, digest in virtual.items()}

        # Add the host last so that if the same digest was used in virtual nodes dictionary, this will
        # override it and ensure that the name of the node is correct
        virtual_nodes[self.digest_id] = virtual_node_type(self.name, self.digest_id, self.digest_id,
                                                          self.internal_endpoint)

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

    def create(self):
        # When there is only one node in the network, the virtual nodes must still be connected
        # for the synchronization protocols to work. No nodes are running at this point so we
        # can't use the join call, but because all of the the nodes in the network are on the
        # current machine, we can calculate the successors locally.
        #
        # Keep computation out of constructor because it only needs to be done for one node in the network

        # If there is 1 node, then the successor and predecessor set in the constructor are correct
        if len(self.virtual_nodes) > 1:
            node_iter = iter(self.virtual_nodes.values())
            node1 = next(node_iter)
            node2 = next(node_iter)
            node1.successor = node2.routing_info
            node2.successor = node1.routing_info

            for node in node_iter:

                digest = node.get_digest()
                found, next_node, hops = node1.find_successor(digest, 0)
                while not found:
                    node = self.virtual_nodes[next_node.get_digest()]
                    found, next_node, hops = node.find_successor(digest, hops)
                node.successor = next_node

        return len(self.virtual_nodes)

    def join(self, known_id, known_address):
        logging.debug(f'Node {self.digest_id} at {self.internal_endpoint} joining '
                      f'known node {known_id} at {known_address}')

        for v_node in self.virtual_nodes.values():
            success = self.join_vnode(known_id, known_address, v_node)
            if not success:
                self.virtual_nodes.pop(v_node.get_digest())

        # TODO - log an error if there are no virtual nodes at this point

        return len(self.virtual_nodes)

    def join_vnode(self, known_id, known_address, virtual_node):
        recipient = RoutingInfo(known_id, known_id, known_address)
        cmd = FindSuccessorCommand(search_digest=virtual_node.get_digest(),
                                   initiator=virtual_node.routing_info,
                                   recipient=recipient)
        logging.debug(f'Virtual node {virtual_node.get_digest()} is sending command: {cmd}')
        self.route_result(known_address, known_id, cmd)

        # Block waiting for result. We can't start execution without know our successor
        # Because loop has not started, socket is not being used. We can wait for the message here
        result = self.receiver.recv_pyobj()
        virtual_node.successor = result.recipient

        # If the found successor has the same id as we do, there is already
        # a node the same value in the network and we cannot join with that id
        if virtual_node.successor.get_digest() == virtual_node.get_digest():
            return False

        logging.debug(f'Node {virtual_node.get_digest()} initialized successor '
                      f'{virtual_node.successor.get_digest()} at {virtual_node.successor.get_address()}')
        return True

    def run_stabilize(self, context, interval, shutdown_event):
        pair = context.socket(zmq.PAIR)
        pair.setsockopt(zmq.LINGER, 0)
        pair.connect(self.stabilize_address)

        try:
            while not shutdown_event.is_set():
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
        cmd = PredecessorCommand(initiator=v_node.routing_info)
        pair.send_pyobj(cmd)

        # While we don't use the results received, it is important to acknowledge that the successor
        # has been updated before continuing with the stabilization protocol because the next step
        # involves notifying the new successor of the current nodes existence. If we don't wait for this
        # acknowledgement, we may end up notifying the old successor
        if pair.poll(STABILIZE_WAIT, zmq.POLLIN) == zmq.POLLIN:
            success = pair.recv_pyobj()
            if not success:
                logging.warning(f'Node {v_node.get_parent()} unable to update successor for '
                                f'virtual node {v_node.get_digest()}')
        else:
            # TODO implement successor lists to handle cases where successor fails
            logging.debug(f'Node {v_node.get_parent()}, Virtual Node {v_node.get_digest()} stabilize did not receive '
                          f'response from successor in {STABILIZE_WAIT} milliseconds. Continuing')

    @staticmethod
    def _notify_successor(pair, v_node):
        cmd = NotifyCommand(initiator=v_node.routing_info)
        pair.send_pyobj(cmd)

        # Note that other synchronization processes (updating successor, fixing fingers) wait for a response.
        # Those protocols require information to be sent back to the initiating node for processing. Once that
        # processing is done, the node sends a message to the thread the task is complete and the task movies on.
        # Notify is different from the other synchronization processes because it does not send information back to
        # the initiating node. We make notify asynchronous because we don't want to add network traffic just for
        # the purpose of being synchronous.

    def run_fix_fingers(self, context, interval, shutdown_event):
        pair = context.socket(zmq.PAIR)
        pair.setsockopt(zmq.LINGER, 0)
        pair.connect(self.fix_fingers_address)

        try:
            while not shutdown_event.is_set():
                self._fix_fingers(pair)
                time.sleep(interval)
        finally:
            pair.close()

    def _fix_fingers(self, pair):
        for v_node in self.virtual_nodes.values():
            logging.debug(f"Building finger table for {v_node.name} (Digest: {v_node.get_digest()})")

            random_index = random.randint(0, NUM_BITS - 1)
            next_key = (v_node.get_digest() + pow(2, random_index)) % (pow(2, NUM_BITS) - random_index)
            self._find_successor(pair, next_key, v_node.routing_info, random_index)
            logging.debug(f"  Found finger {random_index} is successor({next_key}) = {v_node.fingers[random_index]}")

    @staticmethod
    def _find_successor(pair, digest, initiator, index):
        cmd = FindSuccessorCommand()
        cmd.initiator = initiator
        cmd.recipient = initiator
        cmd.return_data = index
        cmd.search_digest = digest

        pair.send_pyobj(cmd)

        if pair.poll(STABILIZE_WAIT, zmq.POLLIN) == zmq.POLLIN:
            success = pair.recv_pyobj()
            if not success:
                logging.error(f'Node {initiator.get_parent()} unable to update finger {index} '
                              f'on virtual node {initiator.get_digest()}')
        else:
            logging.debug(f'Node {initiator.get_parent()}, Virtual Node {initiator.get_digest()}: fix fingers did '
                          f'not receive response in {FIX_FINGERS_WAIT} milliseconds. Continuing.')

    def run(self, stabilize_interval=5, fix_fingers_interval=7):
        logging.info(f'Starting loop for node {self.digest_id}')
        logging.info(f'Node {self.digest_id} managing virtual nodes: {self.virtual_nodes.keys()}')

        # Create PAIR socket for stabilize
        stability = self.context.socket(zmq.PAIR)
        stability.setsockopt(zmq.LINGER, 0)
        stability.bind(self.stabilize_address)
        logging.debug(f'Stabilize using address {self.stabilize_address}')

        # Create PAIR socket for fix_fingers
        fix_fingers = self.context.socket(zmq.PAIR)
        fix_fingers.setsockopt(zmq.LINGER, 0)
        fix_fingers.bind(self.fix_fingers_address)
        logging.debug(f'Fix fingers using address {self.fix_fingers_address}')

        # Create Poller to listen for messages on all sockets
        poller = zmq.Poller()
        poller.register(self.receiver, zmq.POLLIN)
        poller.register(stability, zmq.POLLIN)
        poller.register(fix_fingers, zmq.POLLIN)
        logging.debug('Poller listening to receiver, stability, and fix_fingers')

        shutdown_event = threading.Event()
        logging.debug('Created shutdown event')

        # Start stabilize thread
        if stabilize_interval:
            logging.debug('Starting stabilize thread...')
            stability_t = threading.Thread(target=self.run_stabilize,
                                           args=[self.context, stabilize_interval, shutdown_event],
                                           daemon=True)
            stability_t.start()

        # Start fix fingers thread
        if fix_fingers_interval:
            logging.debug('Starting fix fingers thread...')
            fix_fingers_t = threading.Thread(target=self.run_fix_fingers,
                                             args=[self.context, fix_fingers_interval, shutdown_event],
                                             daemon=True)
            fix_fingers_t.start()

        try:
            while True:

                logging.debug(f'Node {self.digest_id} waiting for messages')
                socks = dict(poller.poll())
                received_exit = self.process_input(socks, stability, fix_fingers)
                if received_exit:
                    shutdown_event.set()
                    break

            logging.info(f'Node {self.digest_id} shutting down...')
            logging.info(f'Node state: {[vars(v_node) for v_node in self.virtual_nodes.values()]}')

        # TODO notify successors and predecessors of known departure

        finally:
            logging.debug(f'Node {self.digest_id} destroying context...')

            fix_fingers_t.join()
            stability_t.join()
            fix_fingers.close()
            stability.close()

            self.receiver.close()
            self.router.close()
            self.context.term()

            self.shutdown = True

        logging.info(f'Node {self.digest_id} says Goodbye!')

    def process_input(self, socks, stability, fix_fingers):
        logging.debug(f'Node {self.digest_id} processing {len(socks)} messages')
        for sock in socks:

            # Receive command object
            command = sock.recv_pyobj()
            logging.debug(f'Node {self.digest_id} received command {command}')

            if isinstance(command, FindSuccessorCommand) and command.initiator.digest != 1:
                request.debug(f'Node {self.digest_id} received command {command}')

            if command == EXIT_COMMAND:
                logging.debug(f'Node {self.digest_id} received EXIT message. Node shutting down.')
                return True

            # Process the command
            result = command.execute(self)

            # Process results
            if result:
                address = result.get_address()
                identity = result.get_parent()

                if address == self.stabilize_address and not identity:
                    stability.send_pyobj(True)
                elif address == self.fix_fingers_address and not identity:
                    fix_fingers.send_pyobj(True)
                else:
                    self.route_result(address, identity, command)

            return False

    def route_result(self, address, identity, command):
        logging.debug(f'Node {self.digest_id} sending {command} to node {identity} at {address}')
        if address not in self.connected:
            self.connected.add(address)
            self.router.connect(address)
            time.sleep(.5)

        identity_b = struct.pack('i', identity)
        self.router.send(identity_b, zmq.SNDMORE)
        self.router.send_pyobj(command)


class ChordNode(Node):

    def __init__(self, node_name, node_id, address, external_port=None, internal_port=None, virtual={}):
        super().__init__(node_name, node_id, address, external_port, internal_port, virtual)

    @staticmethod
    def get_virtual_node_type():
        return ChordVirtualNode


# TODO extract common logic to command
# TODO refactor if/else in execute() to state pattern
# TODO optimize requests on the same host
# TODO move commands to their own module
class Command:

    def execute(self, node):
        pass

    def __repr__(self):
        return f'{type(self).__name__}: {vars(self)}'


class ExitCommand(Command):
    """ Command to signal the server to shutdown"""

    def __init__(self):
        pass

    def execute(self, node):
        # TODO raise error
        # Unlike java, in python exceptions can be used as signals
        # https://softwareengineering.stackexchange.com/a/351121/392415
        pass

    def __eq__(self, other):
        # Idea was to use a singleton because exit has no particular state
        # But that is impractical because exit will be initiated by a separate
        # process and sharing memory for this use case is overkill
        # This is the alternative but a better approach would be for execute()
        # to raise an exception
        return type(other) == ExitCommand


class NotifyCommand(Command):

    def __init__(self, initiator=None, recipient=None):
        self.initiator = initiator
        self.recipient = recipient

    def execute(self, node):
        if not self.recipient and self.initiator.digest in node.virtual_nodes:
            self.recipient = node.virtual_nodes[self.initiator.digest].successor
            return self.recipient
        elif self.recipient.digest in node.virtual_nodes:
            node.virtual_nodes[self.recipient.digest].notify(self.initiator)
        else:
            logging.error(f'Node {node.digest_id} unable to execute {self}')


class PredecessorCommand(Command):

    def __init__(self, initiator=None, recipient=None, successors_predecessor=None):
        self.initiator = initiator
        self.recipient = recipient
        self.successors_predecessor = successors_predecessor

    def execute(self, node):
        if not self.recipient and \
                not self.successors_predecessor and \
                self.initiator.digest in node.virtual_nodes:
            # Set the recipient
            self.recipient = node.virtual_nodes[self.initiator.digest].successor
            return self.recipient
        elif not self.successors_predecessor and \
                self.recipient.digest in node.virtual_nodes:
            # Return to initiator
            self.successors_predecessor = node.virtual_nodes[self.recipient.digest].predecessor
            return self.initiator
        elif self.initiator.digest in node.virtual_nodes:
            # Initiator updates successor
            node.virtual_nodes[self.initiator.digest].update_successor(self.successors_predecessor)
            return RoutingInfo(address=node.stabilize_address)
        else:
            logging.error(f'Node {node.digest_id} unable to execute {self}')


class FindSuccessorCommand(Command):

    # TODO handle get/put requests from clients

    def __init__(self, initiator=None, recipient=None, hops=0, found=False,
                 search_digest=None, return_data=None):
        self.initiator = initiator
        self.recipient = recipient

        self.hops = hops
        self.found = found

        self.search_digest = search_digest
        self.return_data = return_data

    def execute(self, node):
        logging.debug(f'Node {node.digest_id} executing command: {vars(self)}')

        if self.initiator.digest != 1:
            request.debug(f'Current state: {self}')

        if self.found and self.initiator.digest in node.virtual_nodes:
            if self.initiator.digest != 1:
                request.debug(f'Found the search term')
            return self.update_node(node)
        elif self.recipient.digest in node.virtual_nodes:
            if self.initiator.digest != 1:
                request.debug('Searching for term')
            v_node = node.virtual_nodes[self.recipient.digest]
            if self.initiator.digest != 1:
                request.debug(f'Found v_node: {v_node}')
            self.found, self.recipient, self.hops = v_node.find_successor(self.search_digest, self.hops)
            if self.initiator.digest != 1:
                request.debug(f'Left find_successor: {self.found}, {self.recipient}, {self.hops}')
            return self.forward_result()
        else:
            logging.error(f'Node {node.digest_id} unable to execute {self}')
            request.error(f'Unable to execute')

    def client_response(self):
        # if return_data has value `put`
        # else `get`
        message = None
        return self.initiator

    def update_node(self, node):
        # If the current node is the initiator, then it has received its response and must
        # process/store the information appropriately
        v_node = node.virtual_nodes[self.initiator.digest]
        index = self.return_data
        v_node.fingers[index] = self.recipient
        if index == 0:
            v_node.successor = self.recipient
        node.router.connect(self.recipient.address)
        node.connected.add(self.recipient.address)
        return RoutingInfo(address=node.fix_fingers_address)

    def forward_result(self):
        if self.found:
            # If successor is found and the initiator has a digest set, the result
            # is sent to another node in the network
            return self.initiator
        else:
            # If the successor is found and the initiator does not have a digest set,
            # we have a client request. This result needs to be forwarded to the found successor
            # which will handle the response to the client
            #
            # If the successor is not found, the search for the successor is forwarded to the result
            # found on this node
            return self.recipient


EXIT_COMMAND = ExitCommand()


# -----------------------------------------------------------------------------
# CLI Helpers
# -----------------------------------------------------------------------------


def finger_table_links(node):
    return [vars(v_node) for v_node in node.virtual_nodes.values()]


def to_int(digest):
    return int(digest)


def handle_shutdown(name, address, internal_port, hash_func):
    endpoint = f'{address}:{internal_port}'
    digest = hash_func(name)

    try:
        context = zmq.Context()
        shutdown_socket = context.socket(zmq.ROUTER)
        shutdown_socket.connect(endpoint)
        time.sleep(0.5)

        identity = struct.pack('i', digest)
        shutdown_socket.send(identity, zmq.SNDMORE)
        shutdown_socket.send_pyobj(EXIT_COMMAND)
    finally:
        shutdown_socket.close()
        context.destroy()


def handle_new_node(name, address, external_port, internal_port, action,
                    known_endpoint, known_name, stabilize_interval, fix_fingers_interval,
                    node_type, hash_func, virtual_nodes):
    node = node_type(name, hash_func(name), address, external_port, internal_port, dict(virtual_nodes))

    if action == 'create':
        num_added = node.create()
    elif action == 'join':
        if not known_endpoint or not known_name:
            raise ValueError('join action requires known name and known address')

        num_added = node.join(hash_func(known_name), known_endpoint)

    node_t = threading.Thread(target=node.run, args=[stabilize_interval, fix_fingers_interval])
    node_t.start()

    return node, node_t


def virtual_node(v_node):
    split = v_node.split(':')
    return split[0], int(split[1])


def port(port_val):
    url = urlparse(f"//:{port_val}")
    if url.port:
        return port_val


def config_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('action', choices=['create', 'join', 'shutdown'],
                        help='create to create a network, i.e. this node is the first to join.\n'
                             'join to join an existing network')
    parser.add_argument('name', type=str, help='Name of node to create. When --real-hashes is NOT specified, '
                                               'the name should be the digest.')
    # parser.add_argument('address', type=str, help='Address of node')

    parser.add_argument('--known-endpoint', '-ke', type=str,
                        help='Endpoint of node in network. Required to join an existing network.')
    parser.add_argument('--known-name', '-kn', type=str,
                        help='Name of a node in network. Required to join an existing network.')

    parser.add_argument('--internal-port', '-i', type=port, default=None,
                        help='port for chord node to receive messages from other chord nodes')
    parser.add_argument('--external-port', '-e', type=port, default=None,
                        help='port for clients to communicate with chord node')
    parser.add_argument('--stabilize-interval', '-s', type=int, default=15,
                        help='seconds between stabilize executions')
    parser.add_argument('--fix-fingers-interval', '-f', type=int, default=10,
                        help='seconds between fix fingers executions')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Print less log info')

    parser.add_argument('--virtual-nodes', '-vn', type=virtual_node, nargs='+', default=[],
                        metavar='node_name:digest',
                        help='Space separated list of virtual nodes to run. Each virtual node is identified by a colon '
                             'separated string containing its node name and digest ')
    parser.add_argument('--real-hashes', '-rh', action='store_const', const=hash_value,
                        help='By default, hashes are artificially generated to avoid duplicates in '
                             'the small address space. This option allows using real hashes.')

    node_type_group = parser.add_mutually_exclusive_group()
    node_type_group.add_argument('--naive-nodes', action='store_const', const=Node,
                                 help='Build naive nodes. Only useful with \'hops\' action. Cannot be used with '
                                      'another node type')
    node_type_group.add_argument('--chord-nodes', action='store_const', const=ChordNode,
                                 help='Build chord nodes. Cannot be used with another node type')

    return parser


def main():
    parser = config_parser()
    args = parser.parse_args()

    action = args.action
    name = args.name
    address = socket.gethostbyname(socket.gethostname())

    output = open(f'/opt/chord/out{name}.log', 'w')
    output.write(f'Starting chord node {name} at {address}')

    known_endpoint = args.known_endpoint
    known_name = args.known_name

    external_port = args.external_port
    internal_port = args.internal_port
    stabilize_interval = args.stabilize_interval
    fix_fingers_interval = args.fix_fingers_interval
    quiet = args.quiet
    virtual_nodes = args.virtual_nodes

    hash_func = next(hash_func for hash_func in [args.real_hashes, to_int]
                     if hash_func is not None)

    # Retrieve first non None value
    node_type = next(node_type
                     for node_type in [args.chord_nodes, args.naive_nodes, ChordNode]
                     if node_type is not None)

    if action == 'create' or action == 'join':

        node, node_t = handle_new_node(name, address, external_port, internal_port, action,
                                       known_endpoint, known_name, stabilize_interval,
                                       fix_fingers_interval, node_type, hash_func, virtual_nodes)

        print(f'Node {node.name} joined network with {len(node.virtual_nodes)} virtual node(s)')
        # TODO - exit with error code if no nodes were added to network

        while node_t.is_alive():
            if not quiet:
                print(finger_table_links(node), output)
            node_t.join(30)

    elif action == 'shutdown':

        output.write('Shutting down...')
        handle_shutdown(name, address, internal_port, hash_func)
        output.write(f'Shutdown node {name}')

    output.close()


if __name__ == '__main__':
    main()
