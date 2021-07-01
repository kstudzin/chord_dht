#### 1. This ring uses 6-bit identifiers. How many unique identifiers exist on this identifier ring?

2^6 = 64
   
#### 2. Key k is assigned to the node that follows k. This is the successor(k). What is the successor(12)?

successor(12) = N14

#### 3. A node is responsible for all keys between itself and its predecessor node. Which node is responsible for address 32?

N41

#### 4. What is the set of keys that N21 is responsible for? Your answer should use interval notation e.g. [start, end) using brackets to denote that number is included in the set and parens to denote the number is not included in the set

(14, 21]

#### 5. The successor(50) = 60. If we assume that node 50 is aware that node 60 is its current successor, is this enough information for node 50 to know the set of keys that node 60 is responsible for? Explain your answer in a sentence or two

Yes. If 50 know 60 is its successor, then it also knows that it is 60's predecessor. A node is responsible for all the keys between itself and its predecessor.  50 knows this so that it knows what nodes it is responsible for, i.e. it knows that it is responsible for all keys after its successor up to 50. By the same logic, it knows that its successor is responsible for keys after 50 up to 60.

#### 6. If every node in the ring has a pointer to its current successor (e.g. we are ignoring nodes joining and leaving), a simple routing algorithm is possible. To locate the node responsible for a given key K_search, each node determines if it’s successor is responsible for K_search. If yes, then return the successor’s node ID. Else, forward the query onwards to your successor who repeats the process. The pseudocode is shown below. Using this algorithm, how many network hops would it take for node 50 to locate the node responsible for key 12?

It would take 3 hops for N50 to locate key 12. N50 -> N60 -> N4 -> N10. N10 returns its successor N14 as the node responsible for key 12.

#### 7. If every node stored the current (again, we are ignoring nodes joining or leaving), how many network hops would it take for node 4 to determine the node that is responsible for key 22?

It would take 4 hops for N4 to locate key 22. N4 -> N10 -> N14 -> N21. N21 returns N23 which is responsible for key 22

#### 8. Each node N_source maintains a small table of “finger entries”. The table entry for finger[k] on a specific node lists the address of another node N_target. This ‘target’ is the node that is responsible for key N_source + 2^(k-1). In precise terms, this is `successor(N_source + 2^(k-1))`

**If we wanted to create a finger table entry for the “next” node on the identifier ring, (e.g.the node immediately following N_source which we would expect to be the node responsible for the key at N_source + 1), what would be the value of k?**

_**Hint: Remember that node identifiers and key identifiers share the same address space.**_

_**Hint: The node we are after is the successor(N_source + 1). This question is directly asking “what value of k would give us our direct successor”?**_

k=1 

We know this because we can solve 2^(k-1) = 1

#### 9. In the example ring, what is the value for finger[1] on node 14?

N21

We need to find `successor(N_source + 2^(k-1))`
1. First calculate `N_source + 2^(k-1))`
   
   ```
   14 + 2^(1-1) 
   = 14 + 1 
   = 15
   ```

2. Find `successor(15) = N21`

#### 10. This example ring uses 6-bit identifiers. If there was a Node 0 on this ring, what key would be identified by value of finger[6]? What would be the successor of that key (in other words, what would be the value of the finger table for finger[6])?

_**Hint: Refer to question 1.**_

_**Hint: Do not miss that finger is calculated with k-1, not with k directly**_

N41

We need to find `successor(N_source + 2^(k-1))`
1. First calculate `N_source + 2^(k-1))`
   
   ```
   0 + 2^(6-1) 
   = 0 + 2^5
   = 32
   ```

2. Find `successor(32) = N41`

#### 11. If a ring is uses m bits for addresses, then each node stores from finger[1] to finger[m] entries in the finger table. Our ring uses 6-bit addresses, so we store up to finger[6]. A node can only route to the addresses stored in its finger table. What is the maximum number of address values a node can skip past when routing? Express your answer both as a concrete number for our 6-bit example

32 address values

_**Bonus: Express your answer as a formula**_

`(2^m) / 2`

#### 12. For node N10, what is it’s finger[4] entry?

N21

We need to find `successor(N_source + 2^(k-1))`
1. First calculate `N_source + 2^(k-1))`
   
   ```
   10 + 2^(4-1) 
   = 10 + 2^3
   = 18
   ```

2. Find `successor(18) = N21`

#### 13. Is node N21 responsible for key K16?

Yes, `successor(16) = N21`. The predecessor of 21 is only responsible for keys (10, 14]

#### 14. If node 10 wants to find the node responsible for K34 e.g. successor(34), it will search its finger table. Would it be possible for node 21 to be the successor(34)?

_**Hint: Look at the definition of successor. Is it possible for a lower-valued node to be the successor for a higher-valued key?**_

_**Clarification: We are ignoring modular arithmetic here....please don’t worry about the edge case**_

Ignoring the modular arithmetic, it is not possible that `successor(34) = N21` because 34 is greater than 21. 

#### 15. If node 10 wants to find the node responsible for K34 e.g. successor(34), it will search its finger table. Would it be possible for node 50 to be the successor(34)?

Yes it is possible to `successor(34) = N50`. If N41 dies, then this will be the case.

#### 16. In general, does a node’s identifier need to be lower or higher than a key’s identifier for the node to be a possible candidate for successor(key)?

In general a node's identifier needs to higher than a key's identifier for a node to be a possible candidate for `successor(key)`

#### 17. If a node N knows that it is not responsible for a key K, and we assume routing can only go in the positive direction, then is the key identifier for K bigger or smaller than the node identifier for N?

If a node N knows that it is not responsible for a key K, then the key identifier for K is bigger than the key identifier for N.

#### 18. Build the finger table for node 4
```
|---|------------------|-----------|
| K | 4 + 2^(K-1)      | finger[K] |
|---|------------------|-----------|
| 1 | 4 + 2^(1-1) = 5  |    N10    |
|---|------------------|-----------|
| 2 | 4 + 2^(2-1) = 6  |    N10    |
|---|------------------|-----------|
| 3 | 4 + 2^(3-1) = 8  |    N10    |
|---|------------------|-----------|
| 4 | 4 + 2^(4-1) = 12 |    N14    |
|---|------------------|-----------|
| 5 | 4 + 2^(5-1) = 20 |    N21    |
|---|------------------|-----------|
| 6 | 4 + 2^(6-1) = 36 |    N41    |
|---|------------------|-----------|
```

#### 19. The following is the chord routing algorithm. Attempt to route from node 4, looking for key 12.

```
n4.find_successor(12)
 |-> 12 not in (4, 10]
 |-> n4.closest_preceding_node(12)
      |-> finger[6] = N41, 41 not in (4,12)
      |-> finger[5] = N21, 21 not in (4, 12)
      |-> finger[4] = N14, 14 not in (4, 12)
      |-> finger[3] = N10, 10 is in (4, 12)
      |-> return N10
 |-> n10.find_successor(12)
      |-> 12 is in (10,  14]
      |-> return N14
```
