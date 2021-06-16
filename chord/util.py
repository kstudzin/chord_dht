import logging

logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)


def generate_keys(num_keys, key_prefix="cached_data"):
    key_format = "{prefix}_{id}"

    i = 0
    keys = []
    while len(keys) < num_keys:
        keys.append(key_format.format(prefix=key_prefix, id=str(i)))
        i += 1

    return keys
