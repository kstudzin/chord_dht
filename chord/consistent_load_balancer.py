import argparse
import json
import sys

from sortedcontainers import SortedDict
from util import generate_keys
from server import Server
from hash import hash_value


server_name_fmt = "server_{id}"
servers = SortedDict()
max_server_id = 0


def consistent_responsible_server(key):
    key_digest = hash_value(key)

    if key_digest in servers:
        return servers[key_digest]
    else:
        return find_server(key_digest)


def find_server(key_digest):
    for server_digest in servers.keys():
        if server_digest > key_digest:
            return servers[server_digest]

    # If we have gone through the list of servers and not found the hosting server,
    # then the key digest is larger than the largest node digest. In this case the
    # key is hosted by the server with the smallest digest
    first_server_digest = servers.keys()[0]
    return servers[first_server_digest]


def build_server_list(num_servers):
    global max_server_id

    i = max_server_id
    new_total = len(servers) + num_servers
    while len(servers) < new_total:
        name = server_name_fmt.format(id=str(i))
        digest = hash_value(name)
        servers[digest] = Server(name)
        i += 1

    max_server_id = i


def get_servers(keys):
    result = {}

    for key in keys:
        server = consistent_responsible_server(key)
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
    orig_length = len(servers)
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

    print(f"\nMapping of keys to server hosting key with {len(servers)} servers:", file=output)
    print(json.dumps(result2, indent=indent, default=vars), file=output)

    print(f"\n A total of {len(changes)} out of {len(keys)} keys have changed hosts:", file=output)
    print(json.dumps(changes, indent=indent), file=output)


if __name__ == "__main__":
    main(sys.stdout, sys.argv[1:])
