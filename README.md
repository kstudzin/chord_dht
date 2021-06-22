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
| Naive routing | `chord/directchord.py` |
| Build finger tables | `chord/directchord.py` |
| Chord routing | `chord/directchord.py` |
| Synchronization Protocol | `chord/directchord.py` |
| Run on Mininet | `chord/node.py` |

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

**File:** `chord/directchord.py` <br>
**Python structure:** `chord.directchord.DirectNode.find_successor()` <br>

#### Execution

```
# Unit Tests
 pytest tests/test_directchord.py -k test_naive_hops
 
# CLI Tests
pytest tests/test_diretchord_cli.py -k test_100_naive_hops
pytest tests/test_directchord_cli.py -k test_50_naive_hops

# CLI
python directchord.py 50 100 --naive --action hops
python directchord.py 100 100 --naive --action hops
```

#### Results

```
Average hops with 50 nodes is 25.48
Average hops with 100 nodes is 47.43
```

The naive routing algorithm used here is _O(n)_ where _n_ is the number of nodes in the network. On average, we would expect to see _n/2_ hops. This aligns with what we see since _25.48 ~= 50/2_ and _47.43 ~= 100/2_.

### Build Finger Tables

**File:** `chord/directchord.py` <br>
**Python structure:** `chord.directchord.DirectNode.fingers`, `chord.directchord.DirectNode.init_fingers()` <br>

#### Execution*

(* Testing and CLI commands for chord nodes listed here as well)

_**Network**_

```
# Unit Tests
pytest tests/test_directchord.py -k test_node_creation
pytest tests/test_directchord.py -k test_chord_node_creation

# CLI Tests
pytest tests/test_directchord_cli.py -k test_naive_network
pytest tests/test_directchord_cli.py -k test_chord_network

# CLI
python directchord.py 10 100 --action network --naive
python directchord.py 10 100 --action network 
```

_**Fingers**_

```
# Unit Tests
pytest tests/test_directchord.py -k test_fingers_first_node 
pytest tests/test_directchord.py -k test_fingers_last_node

pytest tests/test_directchord.py -k test_fingers_first_chord_node
pytest tests/test_directchord.py -k test_fingers_last_chord_node

# CLI Tests
pytest tests/test_directchord_cli.py -k test_naive_fingers
pytest tests/test_directchord_cli.py -k test_chord_fingers
 
# CLI
python directchord.py 10 100 --action fingers --naive
python directchord.py 10 100 --action fingers
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

**File:** `chord/directchord.py` <br>
**Python structure:** `chord.directchord.DirectChordNode.find_successor()` <br>

#### Execution

```
# Unit Tests
pytest tests/test_directchord.py -k test_chord_hops

# CLI Tests
pytest tests/test_directchord_cli.py -k test_100_chord_hops
pytest tests/test_directchord_cli.py -k test_50_chord_hops

# CLI
python directchord.py 50 100 --chord --action hops
python directchord.py 100 100 --chord --action hops
```

#### Results

```
Average hops with 50 nodes is 3.69
Average hops with 100 nodes is 4.12
```

Chord routing scales logarithmically with the number of nodes in the network. Given that, we would expect average hops with 50 nodes to be close to _ln(50) = 3.9_ and average hops with 100 nodes to be close to _ln(100) = 4.6_. This is close to the results above. We expect to see logarithmic scaling because chord routing because it is essentially a binary search where at any point we can skip approximately half of the search space.

### Synchronization Protocol

**File:** `chord/directchord.py` <br>
**Python structure:** `chord.directchord.DirectNode.join()`, `chord.directchord.DirectNode.stabilize()`, `chord.directchord.DirectNode.fix_fingers()`, `chord.directchord.DirectNode.notify()` 

#### Execution

```
### Unit Tests
pytest tests/test_directchord.py -k test_add_node

### CLI Tests
pytest tests/test_directchord_cli.py -k test_node_joining

### CLI
python directchord.py 10 100 --chord --action join
```

#### Results

The tests create a new node named `node_added_0` whose digest is `218`. The synchronization methods correctly set the successor to node `241` and the predecessor `163`. Similarly, node `163` has updated its successor to point to new node `218`. This information is also reflected in properly updated finger tables.

### Run Chord on Mininet

**File:** `chord/node.py` <br>
**Python structure:** `chord.node.Node`, `chord.node.ChordNode`, `chord.node.Command`, `chord.node.FindSuccessorCommand`, `chord.node.PredecessorCommand`, `chord.node.NotifyCommand`

#### Design

_**Socket Initialization**_

Sockets are initialized in the constructor so that they are available to `join()` before they are used in `run()`.

_**Node Sockets**_

Each Node has two sockets for communicating with other Nodes: ROUTER and DEALER. We use these sockets to apply an asynchronous request-reply pattern. When nodes send messages to other nodes, they do not care about a reply. For example, in `find_successor()` when a node finds the next node to query, it simply wants to pass of the responsibility to that node.

The ROUTER socket is used because it can send messages to specific sockets and receive the identity of sockets that send messages to it. It needs to be able to send messages to specific sockets because that is how it communicates with the other network nodes it knows about. It needs to know the identity of sockets that send messages to it when it talks to clients. When a client wants to 

The DEALER socket is used because it can specify its identity so that the ROUTER socket can send messages directly to it. 

_**Threads**_

Running Chord on Mininet requires synchronization tasks to run periodically. To do that, we run threads that threads will tell the main thread to execute a command at specified time intervals. The reason that these threads communicate with the main thread rather than executing the command themselves is that the execution requires using sockets that the main thread is using. Because sockets are not thread-safe, we do not want to do that. Instead, we use PAIR sockets and inproc communication for threads to communicate.

## TODO

#### High Priority (Functional)

- [ ] Add code to get commands from clients
- [ ] Accept port for router socket. Needs to be bound before dealer binds to random port

#### Low Priority (Code Quality)

- [ ] Command should be bytes not ints because that's how they will be sent across the wire
- [ ] Search for node rather than iterate in `consistent_load_balancer`
- [ ] Move `fix_fingers()` into `__init__()` or `set_successor()`
- [ ] Add succeeding node list and use it to jump further if fingers not there
- [ ] Use data frames instead of pretty printing output
- [ ] Load balancers share a lot of code and could be consolidated
- [ ] Make `num_keys` optional in `directchord.py`
- [ ] Use subparser instead of `--actions` in `directchord.py` 
- [ ] FOR_NODE and FOR_CLIENT don't really belong in Command

## Questions

- ~~Should nodes a have reply socket that will send synchronous replies for predecessor requests? No, as the docs note, there is no advantage to router-rep over router-dealer~~
- ~~What is the use case for POLLOUT? Receiving from multiple sockets~~
- Only nodes call find successor; clients call get and put. OR nodes call find successor to get the identity of the hosting node and then get data from host directly.
- How does a node know if a found successor message is for it or for a client? How does fix_fingers know which k a found successor is for?