# cs6381-assignment2

Chord DHT Implementation

## Setup

### Installation

From the project root run the following commands:

1. `source env.sh` 
   _(Note: This will need to be run every time you open a new shell. To avoid re-running, add the contents to your shell profile.)_ 
2. `pip install -r requirements.txt`

### Testing

Run tests using `pytest` from the project root or `tests` directories. All documentation of results from the assignment specification have test methods which can be run individually. The specific commands for each can be found in the Assignment Tasks section. Each `chord` submodule has unit tests and CLI tests which are in separate files for longer tests.

## Assignment Tasks

| Task | File |
|------|------|
| Chord Worksheet | `worksheet.md` |
| Hash function | `chord/hash.py` |
| Mod-N load balancer | `chord/modn_load_balancer.py` |
| Consistent load balancer | `chord/consistent_load_balancer.py` |
| Naive routing | `chord/node.py` |
| Build finger tables | `chord/node.py` |
| Chord routing | `chord/node.py` |

### Chord Worksheet

**File:** `worksheet.md`

### Hash Function

**File:** `chord/hash.py` <br>
**Python structure:** `chord.hash.hash_value()` <br>

#### Execution

```
# Unit Tests
pytest tests/test_hash.py -k test_hash

# CLI Tests
pytest tests/test_hash.py -k test_hash_cli

# CLI
python hash.py Hello, world!
```

### Mod-N Load Balancer

**File:** `chord/modn_load_balancer.py` <br>
**Python structure:** `chord.modn_load_balancer` <br>

#### Execution

```
# Unit Tests
pytest tests/test_modn_load_balancer.py -k test_adding_server

# CLI Tests
pytest tests/test_modn_load_balancer_cli.py -k test_50_orig_1_addtl 

# CLI
python modn_load_balancer.py 50 10 --additional 1
```

#### Results

9 out of 10 keys were assigned to different servers after adding an additional server

### Consistent Load Balancer

**File:** `chord/consistent_load_balancer.py` <br>
**Python structure:** `chord.consistent_load_balancer` <br>

#### Execution

```
# Unit Tests
pytest tests/test_consistent_load_balancer.py

# CLI Tests
pytest tests/test_consistent_load_balancer_cli.py -k test_50_orig_1_addtl

# CLI
python consistent_load_balancer.py 50 10 --additional 1
```

#### Results

1 out of 10 keys were assigned to different servers after adding an additional server

### Naive Chord Routing

**File:** `chord/node.py` <br>
**Python structure:** `chord.node.Node.find_successor()` <br>

#### Execution

```
# Unit Tests
 pytest tests/test_node.py -k test_naive_hops
 
# CLI Tests
pytest tests/test_node_cli.py -k test_100_naive_hops
pytest tests/test_node_cli.py -k test_50_naive_hops

# CLI
python node.py 50 100 --naive --action hops
python node.py 100 100 --naive --action hops
```

#### Results

```
Average hops with 50 nodes is 25.48
Average hops with 100 nodes is 47.43
```

The naive routing algorithm used here is _O(n)_ where _n_ is the number of nodes in the network. On average, we would expect to see _n/2_ hops. This aligns with what we see since _25.48 ~= 50/2_ and _47.43 ~= 100/2_.

### Build Finger Tables

**File:** `chord/node.py` <br>
**Python structure:** `chord.node.Node.fingers` <br>

#### Execution*

(* Testing and CLI commands for chord nodes listed here as well)

_**Network**_

```
# Unit Tests
pytest tests/test_node.py -k test_node_creation
pytest tests/test_node.py -k test_chord_node_creation

# CLI Tests
pytest tests/test_node_cli.py -k test_naive_network
pytest tests/test_node_cli.py -k test_chord_network

# CLI
python node.py 10 100 --action network --naive
python node.py 10 100 --action network 
```

_**Fingers**_

```
# Unit Tests
pytest tests/test_node.py -k test_fingers_first_node 
pytest tests/test_node.py -k test_fingers_last_node

pytest tests/test_node.py -k test_fingers_first_chord_node
pytest tests/test_node.py -k test_fingers_last_chord_node

# CLI Tests
pytest tests/test_node_cli.py -k test_naive_fingers
pytest tests/test_node_cli.py -k test_chord_fingers
 
# CLI
python node.py 10 100 --action fingers --naive
python node.py 10 100 --action fingers
```

#### Results\*
(* Verification may be easier by running and examining tests)

_**Network**_

```
|-----------|---------|
| Node Name | Node ID | 
|-----------|---------|
| node_3    |      24 |
| node_2    |      32 |
| node_6    |      46 |
| node_4    |     109 |
| node_8    |     145 |
| node_7    |     150 |
| node_0    |     160 |
| node_1    |     163 |
| node_9    |     241 |
| node_5    |     244 |
|-----------|---------|
```

_**Fingers**_

```
Finger Table for Node: node_3 ID: 24
|---|-----------|---------|
| k | Node Name | Node ID |
|---|-----------|---------|
| 1 | node_2    |      32 |
| 2 | node_2    |      32 |
| 3 | node_2    |      32 |
| 4 | node_2    |      32 |
| 5 | node_6    |      46 |
| 6 | node_4    |     109 |
| 7 | node_4    |     109 |
| 8 | node_0    |     160 |
|---|-----------|---------|
```

### Chord Routing

**File:** `chord/node.py` <br>
**Python structure:** `chord.node.ChordNode.find_successor()` <br>

#### Execution

```
# Unit Tests
pytest tests/test_node.py -k test_chord_hops

# CLI Tests
pytest tests/test_node_cli.py -k test_100_chord_hops
pytest tests/test_node_cli.py -k test_50_chord_hops

# CLI
python node.py 50 100 --chord --action hops
python node.py 100 100 --chord --action hops
```

#### Results

```
Average hops with 50 nodes is 3.69
Average hops with 100 nodes is 4.12
```

Chord routing scales logarithmically with the number of nodes in the network. Given that, we would expect average hops with 50 nodes to be close to _ln(50) = 3.9_ and average hops with 100 nodes to be close to _ln(100) = 4.6_. This is close to the results above. We expect to see logarithmic scaling because chord routing because it is essentially a binary search where at any point we can skip approximately half of the search space.

## TODO
- [ ] Search for node rather than iterate in `consistent_load_balancer`
- [ ] Move `fix_fingers()` into `__init__()` or `set_successor()`
- [ ] Add succeeding node list and use it to jump further if fingers not there
- [ ] Use data frames instead of pretty printing output
- [ ] Load balancers share a lot of code and could be consolidated
