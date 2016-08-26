from gurobipy import *
import networkx
import time as python_time
sys.path.append("..")
from utils import execution_time, print_edges_in_graph

epsilon = 0.000000001

def solve_TCP_instance(graph, existence_for_node_time, connectivity_demand, detailed_output=True, time_output=False):

	"""
	Given a simple TCP problem instance, returns a minimum weight subgraph that satisfies the demand.

	:param graph: a directed graph with attribute 'weight' on all edges
	:param existence_for_node_time: a dictionary from (node, time) to existence {True, False}
	:param connectivity_demand: a connectivity demand (source, demand)
	:param detailed_output: flag which when True will print the edges in the optimal subgraph
	:param time_output: flag which when True will return the time taken to obtain result rather than the optimal subgraph
	:return:
	"""

	start_time = python_time.time()

	# MODEL SETUP
	# Infer a list of times
	times = list(set([node_time[1] for node_time in existence_for_node_time.keys()]))

	# Sources get +1 sourceflow, destinations get -1, other nodes 0
	sourceflow = {(v, t): 0 for v in graph.nodes_iter() for t in times}
	source, destination = connectivity_demand
	sourceflow[source, 0] = 1
	sourceflow[destination, max(times)] = -1

	# Create empty optimization model
	model = Model('temporal_connectivity')

	# Create variables d_{uvtt'}
	edge_time_variables = {}
	for t in times:
		for t_prime in times:
			for u, v in graph.edges_iter():
				edge_time_variables[u, v, t, t_prime] = model.addVar(vtype=GRB.BINARY, name='edge_time_%s_%s_%s_%s' % (u, v, t, t_prime))

	# Create variables d_{uv}
	edge_variables = {}
	for u, v in graph.edges_iter():
		edge_variables[u, v] = model.addVar(vtype=GRB.BINARY, name='edge_%s_%s' % (u, v))

	model.update()

	# CONSTRAINTS
	# Edge decision constraints (an edge is chosen if it is chosen at any time)
	for t in times:
		for t_prime in times:
			for u, v in graph.edges_iter():
				model.addConstr(edge_variables[u, v] >= edge_time_variables[u, v, t, t_prime])

	# Existence constraints (can only route flow through active nodes)
	for t in times:
		for t_prime in times:
			for u, v in graph.edges_iter():
				model.addConstr(edge_time_variables[u, v, t, t_prime] <= existence_for_node_time[u, t])
				model.addConstr(edge_time_variables[u, v, t, t_prime] <= existence_for_node_time[v, t_prime])

	for t in times:
		for t_prime in times:
			if t != t_prime and t+1 != t_prime:
				model.addConstr(edge_time_variables[u, v, t, t_prime] == 0)

	# Flow conservation constraints
	for t in times:
		for v in graph.nodes_iter():
			if t != 0 and t != max(times):
				model.addConstr(
					quicksum(edge_time_variables[u, v, t-1, t] for u in graph.predecessors_iter(v)) +
					quicksum(edge_time_variables[u, v, t, t] for u in graph.predecessors_iter(v)) +
					sourceflow[v, t] ==
					quicksum(edge_time_variables[v, w, t, t] for w in graph.successors_iter(v)) +
					quicksum(edge_time_variables[v, w, t, t+1] for w in graph.successors_iter(v))
				)
			if t == 0:
				model.addConstr(
					quicksum(edge_time_variables[u, v, t, t] for u in graph.predecessors_iter(v)) +
					sourceflow[v, t] ==
					quicksum(edge_time_variables[v, w, t, t] for w in graph.successors_iter(v)) +
					quicksum(edge_time_variables[v, w, t, t + 1] for w in graph.successors_iter(v))
				)
			if t == max(times):
				model.addConstr(
					quicksum(edge_time_variables[u, v, t - 1, t] for u in graph.predecessors_iter(v)) +
					quicksum(edge_time_variables[u, v, t, t] for u in graph.predecessors_iter(v)) +
					sourceflow[v, t] ==
					quicksum(edge_time_variables[v, w, t, t] for w in graph.successors_iter(v))
				)



	# OBJECTIVE
	# Minimize total path weight
	objective_expression = quicksum(edge_variables[u, v] * graph[u][v]['weight'] for u, v in graph.edges_iter())
	model.setObjective(objective_expression, GRB.MINIMIZE)

	# SOLVE AND RECOVER SOLUTION
	print('-----------------------------------------------------------------------')
	model.optimize()

	subgraph = retreive_and_print_subgraph(model, graph, edge_variables, detailed_output)

	end_time = python_time.time()
	days, hours, minutes, seconds = execution_time(start_time, end_time)
	print('sDCP solving took %s days, %s hours, %s minutes, %s seconds' % (days, hours, minutes, seconds))

	# Return solution iff found
	if time_output:
		return end_time - start_time
	return subgraph if model.status == GRB.status.OPTIMAL else None

def solve_multi_destination_TCP_instance(graph, existence_for_node_time, source, destinations, detailed_output=True, time_output=False):
	"""
	Given a multi-destination TCP problem instance, returns a minimum weight subgraph that satisfies the demand.


	:param graph: a directed graph with attribute 'weight' on all edges
	:param existence_for_node_time: a dictionary from (node, time) to existence {True, False}
	:param source: the source node in the graph
	:param destinations: all destination nodes in the graph
	:param detailed_output: flag which when True will print the edges in the optimal subgraph
	:param time_output: flag which when True will return the time taken to obtain result rather than the optimal subgraph
	:return:
	"""
	start_time = python_time.time()

	# MODEL SETUP
	# Infer a list of times
	times = list(set([node_time[1] for node_time in existence_for_node_time.keys()]))

	# Source get +len(destination) sourceflow, destinations get -1, other nodes 0
	sourceflow = {(v, t): 0 for v in graph.nodes_iter() for t in times}
	sourceflow[source, 0] = len(destinations)
	for destination in destinations:
		sourceflow[destination, max(times)] = -1

	# Create empty optimization model
	model = Model('temporal_connectivity')

	# Create variables d_{uvtt'}
	edge_time_variables = {}
	for t in times:
		for t_prime in times:
			for u, v in graph.edges_iter():
				edge_time_variables[u, v, t, t_prime] = model.addVar(vtype=GRB.INTEGER, lb=0, ub=len(destinations), name='edge_time_%s_%s_%s_%s' % (u, v, t, t_prime))

	# Create variables d_{uv}
	edge_variables = {}
	for u, v in graph.edges_iter():
		edge_variables[u, v] = model.addVar(vtype=GRB.BINARY, name='edge_%s_%s' % (u, v))

	model.update()

	# CONSTRAINTS
	# Edge decision constraints (an edge is chosen if it is chosen at any time)
	for t in times:
		for t_prime in times:
			for u, v in graph.edges_iter():
				model.addConstr(edge_variables[u, v] >= edge_time_variables[u, v, t, t_prime]/len(destinations)) #*******

	# Existence constraints (can only route flow through active nodes)
	for t in times:
		for t_prime in times:
			for u, v in graph.edges_iter():
				model.addConstr(edge_time_variables[u, v, t, t_prime] <= len(destinations) * existence_for_node_time[u, t])
				model.addConstr(edge_time_variables[u, v, t, t_prime] <= len(destinations) * existence_for_node_time[v, t_prime])

	for t in times:
		for t_prime in times:
			if t != t_prime and t+1 != t_prime:
				model.addConstr(edge_time_variables[u, v, t, t_prime] == 0)

	# Flow conservation constraints
	for t in times:
		for v in graph.nodes_iter():
			if t != 0 and t != max(times):
				model.addConstr(
					quicksum(edge_time_variables[u, v, t-1, t] for u in graph.predecessors_iter(v)) +
					quicksum(edge_time_variables[u, v, t, t] for u in graph.predecessors_iter(v)) +
					sourceflow[v, t] ==
					quicksum(edge_time_variables[v, w, t, t] for w in graph.successors_iter(v)) +
					quicksum(edge_time_variables[v, w, t, t+1] for w in graph.successors_iter(v))
				)
			if t == 0:
				model.addConstr(
					quicksum(edge_time_variables[u, v, t, t] for u in graph.predecessors_iter(v)) +
					sourceflow[v, t] ==
					quicksum(edge_time_variables[v, w, t, t] for w in graph.successors_iter(v)) +
					quicksum(edge_time_variables[v, w, t, t + 1] for w in graph.successors_iter(v))
				)
			if t == max(times):
				model.addConstr(
					quicksum(edge_time_variables[u, v, t - 1, t] for u in graph.predecessors_iter(v)) +
					quicksum(edge_time_variables[u, v, t, t] for u in graph.predecessors_iter(v)) +
					sourceflow[v, t] ==
					quicksum(edge_time_variables[v, w, t, t] for w in graph.successors_iter(v))
				)



	# OBJECTIVE
	# Minimize total path weight
	objective_expression = quicksum(edge_variables[u, v] * graph[u][v]['weight'] for u, v in graph.edges_iter())
	model.setObjective(objective_expression, GRB.MINIMIZE)

	# SOLVE AND RECOVER SOLUTION
	print('-----------------------------------------------------------------------')
	model.optimize()

	# Recover minimal subgraph
	subgraph = retreive_and_print_subgraph(model, graph, edge_variables, detailed_output)


	end_time = python_time.time()
	days, hours, minutes, seconds = execution_time(start_time, end_time)
	print('sDCP solving took %s days, %s hours, %s minutes, %s seconds' % (days, hours, minutes, seconds))

	# Return solution iff found
	if time_output:
		return end_time - start_time
	return subgraph if model.status == GRB.status.OPTIMAL else None


def retreive_and_print_subgraph(model, graph, edge_variables, detailed_output):
	"""

	:param model: Optimized gurobi model
	:param graph: a directed graph with attribute 'weight' on all edges
	:param edge_variables: dictionary of edge models
	:param detailed_output: flag which when True will print the edges in the optimal subgraph
	"""
	# Recover minimal subgraph
	subgraph = networkx.DiGraph()
	if model.status == GRB.status.OPTIMAL:
		value_for_edge = model.getAttr('x', edge_variables)
		for u,v in graph.edges_iter():
			if value_for_edge[u,v] > 0:
				subgraph.add_edge(u, v, weight=graph[u][v]['weight'])

		# Print solution
		print('-----------------------------------------------------------------------')
		print('Solved sDCP instance. Optimal Solution costs ' + str(model.objVal))
		if detailed_output:
			print('Edges in minimal subgraph:')
			print_edges_in_graph(subgraph)