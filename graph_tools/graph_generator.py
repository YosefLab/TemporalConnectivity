"""
This file generates a random graph w/ a source destination pair
"""

import networkx
import random

def generate_graph(num_nodes=100, edge_connectivity=1.0, active_time_percent=1.0, max_time=3, weight_distribution=(1.0,1.0)):
	"""
	:param num_nodes: Number of nodes in graph
	:param edge_connectivity: We begin with a fully connected graph, and remove each edge based on (1-edge_connectivity)*100%
	:param active_time_percent: We begin with a fully active graph, and remove time points per vertice based on (1-edge_connectivity)*100%
	:param weight_distribution: What range to choose random weights from
	:return: graph, existence_for_node_time (dictionary: V x T -> 1/0), connectivity_demand (source, destination)
	"""
	graph = networkx.DiGraph()
	nodes = generate_nodes(num_nodes)
	for node in nodes:
		graph.add_node(node)

	source,destination = random.sample(nodes,2)

	for begin in nodes:
		for end in nodes:
			if end != source and begin != destination:
				if begin != end:
					if random.random() < edge_connectivity:
						weight = random.uniform(weight_distribution[0], weight_distribution[1])
						graph.add_edge(begin, end, weight=weight)
				else:
					graph.add_edge(begin, end, weight=0.001)

	existence_for_node_time = {(source,0):1, (destination,max_time):1}
	for i in range(1, max_time+1):
		existence_for_node_time[(source, i)] = 0

	for i in range(0, max_time):
		existence_for_node_time[(destination, i)] = 0

	for node in nodes:
		for i in range(0, max_time+1):
			if node != source and node != destination:
				is_active = int(random.random() < active_time_percent)
				existence_for_node_time[(node, i)] = is_active


	return graph, existence_for_node_time, (source, destination)


def generate_nodes(num_nodes=100):
	return list(range(1,num_nodes+1))

