import logging

logging.basicConfig(filename='chord.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')


def generate_keys(num_keys, key_prefix="cached_data"):
    key_format = "{prefix}_{id}"

    i = 0
    keys = []
    while len(keys) < num_keys:
        keys.append(key_format.format(prefix=key_prefix, id=str(i)))
        i += 1

    return keys


def open_closed(start, end, test):
    if start < end:
        return start < test <= end
    else:
        return test > start or test <= end


def open_open(start, end, test):
    if start < end:
        return start < test < end
    else:
        return test > start or test < end
