from ILP_solver.ILP_solver import solve_TCP_instance, solve_multi_destination_TCP_instance, generate_TCP_model, generate_mTCP_model, add_optimal_solution_constraint
from graph_tools.graph_generator import generate_graph, generate_scale_free_graph
import time as python_time
from utils import execution_time
import networkx

def test_TCP_instance():
	"""
	Tests the TCP ILP solver on an instance of necessary edge reuse.
	"""
	graph = networkx.DiGraph()

	graph.add_edge(2, 2, weight=0.001)
	graph.add_edge(1, 2, weight=3)
	graph.add_edge(2, 6, weight=6)
	graph.add_edge(1, 3, weight=5)
	graph.add_edge(3, 4, weight=1)
	graph.add_edge(4, 5, weight=1)
	graph.add_edge(5, 3, weight=1)
	graph.add_edge(4, 6, weight=1)

	existence_for_node_time = {
		(1, 0): 1, (1, 1): 0, (1, 2): 0, (1, 3): 0, (1, 4): 0, (1, 5): 0, (1, 6): 0,
		(2, 0): 0, (2, 1): 1, (2, 2): 1, (2, 3): 1, (2, 4): 1, (2, 5): 1, (2, 6): 0,
		(3, 0): 0, (3, 1): 1, (3, 2): 1, (3, 3): 0, (3, 4): 1, (3, 5): 0, (3, 6): 0,
		(4, 0): 0, (4, 1): 0, (4, 2): 1, (4, 3): 0, (4, 4): 0, (4, 5): 1, (4, 6): 0,
		(5, 0): 0, (5, 1): 0, (5, 2): 1, (5, 3): 1, (5, 4): 0, (5, 5): 0, (5, 6): 0,
		(6, 0): 0, (6, 1): 0, (6, 2): 0, (6, 3): 0, (6, 4): 0, (6, 5): 0, (6, 6): 1,
	}

	connectivity_demand = (1, 6)
	model, edge_variables = generate_TCP_model(graph, existence_for_node_time, connectivity_demand)
	subgraph = solve_TCP_instance(model, graph, edge_variables)



def test_mTCP_instance():
	"""
	Tests the mTCP ILP solver on an instance of necessary edge reuse.
	"""
	graph = networkx.DiGraph()

	graph.add_edge(2, 2, weight=0.001)
	graph.add_edge(1, 2, weight=3)
	graph.add_edge(2, 6, weight=6)
	graph.add_edge(1, 3, weight=5)
	graph.add_edge(3, 4, weight=1)
	graph.add_edge(4, 5, weight=1)
	graph.add_edge(5, 3, weight=1)
	graph.add_edge(4, 6, weight=1)

	existence_for_node_time = {
		(1, 0): 1, (1, 1): 0, (1, 2): 0, (1, 3): 0, (1, 4): 0, (1, 5): 0, (1, 6): 0,
		(2, 0): 0, (2, 1): 1, (2, 2): 1, (2, 3): 1, (2, 4): 1, (2, 5): 1, (2, 6): 1,
		(3, 0): 0, (3, 1): 1, (3, 2): 1, (3, 3): 0, (3, 4): 1, (3, 5): 0, (3, 6): 0,
		(4, 0): 0, (4, 1): 0, (4, 2): 1, (4, 3): 0, (4, 4): 0, (4, 5): 1, (4, 6): 0,
		(5, 0): 0, (5, 1): 0, (5, 2): 1, (5, 3): 1, (5, 4): 0, (5, 5): 0, (5, 6): 1,
		(6, 0): 0, (6, 1): 0, (6, 2): 0, (6, 3): 0, (6, 4): 0, (6, 5): 0, (6, 6): 1,
	}
	model, edge_variables = generate_mTCP_model(graph, existence_for_node_time, 1, [2, 5])
	subgraph = solve_multi_destination_TCP_instance(model, graph, edge_variables)


def test_generated_TCP():
	graph, existence_for_node_time, connectivity_demand = generate_graph(num_nodes=100, edge_connectivity=.1, max_time=3, active_time_percent=1)
	model, edge_variables = generate_TCP_model(graph, existence_for_node_time, connectivity_demand)
	subgraph = solve_TCP_instance(model, graph, edge_variables)
	print "Connectivity Demand: " + str(connectivity_demand)
	return existence_for_node_time, graph

def test_generated_sfTCP():
	print "Start"
	graph, existence_for_node_time, connectivity_demand = generate_scale_free_graph(num_nodes=10000, max_time=10, active_time_percent=0.25)
	print "GotGraph"
	model, edge_variables = generate_TCP_model(graph, existence_for_node_time, connectivity_demand)
	num_iterations = 10
	d = {}
	solutions = []
	start_time = python_time.time()

	for _ in range(num_iterations):
		subgraph = solve_TCP_instance(model, graph, edge_variables)
		if not subgraph:
			break
		model = add_optimal_solution_constraint(model, subgraph, edge_variables)
		solutions.append(subgraph)
		for vertex in subgraph.nodes():
			if vertex in d:
				d[vertex] += 1
			else:
				d[vertex] = 1


	end_time = python_time.time()
	days, hours, minutes, seconds = execution_time(start_time, end_time)
	print('sDCP solving took %s days, %s hours, %s minutes, %s seconds' % (days, hours, minutes, seconds))

	d_view = [(v, k) for k, v in d.iteritems()]
	d_view.sort(reverse=True)
	print d_view
	print "Demand: " + str(connectivity_demand)
	return graph, subgraph

#test_TCP_instance()
#test_mTCP_instance()
test_generated_TCP()
#graph, subgraph = test_generated_sfTCP()
