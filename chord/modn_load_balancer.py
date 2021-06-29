"""

"""
import argparse
import json
import sys

from util import generate_keys
from hash import hash_value
from server import Server


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
    parser.add_argument('--no-formatting', action='store_true',
                        help='print raw data without formatting')

    return parser


def main(output, args):
    parser = config_parser()
    args = parser.parse_args(args)

    num_servers = args.num_servers
    num_keys = args.num_keys
    additional = args.additional
    indent = None if args.no_formatting else 4

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
    print(f"\nMapping of keys to server hosting key with {orig_length} servers:", file=output)
    print(json.dumps(result1, indent=indent, default=vars), file=output)

    print(f"\nMapping of keys to server hosting key with {len(server_list)} servers:", file=output)
    print(json.dumps(result2, indent=indent, default=vars), file=output)

    print(f"\n A total of {len(changes)} out of {len(keys)} keys have changed hosts:", file=output)
    print(json.dumps(changes, indent=indent), file=output)


if __name__ == "__main__":
    main(sys.stdout, sys.argv[1:])
