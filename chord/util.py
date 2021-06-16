import logging

logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)


def generate_keys(num_keys):
    key_fmt = "cached_data_{id}"

    keys = []
    for i in range(num_keys):
        keys.append(key_fmt.format(id=str(i)))

    return keys
