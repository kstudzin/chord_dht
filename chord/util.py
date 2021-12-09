import logging

# logging.basicConfig(filename='chord.log', level=logging.DEBUG,
#                     format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')

formatter = logging.Formatter('%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')


def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


request = setup_logger('requests', 'chord_request.py', level=logging.DEBUG)
logging = setup_logger('chord', 'chord.log')


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
