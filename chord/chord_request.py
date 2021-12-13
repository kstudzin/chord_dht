import argparse
import random
import socket
import struct
import time
from concurrent.futures import ThreadPoolExecutor

import zmq

from node import RoutingInfo, FindSuccessorCommand

default_trials = 10


def wait_for_response(receiver):
    return receiver.recv_pyobj().recipient


def config_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--search')
    parser.add_argument('bootstrap_endpoint')
    parser.add_argument('--id', default=256)
    parser.add_argument('--port', default='5550')

    return parser


def main():
    parser = config_parser()
    args = parser.parse_args()

    search_term = int(args.search)
    bootstrap_endpoint = args.bootstrap_endpoint
    id = int(args.id)
    port = args.port
    random_search = False if args.search is None else True
    num_trials = default_trials if args.search is None else 1

    bootstrap_id = 1
    endpoint = f'tcp://{socket.gethostbyname(socket.gethostname())}:{port}'

    # Start dealer waiting
    print('Creating ZMQ Context')
    context = zmq.Context()

    identity = struct.pack('i', id)
    receiver = context.socket(zmq.DEALER)
    receiver.setsockopt(zmq.LINGER, 0)
    receiver.setsockopt(zmq.IDENTITY, identity)
    receiver.bind(endpoint)

    # ZMQ sockets
    print('Creating router socket')
    router = context.socket(zmq.ROUTER)
    router.connect(bootstrap_endpoint)
    time.sleep(1)

    print('Creating thread pool executor')
    executor = ThreadPoolExecutor()

    # Find successor command
    me = RoutingInfo(address=endpoint, digest=id, parent_digest=id)
    cn = RoutingInfo(address=bootstrap_endpoint, digest=bootstrap_id, parent_digest=bootstrap_id)

    print('Running tests...')
    file = open('times.csv', 'w')
    for i in range(num_trials):
        future = executor.submit(wait_for_response, receiver=receiver)
        time.sleep(1)

        # print('Creating find successor command')
        if random_search:
            search_term = random.randrange(0, 255)
        cmd = FindSuccessorCommand(initiator=me, recipient=cn, search_digest=search_term)

        # Send message
        # print(f'Chord Node: {bootstrap_endpoint} ({bootstrap_id})')
        print(f'Command: {cmd}')
        start = time.time()
        router.send(struct.pack('i', bootstrap_id), zmq.SNDMORE)
        router.send_pyobj(cmd)

        # Wait for response
        # print('Waiting on future')
        result = future.result()
        end = time.time()

        file.write(f'{result.digest},{result.address},{end - start}\n')

    file.close()
    executor.shutdown()


if __name__ == '__main__':
    main()
