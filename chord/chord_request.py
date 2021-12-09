import argparse
import socket
import struct
import time
from concurrent.futures import ThreadPoolExecutor

import zmq

from node import RoutingInfo, FindSuccessorCommand


def wait_for_response(context, id, endpoint):
    identity = struct.pack('i', id)

    receiver = context.socket(zmq.DEALER)
    receiver.setsockopt(zmq.LINGER, 0)
    receiver.setsockopt(zmq.IDENTITY, identity)
    receiver.bind(endpoint)

    return receiver.recv_pyobj().recipient


def config_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('search_term')
    parser.add_argument('bootstrap_endpoint')
    parser.add_argument('--id', default=256)
    parser.add_argument('--port', default='5550')

    return parser


def main():
    parser = config_parser()
    args = parser.parse_args()

    bootstrap_id = 1
    endpoint = f'tcp://{socket.gethostbyname(socket.gethostname())}:{args.port}'


    # Start dealer waiting
    print('Creating ZMQ Context')
    context = zmq.Context()

    print('Creating thread pool executor')
    executor = ThreadPoolExecutor()
    future = executor.submit(wait_for_response, context=context, id=args.id, endpoint=endpoint)

    # ZMQ sockets
    print('Creating router socket')
    router = context.socket(zmq.ROUTER)
    router.setsockopt(zmq.LINGER, 0)
    router.connect(args.bootstrap_endpoint)

    # Find successor command
    print('Creating find successor command')
    me = RoutingInfo(address=endpoint, digest=args.id, parent_digest=args.id)
    cn = RoutingInfo(address=args.bootstrap_endpoint, digest=bootstrap_id, parent_digest=bootstrap_id)
    cmd = FindSuccessorCommand(initiator=me, recipient=cn, search_digest=args.search_term)

    # Send message
    print(f'Chord Node: {args.bootstrap_endpoint} ({bootstrap_id})')
    print(f'Command: {cmd}')
    start = time.time()
    router.send(struct.pack('i', bootstrap_id), zmq.SNDMORE)
    router.send_pyobj(cmd)

    # Wait for response
    print('Waiting on future')
    result = future.result()
    end = time.time()
    executor.shutdown()

    print(f'{result.digest},{result.address},{end - start}')


if __name__ == '__main__':
    main()
