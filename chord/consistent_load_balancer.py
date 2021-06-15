import pprint
from sortedcontainers import SortedDict

from util import generate_keys
from server import Server
from hash import hash_value

pp = pprint.PrettyPrinter()

server_name_fmt = "server_{id}"
servers = SortedDict()


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
    for i in range(num_servers):
        name = server_name_fmt.format(id=str(i))
        digest = hash_value(name)
        servers[digest] = Server(name)


def get_servers(keys):
    result = {}

    for key in keys:
        server = consistent_responsible_server(key)
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
    digest = hash_value(name)
    servers[digest] = Server(name)

    result2 = get_servers(keys)

    # Calculate the number of changes
    changes = [changed for changed in result1 if result1[changed] != result2[changed]]

    # Print results
    print(f"\nMapping of keys to server hosting key with {len(servers) - 1} servers:")
    pp.pprint(result1)

    print(f"\nMapping of keys to server hosting key with {len(servers)} servers:")
    pp.pprint(result2)

    print(f"\n A total of {len(changes)} out of {len(keys)} keys have changed hosts:")
    pp.pprint(changes)

    # Expect a total of nine keys to be assigned to a different server
    assert len(changes) == 0


if __name__ == "__main__":
    main()
