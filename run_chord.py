import argparse
import os
import random
import sys
import time

from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import Controller
from mininet.topo import SingleSwitchTopo, Topo

from chord.hash import NUM_BITS


name_fmt = 'node_{id}'
cmd_fmt = 'python chord/node.py {action} {name} tcp://{ip} --internal-port 5555 ' \
          '--external-port 5556 --stabilize-interval {stabilize_interval} ' \
          '--fix-fingers-interval {fix_fingers_interval} {ext} {virtual} &'
join_fmt_ext = '--known-endpoint tcp://{ip}:5555 --known-name {name}'
shutdown_cmd_fmt = 'python chord/node.py shutdown {name} tcp://{ip} --internal-port 5555'


class SingleSwitchTopo(Topo):
    """Single switch connected to n hosts."""

    def build(self, n=2):
        switch = self.addSwitch('s1')
        # Python's range(N) generates 0..N-1
        for h in range(n):
            host = self.addHost('h%s' % (h + 1))
            self.addLink(host, switch)


def generate_hash():
    random.seed(0)
    max_value = pow(2, NUM_BITS)
    valid_hashes = range(max_value)
    for hash_val in random.sample(valid_hashes, max_value):
        yield hash_val


def create_network(n_hosts):
    """Create and test a simple network"""

    topo = SingleSwitchTopo(n=n_hosts)

    return Mininet(topo=topo, controller=Controller)


def config_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('nodes', type=int, default=10,
                        help='Number of nodes in network')

    parser.add_argument('--stabilize-interval', '-s', type=int, default=15,
                        help='seconds between stabilize executions')
    parser.add_argument('--fix-fingers-interval', '-f', type=int, default=10,
                        help='seconds between fix fingers executions')
    parser.add_argument('--wait-per-node', '-w', type=int, default=10,
                        help='amount of time (in seconds) to wait per node for the network to stabilize')

    # TODO - should be able to have different numbers of virtual nodes on each node
    parser.add_argument('--nodes-per-host', '-nph', type=int, default=1,
                        help='Number of nodes hosted on a single instance.')

    return parser


def main():
    parser = config_parser()
    args = parser.parse_args()

    stabilize_interval = args.stabilize_interval
    fix_fingers_interval = args.fix_fingers_interval
    wait_per_node = args.wait_per_node

    num_nodes = args.nodes
    if not num_nodes < pow(2, NUM_BITS):
        print(f'Cannot create {num_nodes} nodes in {NUM_BITS}-bit address space', file=sys.stderr)
        exit(1)

    num_virtual = args.nodes_per_host - 1
    if not ((num_virtual + 1) * num_nodes) < pow(2, NUM_BITS):
        print(f'Cannot create {num_virtual} hosted nodes in {NUM_BITS}-bit address space', file=sys.stderr)
        exit(1)

    # Create and start network
    net = create_network(num_nodes)
    net.start()

    # Move old log into logs dir to ensure we have a fresh log
    os.makedirs('logs', exist_ok=True)
    if os.path.isfile('chord.log'):
        os.rename('chord.log',
                  os.path.join('logs', f'chord_{time.time()}.log'))

    # In order to guarantee that we can specify the exact number of nodes/virtual nodes
    # and avoid hash collisions, we will generate random numbers in the address space and
    # use those as if they were hashes
    hashes = generate_hash()

    node2name = {}
    for i, node in enumerate(net.hosts):

        name = next(hashes)
        if num_virtual:
            virtual = '--virtual-nodes '
            # Iterator
            for j in range(num_virtual):
                digest = next(hashes)
                virtual += f'vnode_{digest}:{digest} '
        else:
            virtual = ''

        if i == 0:
            action = 'create'
            ext = ''
            join_ext = join_fmt_ext.format(ip=node.IP(), name=name)
        else:
            action = 'join'
            ext = join_ext

        node2name[node] = name
        cmd = cmd_fmt.format(action=action, name=name, ip=node.IP(), ext=ext,
                             stabilize_interval=stabilize_interval,
                             fix_fingers_interval=fix_fingers_interval,
                             virtual=virtual)

        print(f'Starting node {name}: {cmd}')
        node.cmd(cmd)

    # Allow stabilize and finger node processes to complete
    total_wait = wait_per_node * num_nodes * (num_virtual + 1)
    print(f'Waiting {total_wait} seconds for network to stabilize...')
    time.sleep(total_wait)

    # Send shut down commands
    for node, name in node2name.items():
        cmd = shutdown_cmd_fmt.format(ip=node.IP(), name=name)
        print(f'Shutting down node {name}')
        node.cmd(cmd)

    # Make sure logs have time to finish printing before shutting down nodes
    # so we can check our system's state
    time.sleep(.3 * num_nodes)
    os.rename(
        'chord.log',
        os.path.join('logs',
                     f'chord_{time.time()}_{stabilize_interval}_{fix_fingers_interval}_{wait_per_node}.log'))

    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    main()
