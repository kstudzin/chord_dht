"""Hash function to use in chord algorithm

Implemented using md5. All values are 1 byte, i.e., 0-255
"""
import hashlib
import sys

NUM_BITS = 8


def hash_value(value):
    """ Computes the least significant byte of the md5 for the given input

    MD5 RFC specifies that the bytes are in little endian order
    (https://datatracker.ietf.org/doc/html/rfc1321#section-2)

    :param value: value to hash
    :return: the least significant byte of of the m5 hash of the input value
    """
    md5_hash = hashlib.md5(value.encode('utf-8'))
    return md5_hash.digest()[0]


if __name__ == '__main__':
    value = ' '.join(sys.argv[1:])
    print(f"Value \"{value}\" has digest \"{hash_value(value)}\"")
