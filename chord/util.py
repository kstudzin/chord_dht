import logging

logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)


def generate_keys(num_keys, key_prefix="cached_data"):
    key_format = "{prefix}_{id}"

    keys = []
    for i in range(num_keys):
        keys.append(key_format.format(prefix=key_prefix, id=str(i)))

    return keys
