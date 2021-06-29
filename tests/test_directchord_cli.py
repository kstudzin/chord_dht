import io

from chord import directchord


def test_100_naive_hops():
    cmd = ["100", "100", '--naive', '--action', 'hops']

    expected = "Average hops with 100 nodes is 47.43"
    actual = io.StringIO()

    directchord.main(actual, cmd)
    assert actual.getvalue().strip() == expected


def test_50_naive_hops():
    cmd = ["50", "100", '--naive', '--action', 'hops']

    expected = "Average hops with 50 nodes is 25.48"
    actual = io.StringIO()

    directchord.main(actual, cmd)
    assert actual.getvalue().strip() == expected


def test_100_chord_hops():
    cmd = ["100", "100", '--chord', '--action', 'hops']

    expected = "Average hops with 100 nodes is 4.12"
    actual = io.StringIO()

    directchord.main(actual, cmd)
    assert actual.getvalue().strip() == expected


def test_50_chord_hops():
    cmd = ["50", "100", '--chord', '--action', 'hops']

    expected = "Average hops with 50 nodes is 3.69"
    actual = io.StringIO()

    directchord.main(actual, cmd)
    assert actual.getvalue().strip() == expected


def test_naive_network():
    cmd = ["10", "100", '--naive', '--action', 'network', '--no-formatting']
    expected = 'Nodes in the network: \n{"network": [{"id": 24, "name": "node_3"}, {"id": 32, "name": "node_2"}, ' \
               '{"id": 46, "name": "node_6"}, {"id": 109, "name": "node_4"}, {"id": 145, "name": "node_8"}, ' \
               '{"id": 150, "name": "node_7"}, {"id": 160, "name": "node_0"}, {"id": 163, "name": "node_1"}, ' \
               '{"id": 241, "name": "node_9"}, {"id": 244, "name": "node_5"}]}'
    actual = io.StringIO()

    directchord.main(actual, cmd)
    assert actual.getvalue().strip() == expected


def test_chord_network():
    cmd = ["10", "100", '--chord', '--action', 'network', '--no-formatting']
    expected = 'Nodes in the network: \n{"network": [{"id": 24, "name": "node_3"}, {"id": 32, "name": "node_2"}, ' \
               '{"id": 46, "name": "node_6"}, {"id": 109, "name": "node_4"}, {"id": 145, "name": "node_8"}, ' \
               '{"id": 150, "name": "node_7"}, {"id": 160, "name": "node_0"}, {"id": 163, "name": "node_1"}, ' \
               '{"id": 241, "name": "node_9"}, {"id": 244, "name": "node_5"}]}'
    actual = io.StringIO()

    directchord.main(actual, cmd)
    assert actual.getvalue().strip() == expected


def test_naive_fingers():
    cmd = ["10", "100", '--naive', '--action', 'fingers', '--no-formatting']
    expected = 'Finger table for node "node_3": \n{"name": "node_3", "id": 24, "fingers": [{"position": 0, "id": 32, ' \
               '"name": "node_2"}, {"position": 1, "id": 32, "name": "node_2"}, {"position": 2, "id": 32, ' \
               '"name": "node_2"}, {"position": 3, "id": 32, "name": "node_2"}, {"position": 4, "id": 46, ' \
               '"name": "node_6"}, {"position": 5, "id": 109, "name": "node_4"}, {"position": 6, "id": 109, ' \
               '"name": "node_4"}, {"position": 7, "id": 160, "name": "node_0"}]}\nFinger table for node "node_5": ' \
               '\n{"name": "node_5", "id": 244, "fingers": [{"position": 0, "id": 24, "name": "node_3"}, {"position": ' \
               '1, "id": 24, "name": "node_3"}, {"position": 2, "id": 24, "name": "node_3"}, {"position": 3, ' \
               '"id": 24, "name": "node_3"}, {"position": 4, "id": 24, "name": "node_3"}, {"position": 5, "id": 24, ' \
               '"name": "node_3"}, {"position": 6, "id": 109, "name": "node_4"}, {"position": 7, "id": 145, ' \
               '"name": "node_8"}]}'
    actual = io.StringIO()

    directchord.main(actual, cmd)
    assert actual.getvalue().strip() == expected


def test_chord_fingers():
    cmd = ["10", "100", '--chord', '--action', 'fingers', '--no-formatting']
    expected = 'Finger table for node "node_3": \n{"name": "node_3", "id": 24, "fingers": [{"position": 0, "id": 32, ' \
               '"name": "node_2"}, {"position": 1, "id": 32, "name": "node_2"}, {"position": 2, "id": 32, ' \
               '"name": "node_2"}, {"position": 3, "id": 32, "name": "node_2"}, {"position": 4, "id": 46, ' \
               '"name": "node_6"}, {"position": 5, "id": 109, "name": "node_4"}, {"position": 6, "id": 109, ' \
               '"name": "node_4"}, {"position": 7, "id": 160, "name": "node_0"}]}\nFinger table for node "node_5": ' \
               '\n{"name": "node_5", "id": 244, "fingers": [{"position": 0, "id": 24, "name": "node_3"}, {"position": ' \
               '1, "id": 24, "name": "node_3"}, {"position": 2, "id": 24, "name": "node_3"}, {"position": 3, ' \
               '"id": 24, "name": "node_3"}, {"position": 4, "id": 24, "name": "node_3"}, {"position": 5, "id": 24, ' \
               '"name": "node_3"}, {"position": 6, "id": 109, "name": "node_4"}, {"position": 7, "id": 145, ' \
               '"name": "node_8"}]}'
    actual = io.StringIO()

    directchord.main(actual, cmd)
    assert actual.getvalue().strip() == expected


def test_node_joining():
    cmd = ['10', '100', '--chord', '--action', 'join', '--no-formatting']
    expected = 'Original node ids: [24, 32, 46, 109, 145, 150, 160, 163, 241, 244]\n\nFinger table(s) for new ' \
               'nodes:\n{"name": "node_added_0", "id": 218, "fingers": [{"position": 0, "id": 241, "name": "node_9"}, ' \
               '{"position": 1, "id": 241, "name": "node_9"}, {"position": 2, "id": 241, "name": "node_9"}, ' \
               '{"position": 3, "id": 241, "name": "node_9"}, {"position": 4, "id": 241, "name": "node_9"}, ' \
               '{"position": 5, "id": 24, "name": "node_3"}, {"position": 6, "id": 32, "name": "node_2"}, ' \
               '{"position": 7, "id": 109, "name": "node_4"}], "successor": 241, "predecessor": 163}\n\nFinger table(' \
               's) for key updated nodes:\n{"name": "node_1", "id": 163, "fingers": [{"position": 0, "id": 218, ' \
               '"name": "node_added_0"}, {"position": 1, "id": 218, "name": "node_added_0"}, {"position": 2, ' \
               '"id": 218, "name": "node_added_0"}, {"position": 3, "id": 218, "name": "node_added_0"}, {"position": ' \
               '4, "id": 218, "name": "node_added_0"}, {"position": 5, "id": 218, "name": "node_added_0"}, ' \
               '{"position": 6, "id": 241, "name": "node_9"}, {"position": 7, "id": 46, "name": "node_6"}], ' \
               '"successor": 218, "predecessor": 160}'
    actual = io.StringIO()

    directchord.main(actual, cmd)
    assert actual.getvalue().strip() == expected
