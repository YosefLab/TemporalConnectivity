# Temporal Connectivity

This project implements an algorithm for solving the Temporal Connectivity problem in time-varying graphs. It also contains tools for generating interesting instances of the problem to test the feasibility of the algorithm in practice.


#### Problem Statement

Formally, the Temporal Connectivity problem is the following: we are given

1. A weighted directed graph _G = (V,E,w)_.

2. An _existence function_ _ρ : V × [T] → {0,1}_ indicating whether each vertex exists at each time.

3. A connectivity demand from a source to a destination (Or single source multiple destinations)

The task is to find a subgraph _H ⊆ G_ of minimum total weight such that every demand _(s,d) ∈ D_ is satisfied: there exists an _s → d_ path in _H_ that is consistant through time.

Throughout the code we will refer to one source destination demand as TCP, and single source multi destination as mTCP

Theoretical aspects of this problem, as well as our algorithm, will be detailed in a forthcoming paper.


---
### Solving Dynamic Steiner Network Instances

The main TCP and mTCP solver is invoked by calling the following functions in `/ILP_solver/ILP_solver.py`:

```python
# In the following, G is a NetworkX DiGraph, rho is a dictionary, and D is a list of triples. See the docstring for details.
solve_TCP_instance(graph=G, existence_for_node_time=rho, connectivity_demands=D, detailed_output=False, time_output=False)
```
```python
# In the following, G is a NetworkX DiGraph, rho is a dictionary, and D is a list of triples. See the docstring for details.
solve_TCP_instance(graph=G, existence_for_node_time=rho, source=s, destinations=D, detailed_output=False, time_output=False)
```
_Note: This function works by modeling the instance as an integer linear program (ILP), then solving using an optimization library (Gurobi).



### Generating Artificial Instances

We implement the following procedure for generating random TCP instances (mTCP coming soon...):

1. Instantiate a pool of nodes _V_.

2. Create an edge between vertices v, w with probability edge_connectivity

3. rho(v,t) = 1 with probability active_time_percent

4. T = {0,...,max_time}

5. w(e) = Random number within the range defined by weight_distribution


This procedure is implemented in the following function in `/graph_tools/graph_generator.py`:

```python
# In the following, node_count = |V|, tree_count = β, and tree_span = γ
generate_graph(num_nodes=100, edge_connectivity=1.0, active_time_percent=1.0, max_time=3, weight_distribution=(1.0,1.0))
```

To generate an instance and run the algorithm on it all at once, call the following function in `ILP_solver_tests.py`:

```python
test_solve_random_instance(node_count=100, tree_count=10, tree_span=20, detailed_output=False)
```

