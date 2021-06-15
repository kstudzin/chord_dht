"""

"""
import pprint

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


def generate_keys(num_keys):
    key_fmt = "cached_data_{id}"

    keys = []
    for i in range(num_keys):
        keys.append(key_fmt.format(id=str(i)))

    return keys


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
    print(f"\nMapping of keys to server hosting key with {len(server_list)} servers:")
    pp.pprint(result1)

    # Add a server
    server_list.append(server_name_fmt.format(id=num_servers))

    result2 = get_servers(keys)
    print(f"\nMapping of keys to server hosting key with {len(server_list)} servers:")
    pp.pprint(result2)

    # Calculate the number of changes
    changes = [changed for changed in result1 if result1[changed] != result2[changed]]
    print(f"\n A total of {len(changes)} out of {len(keys)} keys have changed hosts:")
    pp.pprint(changes)

    # Expect a total of nine keys to be assigned to a different server
    assert len(changes) == 9


if __name__ == "__main__":
    main()
