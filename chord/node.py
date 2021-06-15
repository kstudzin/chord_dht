
class Node:

    def __init__(self, name, id):
        self.name = name
        self.digest_id = id
        self.successor = None

    def get_name(self):
        return self.name

    def successor(self):
        return self.successor

    def get_id(self):
        return self.digest_id

    def set_successor(self, successor):
        self.successor = successor

    def find_successor(self, digest, hops):
        next_id = self.successor.get_id()
        if next_id > self.digest_id:
            if self.digest_id < digest <= next_id:
                return self.successor, hops
            else:
                return self.successor.find_successor(digest, hops + 1)
        else:
            # Handle the case where this node has the highest digest
            if digest > self.digest_id or digest <= next_id:
                return self.successor, hops
            else:
                return self.successor.find_successor(digest, hops + 1)
