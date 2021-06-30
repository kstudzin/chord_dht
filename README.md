# cs6381-assignment2

Chord DHT Implementation

## Setup

### Installation

From the project root run the following commands:

1. `source env.sh` 
   _(Note: This will need to be run every time you open a new shell. To avoid re-running, add the contents to your shell profile.)_ 
2. `pip install -r requirements.txt`
3. Set log level in `chord/util.py`. Logs are in `chord.log` from the directory the code was run from. _Node: DEBUG has a lot of logging_ 

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
| Virtual Nodes | `chord/node.py` |
| Cryptographic vs. Non-Cryptographic Hashes | `README.md` |
| How Chord Relates to B-trees | `README.md` |

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

**File:** `chord/node.py`, `run_chord.py` <br>
**Python structure:** `chord.node.Node`, `chord.node.ChordNode`, `chord.node.Command`, `chord.node.FindSuccessorCommand`, `chord.node.PredecessorCommand`, `chord.node.NotifyCommand`

#### Design

_**Node Sockets**_

Each node has two sockets for communicating with other nodes: ROUTER and DEALER. We use these sockets so that nodes can communicate asynchronously. In other words, when nodes send messages to other nodes, they do not wait for a reply. For example, in `find_successor()` when a node finds the next node to query, it simply wants to pass off the search to that node. Or when a node receives a client request, it may pass the request off to another node who will respond to the client.

Nodes use their ROUTER socket for two purposes: receiving messages from clients and sending messages.
Nodes receive messages from clients on the router socket because the router receives the identity of sending socket. The nodes will pass the identity to other nodes as they look up the information the client requested, and when a node finds the information, it will respond to the client directly on its router socket. The ability to communicate with a specific socket by knowing its identity is the other reason nodes use router sockets. Nodes send all messages, to network nodes as well as clients, with the router socket for this reason.

Nodes use their DEALER socket for receiving messages from nodes in the network. They use dealers for this purpose because dealer sockets can set their identity property. In this implementation, dealers set their socket identity to the digest of the node. This allows a network node to send messages to another network node knowing its name, more specifically the hashed digest of the name, and its address. 

Each socket must be bound to an endpoint and because each node has two sockets, it also has two endpoints. These endpoints are differentiated by the types of messages they receive. The dealer socket receives messages from network nodes, so its endpoint is called the internal endpoint. The router socket receives messages from clients, so its endpoint is called the external endpoint.

Nodes also have 2 sets of PAIR sockets used in the synchronization protocol. These are discussed in the 'Threads' section.

_**Message Flow Diagram**_

![Chord Request Flow (1)](https://user-images.githubusercontent.com/10711838/123801885-ad6b3b00-d8b8-11eb-8719-1afc9e65cc71.png)

_**Socket Initialization**_

Except for the pair sockets used in threads, sockets are instance attributes on the nodes. They are bound in the constructor so that they are available to `join()` before they are used in `run()`. It is key that `join()` is called before `run()` because `join()` needs to communicate with other nodes to initialize the successor on the new nodes.

_**Threads**_

Chord requires synchronization tasks to run periodically to adjust node links, i.e., successor, predecessor, and fingers, for joining and leaving nodes. To do that, each node runs two threads: one runs stabilize and the other runs fix fingers. These tasks require communication with other nodes in the network, but because sockets are not thread-safe, we can not use the dealer and router sockets discussed above. Instead, threads use the inproc communication protocol with PAIR sockets. 

Further, these protocols are implemented such that they avoid accessing shared data, such as instance attributes, in non-thread-safe ways. Specifically, they iterate over the virtual nodes, which are not modified after initialization, and they read a single object from that structure which is an atomic operation. The thread uses the pair socket to pass this information to the main thread which updates data and communicates with other nodes.

_**Commands**_

The `Command` subclasses provide templates for messages nodes send to each other, encapsulate the data and logic associated with each operation, and abstract the operation logic from the node. 

#### Execution

```
# Unit tests
pytest tests/integration/test_networked_node.py

# CLI

## Start the first node
python node.py create node_0 tcp://127.0.0.1 --internal-port 5501 --external-port 5502 --real-hashes

## Start a second node
python node.py join node_1 tcp://127.0.0.1 --internal-port 5503 --external-port 5504 --known-endpoint tcp://127.0.0.1:5501 --known-name node_0 --real-hashes

## Shut down the first node
python node.py shutdown node_0 tcp://127.0.0.1 --internal-port 5501 --real-hashes

## Run on mininet
sudo python run_chord.py 25

## Evaluate log output
python chord/util/evaluate_logs.py logs/chord_1624888721.9974809_15_10_20.log --finger-errors --verbose
```

The node module includes code to start a node on the current machine. This script has two actions to spin up nodes: `create` starts the first node in a network and `join` starts subsequent nodes. This script is used by the `run_chord.py` mininet script to start multiple nodes on a virtual network. 

The mininet script starts the number of requested nodes, waits some period of time for them to run synchronization, and shuts down each node.

While the network is running, logs are output to `chord.log`. When using the mininet script, logs are migrated to the `logs` directory after the run is complete. The `evaluate_logs.py` script reads the logs and evaluates if the network had stabilized by the time it shutdown.

#### Results

When running chord on mininet, there are three settings to consider: the interval between calls to stabilize, the interval between calls to fix fingers, and the amount of time to wait for the network to synchronize. In my tests using 25 nodes, I set the stabilize interval to 15 seconds and the fix fingers to 10 seconds. I tested wait times of 10, 20, and 30 seconds per node, and the fingers had 75, 23, and 0 errors, respectively. This means that the network took between 8 and 12.5 seconds to stabilize. In practice there is no wait time and the network may never fully stabilize because nodes will be leaving and enter regularly.

### Virtual Nodes

**File:** `chord/node.py`, `run_chord.py` <br>
**Python structure:** `chord.node.VirtualNode`, `chord.node.ChordVirtualNode`, `chord.node.Node.virtual_nodes`, `chord.node.RoutingInfo`, `chord.node.Node.create()`

#### Design

This iteration adds several new classes. The `VirtualNode` class contains all the information linking a node to other nodes in the network: successor, predecessor, and fingers. Each of these links as well the `VirtualNode` is an instance of `RoutingInfo` which contains information to send messages to a node. Specifically, it has a node's digest, the host node's digest, and the host node's address. One of the virtual nodes will always be the host node. In this case, the digest and parent's digest are the same. `VirtualNode` also contains the methods, such as `find_successor()`, for retrieving and manipulating those links. `ChordVirtualNode` is a subclass that contains the `closest_preceding_finger()` method. As a result of these class, most of the code managing the links between nodes is maintained in the `VirtualNode` class, and the code managing passing messages around the network remains in the `Node` class. One optimization that has not yet been made is to avoid sending messages over the network when one virtual node is looking for information on a virtual node hosted by the same parent node.

Adding virtual nodes required a change in start up procedure. When the host starts, it needs to find the successor for each virtual node. This was not necessary before because there was only one node, but with 2 or more virtual nodes, the nodes should be find their successor within the group. Without this initialization, the synchronization protocols won't properly adjust these nodes. To handle this, the `Node` class now has a `create()` method that should be called on the first node to join the network.

_**Classs Diagram**_

![Class_Diagram](https://user-images.githubusercontent.com/10711838/123802260-1f438480-d8b9-11eb-9984-af04bf2b5704.JPG)

#### Execution

```
# Unit tests
pytest tests/integration/test_networked_node.py -k test_stabilize
pytest tests/test_node.py -k test_create
pytest tests/test_node.py -k test_chord_virtual_nodes
pytest tests/test_node.py -k test_virtual_nodes

# CLI

## Start the first node with 1 virtual node
python chord/node.py create 197 tcp://127.0.0.1 --internal-port 5555 --external-port 5556 --stabilize-interval 20 --fix-fingers-interval 12  --virtual-nodes vnode_194:194
 
## Start the second node with 1 virtual node
python chord/node.py join 227 tcp://10.0.0.2 --internal-port 5555 --external-port 5556 --stabilize-interval 20 --fix-fingers-interval 12 --known-endpoint tcp://10.0.0.1:5555 --known-name 197 --virtual-nodes vnode_107:107

## Shut down the first node
python chord/node.py shutdown 197 tcp://127.0.0.1 --internal-port 5555

## Run on mininet
sudo python run_chord.py 10 --nodes-per-host 2

## Evaluate load
python chord/util/evaluate_logs.py logs/chord_1624890931.7214227_15_10_10.log --load-statistics 
python chord/util/evaluate_logs.py logs/chord_1624847263.2324307_15_10_10.log --load-statistics
```

_Note that evaluating the finger errors on these logs is not useful. The runs generating them did not give the networks time to stabilize._

#### Results

```
# Load statistics for 20 virtual nodes
Evaluating 20 nodes
Average load: 25.6
Standard deviation: 13.898041428760944

# Load statisitics for 200 virtual nodes
Evalutating 200 nodes
Average load: 25.6
Standard deviation: 2.1186998109427604
```

The first calculation is based on a network with 10 'physical' nodes each hosting 2 virtual nodes. The second is based on a network with 10 'physical' nodes each hosting 20 virtual nodes. The average is the same because in both cases the total number of keys hosted by the network, i.e. the numerator in the average, and the number of hosts are the same. However, the standard deviation in the second is significantly less showing that there is less variation in the number of keys hosted by a physical node when there are more virtual nodes. In other words virtual nodes distribute the keys better which means that the load is balanced better.  With this type of load balancing, if clients access keys approximately equally, each host should receive a similar number of requests.

This does not help load balancing if there is some set of keys that is accessed much more than others. In that case replicating keys across several hosts, i.e. read replicas, can help to balance the load. When the data is replicated across multiple hosts, any of those hosts can respond to requests for the data and reduce the number of requests the primary host needs to respond to.

### Cryptographic vs. Non-Cryptographic Hashes

Cryptographic hashes are used in situations where privacy is a concern, such as when storing passwords. Because they deal with sensitive information, they have several requirements they must meet:

- _**Deterministic**_: the same value must always hash to the same digest
- _**Quick**_: must not take long to compute
- _**Pre-image attack resistant**_: given a digest, it is impossible to calculate the input that generated it
- _**Avalanche effect**_: small changes in the input lead to large changes in the digest
- _**Collision resistant**_: two different values should not have the same digest

This ensures that the information is protected from attack.

Non-cryptographic hashes don't need to be as concerned with all of these properties because they are not protecting sensitive information. Instead they can be optimized for other applications. One common application for non-cryptographic hashes is hash tables. In hash tables such as chord a primary goal is distribution of output hashes. In a local hash table a well distributed hash means that items are evenly distributed among buckets. In consistent hashing a well distributed hash means that the number of keys that any one node is responsible for is approximately equal. This helps with load balancing because, assuming requests for keys is also well distributed, each node will receive approximately the same number of requests. Additionally, fewer, less strict requirements often mean that non-cryptographic hashes can be computed faster.

#### Resources
https://dadario.com.br/cryptographic-and-non-cryptographic-hash-functions/
https://www.youtube.com/watch?v=siV5pr44FAI
https://crypto.stackexchange.com/a/43520
https://softwareengineering.stackexchange.com/a/145633/392415
https://stackoverflow.com/a/11901654/3027632

### How Chord Relates to B-trees

B-trees are a self-balancing tree data structure that generalize binary search trees. While binary search trees can have only 2 child nodes where each node has one key, b-trees can, and should, have multiple children each many keys. In b-trees, the keys on each node are sorted and serve as separators between pointers to children. Like binary search trees, the left child contains keys smaller than the current key, and the right child contains keys larger than the current key. The average search time complexity of b-trees is, like binary search trees, `O(lg n)` where `n` is the number of nodes in the tree. Because b-trees are self-balancing, there is no case where they have `O(n)` search time complexity. 

B-trees and chord have similar origins. Both were discovered by researchers trying to overcome the problems introduced by the size of the datasets they were working on. For b-trees, the data could no longer fit in memory. B-trees store data on disk but overcome the time cost by aligning their elements to the disk's block size to maximize cache hits when reading consecutive elements. For chord, the data is too large for a single computer, so it distributes the data over a network of computers.

Because both b-trees and hashes store data based on a key, they need to be able to retrieve the data via lookup or search. Each does this efficiently by splitting the search space in half with each step. For b-trees the mechanism for traversing large chunks of the search space is the keys stored at each node. These serve a similar purpose as the fingers do in the chord algorithm. Given that both store and retrieve data, have similar applications. B-trees are commonly used as indexes in relational databases, and chord-like algorithms are used as 'indexes' in distributed databases like Apache Cassandra.

A key difference is that b-trees are optimized for reading consecutive keys as in range searches, while chord makes that very difficult. The reason range searches are difficult in chord is that keys are hashed, so two keys that are close will have hashes that are far apart by the design of the hash function. The authors of 'A  practical scalable distributed B-tree' (2007) cite distributed range searches as a motivator for their work.

#### Resources
- https://www.cs.cornell.edu/courses/cs3110/2012sp/recitations/rec25-B-trees/rec25.html
- https://youtu.be/TOb1tuEZ2X4
- https://en.wikipedia.org/wiki/B-tree
- https://cassandra.apache.org/doc/latest/architecture/dynamo.html
- Aguilera, Marcos K, Wojciech Golab, and Mehul A Shah. “A Practical Scalable Distributed B-Tree.” Proceedings of the VLDB Endowment 1.1 (2008): 598–609. Web. https://www.hpl.hp.com/techreports/2007/HPL-2007-193.pdf 

### Content Addressable Networks (CAN)

Content addressable networks are a type of distributed hash table whose overlay network forms a d-dimensional torus. For 2 dimensions, this means that the network is a grid with nodes at the intersection of rows and columns where the rows and columns are continuous loops. Each node is responsible for some non-overlapping, convex region in this space. There should be point in the domain that is not the responsiblity of some node in the network. Nodes maintain a list of their neighbors where neighbors are defined as a node whose region overlaps in _d - 1_ dimensions and abuts in one dimension.

When a node joins the network, contacts a node in the network to get a random location. Once the node has a location, it sends a join message to the node currently responsible for the region containing the new node's location. The original node splits its zone and sends the new node a list of its neighbors. Data is inserted into the network and stored on the node whose region contains the data's hash. Hash is a digest of the value to be inserted. To accommodate the multiple dimensions, specific ranges of bits in the digest can be designated to each dimension of the point. When a node leaves, the smallest neighbor becomes responsible for the departed node's region. If the two regions can be merged into a single convex region, they will be. Otherwise one node will be responsible for two regions until the background maintence process balances the regions.

In many ways CANs are a multi-dimensional version of chord. In both approaches nodes are responsible for a set of keys nearby in the address space. To join a network, a node talks to a known entry point node to get the address of the network node it will be close to in the overlay network. The new node lets its new neighbor know it has arrived, and the nearby node hands off some keys it is responsible for to the new node. When a node leaves the network, a nearby node takes over the keys the exiting node was responsible for. In both approaches, each node maintains a list of other nodes it can route queries to. In chord this list includes nodes that are closer on the overlay network and nodes that are further, while in CANs, this list only includes neighbors. Chord nodes do have references to their neighbors, their predecessor and successor, but they are not used for routing.

Even with all of these similarities, there are some differences and usage considerations which choosing a DHT. One consideration is fault tolerance. In addition to routing, CAN nodes' list of neighbors provide fault tolerance. When a chord node's finger is unavailable, chord follows a chain of successors. While it still finds the data, performance is worse. Because CAN nodes have a list of neighbors and multiple neighbors can provide correct routes to the destination, a node can route a lookup through a different neighbor when one is down. Another consideration is scaling. In chord performance scales with the number of nodes in the network, while CAN networks scale with dimensionality. (Both more nodes in chord and higher dimensions in CAN lead to increased fault tolerance). Lastly, there are load balancing considerations. While chord load balancing is largely dependent on the distribution properties of the hash function, CANs are able to dynamically load balance because there are multiple neighbors who could become responsible for a given region.  One example of CAN rebalancing is that after a node leaves the network, neighbors vote so that the smallest region can maintain the newly abandoned region.

## Troubleshooting

#### Nothing prints to the logs from `run_chord.py`
Try running command locally and see what errors arise

## TODO

#### High Priority (Functional)

- [x] `join()` fails if found successor has same id as joining node
- [ ] Add code to get commands from clients
- [ ] Add `pytest-mock` to `requirements.txt`
- [x] Testing specify id that acts like a hash to avoid collisions in small address space
- [x] Accept port for router socket. Needs to be bound before dealer binds to random port
- [ ] Main thread sends exit message to pair sockets. Pair polls - this is the only async message they receive. What happens if they get exit message when waiting for other message?
- [ ] Investigate why some nodes hang on `context.destroy()`
- [ ] Add generator for virtual node keys
- [x] Add virtual nodes to cli
- [x] Add chord node type to cli

#### Low Priority (Code Quality)

- [ ] Exit Command __eq__ explanation
- [ ] Add execute to ExitCommand
- [ ] Use timers rather than threads sleeping for stabilize and fix fingers
- [ ] Add `run_chord.py` options to set stabilize and fix fingers intervals
- [ ] `Command.execute()` could share more code between subclasses
- [ ] Add optimization to `find_successor()` to see if current node is successor: if predecessor is set, check if the digest is between predecessor and current node
- [ ] Search for node rather than iterate in `consistent_load_balancer`
- [ ] Use data frames instead of pretty printing output
- [ ] Load balancers share a lot of code and could be consolidated
- [ ] Make `num_keys` optional in `directchord.py`
- [ ] Use subparser instead of `--actions` in `directchord.py` 
- [ ] Validate url formatting
- [ ] Separate finger node tests and stability tests from `test_networked_node`
- [ ] Add code to help approximate stabilize and fix fingers intervals as well as time to reach steady state

## Questions

- ~~Should nodes a have reply socket that will send synchronous replies for predecessor requests? No, as the docs note, there is no advantage to router-rep over router-dealer~~
- ~~What is the use case for POLLOUT? Receiving from multiple sockets~~
- ~~Only nodes call find successor; clients call get and put. OR nodes call find successor to get the identity of the hosting node and then get data from host directly.~~
- ~~How does a node know if a found successor message is for it or for a client? How does fix_fingers know which k a found successor is for?~~
- What happens if 2 nodes with the same digest enter at the same time?
