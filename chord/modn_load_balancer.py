"""

"""
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

    for i in range(num_servers):
        name = server_name_fmt.format(id=str(i))
        server_list.append(Server(name))


def get_servers(keys):
    result = {}

    for key in keys:
        server = responsible_server(key)
        result[key] = server

    return result


def main():
    # Initial 50 servers
    num_servers = 50
    num_keys = 10

    build_server_list(num_servers)
    keys = generate_keys(num_keys)

    result1 = get_servers(keys)

    # Add a server
    name = server_name_fmt.format(id=num_servers)
    server_list.append(Server(name))

    result2 = get_servers(keys)

    # Calculate the number of changes
    changes = [changed for changed in result1 if result1[changed] != result2[changed]]

    # Print results
    print(f"\nMapping of keys to server hosting key with {len(server_list) - 1} servers:")
    pp.pprint(result1)

    print(f"\nMapping of keys to server hosting key with {len(server_list)} servers:")
    pp.pprint(result2)

    print(f"\n A total of {len(changes)} out of {len(keys)} keys have changed hosts:")
    pp.pprint(changes)

    # Expect a total of nine keys to be assigned to a different server
    assert len(changes) == 9


if __name__ == "__main__":
    main()
