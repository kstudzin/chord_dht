"""

"""
import argparse
import pprint

from util import generate_keys
from hash import hash_value
from server import Server

pp = pprint.PrettyPrinter()

server_name_fmt = "server_{id}"
server_list = []


def responsible_server(key):
    return server_list[hash_value(key) % len(server_list)]


def build_server_list(num_servers):

    curr_max = len(server_list)
    for i in range(curr_max, curr_max + num_servers):
        name = server_name_fmt.format(id=str(i))
        server_list.append(Server(name))


def get_servers(keys):
    result = {}

    for key in keys:
        server = responsible_server(key)
        result[key] = server

    return result


def calculate_change(servers_orig, servers_appended):
    return [changed for changed in servers_orig if servers_orig[changed] != servers_appended[changed]]


def config_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('num_servers', type=int, help='number of servers to build')
    parser.add_argument('num_keys', type=int, help='number of keys to build')
    parser.add_argument('--additional', '-a', type=int, default=1,
                        help='number of servers to add')
    parser.add_argument('--no-formatting', action='store_const', const=print, default=pp.pprint,
                        help='print raw data without formatting')

    return parser


def main():
    parser = config_parser()
    args = parser.parse_args()

    num_servers = args.num_servers
    num_keys = args.num_keys
    additional = args.additional
    printer = args.no_formatting

    build_server_list(num_servers)
    orig_length = len(server_list)
    keys = generate_keys(num_keys)

    result1 = get_servers(keys)

    # Add a server
    build_server_list(additional)

    result2 = get_servers(keys)

    # Calculate the number of changes
    changes = calculate_change(result1, result2)

    # Print results
    print(f"\nMapping of keys to server hosting key with {orig_length} servers:")
    printer(result1)

    print(f"\nMapping of keys to server hosting key with {len(server_list)} servers:")
    printer(result2)

    print(f"\n A total of {len(changes)} out of {len(keys)} keys have changed hosts:")
    printer(changes)


if __name__ == "__main__":
    main()
