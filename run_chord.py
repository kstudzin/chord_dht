import argparse
import time

from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import Controller
from mininet.topo import SingleSwitchTopo, Topo

name_fmt = 'node_{id}'
cmd_fmt = 'python chord/node.py {action} {name} tcp://{ip} --internal-port 5555 ' \
          '--external-port 5556 --stabilize-interval 5 --fix-fingers-interval 7 ' \
          '{ext} &'
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


def create_network(n_hosts):
    """Create and test a simple network"""

    topo = SingleSwitchTopo(n=n_hosts)

    return Mininet(topo=topo, controller=Controller)


def config_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('nodes', type=int, default=10,
                        help='number of nodes in network')

    return parser


def main():
    parser = config_parser()
    args = parser.parse_args()

    num_nodes = args.nodes

    # Create and start network
    net = create_network(num_nodes)
    net.start()

    node2name = {}
    for i, node in enumerate(net.hosts):

        name = name_fmt.format(id=f'{i}')
        if i == 0:
            action = 'create'
            ext = ''
            join_ext = join_fmt_ext.format(ip=node.IP(), name=name)
        else:
            action = 'join'
            ext = join_ext

        node2name[node] = name
        cmd = cmd_fmt.format(action=action, name=name, ip=node.IP(), ext=ext)

        print(f'Starting node {name}: {cmd}')
        node.cmd(cmd)

    # Allow stabilize and finger node processes to complete
    time.sleep(10 * (num_nodes + 1))

    # Send shut down commands
    for node, name in node2name.items():
        cmd = shutdown_cmd_fmt.format(ip=node.IP(), name=name)
        print(f'Shutting down node {name}')
        node.cmd(cmd)

    # Make sure logs have time to finish printing before shutting down nodes
    # so we can check our system's state
    time.sleep(.3 * num_nodes)

    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    main()
