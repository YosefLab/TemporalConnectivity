from gurobipy import *
import networkx
import time as python_time
sys.path.append("..")
from utils import execution_time, print_edges_in_graph

epsilon = 0.000000001

def solve_TCP_instance(model, graph, edge_variables, detailed_output=True, time_output=False):

	"""
	Given a simple TCP problem instance, returns a minimum weight subgraph that satisfies the demand.

	:param graph: a directed graph with attribute 'weight' on all edges
	:param model: a Gurobi model to be optimized
	:param edge_variables: a dictionary of variables corresponding to the variables d_v,w
	:param detailed_output: flag which when True will print the edges in the optimal subgraph
	:param time_output: flag which when True will return the time taken to obtain result rather than the optimal subgraph
	:return: a optimal subgraph containing the path if the solution is Optimal, else None
	"""

	start_time = python_time.time()


	# SOLVE AND RECOVER SOLUTION
	print('-----------------------------------------------------------------------')
	model.optimize()
	print "Solution Count: " + str(model.SolCount)
	subgraph = retreive_and_print_subgraph(model, graph, edge_variables, detailed_output)

	end_time = python_time.time()
	days, hours, minutes, seconds = execution_time(start_time, end_time)
	print('sDCP solving took %s days, %s hours, %s minutes, %s seconds' % (days, hours, minutes, seconds))

	# Return solution iff found
	if time_output:
		return end_time - start_time

	return subgraph if model.status == GRB.status.OPTIMAL else None

def solve_multi_destination_TCP_instance(model, graph, edge_variables, detailed_output=True, time_output=False):
	"""
	Given a multi-destination TCP problem instance, returns a minimum weight subgraph that satisfies the demand.

	:param graph: a directed graph with attribute 'weight' on all edges
	:param model: a Gurobi model to be optimized
	:param edge_variables: a dictionary of variables corresponding to the variables d_v,w
	:param detailed_output: flag which when True will print the edges in the optimal subgraph
	:param time_output: flag which when True will return the time taken to obtain result rather than the optimal subgraph
	:return: a optimal subgraph containing the path(s) if the solution is Optimal, else None
	"""
	start_time = python_time.time()


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

def generate_TCP_model(graph, existence_for_node_time, connectivity_demand):
	"""

	:param graph: a directed graph with attribute 'weight' on all edges
	:param existence_for_node_time: a dictionary from (node, time) to existence {True, False}
	:param connectivity_demand: a connectivity demand (source, demand)
	:return: a Gurobi model pertaining to the TCP instance, and the edge_variables involved
	"""
	# MODEL SETUP
	# Infer a list of times
	times = list(set([node_time[1] for node_time in existence_for_node_time.keys()]))

	# Sources get +1 sourceflow, destinations get -1, other nodes 0
	sourceflow = {(v, t): 0 for v in graph.nodes_iter() for t in times}
	source, destination = connectivity_demand
	sourceflow[source, 0] = 1
	sourceflow[destination, max(times)] = -1

	model = Model('temporal_connectivity')

	# Create variables d_{uvtt'}
	edge_time_variables = {}
	for t in times:
		for t_prime in times:
			for u, v in graph.edges_iter():
				edge_time_variables[u, v, t, t_prime] = model.addVar(vtype=GRB.BINARY,
																	 name='edge_time_%s_%s_%s_%s' % (u, v, t, t_prime))

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
			if t != t_prime and t + 1 != t_prime:
				model.addConstr(edge_time_variables[u, v, t, t_prime] == 0)

	# Flow conservation constraints
	for t in times:
		for v in graph.nodes_iter():
			if t != 0 and t != max(times):
				model.addConstr(
					quicksum(edge_time_variables[u, v, t - 1, t] for u in graph.predecessors_iter(v)) +
					quicksum(edge_time_variables[u, v, t, t] for u in graph.predecessors_iter(v)) +
					sourceflow[v, t] ==
					quicksum(edge_time_variables[v, w, t, t] for w in graph.successors_iter(v)) +
					quicksum(edge_time_variables[v, w, t, t + 1] for w in graph.successors_iter(v))
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

	return model, edge_variables

def generate_mTCP_model(graph, existence_for_node_time, source, destinations):
	"""
	:param graph: a directed graph with attribute 'weight' on all edges
	:param existence_for_node_time: a dictionary from (node, time) to existence {True, False}
	:param connectivity_demand: a connectivity demand (source, demand)
	:return: a Gurobi model pertaining to the mTCP instance, and the edge_variables involved
	"""
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

	return model, edge_variables


def add_optimal_solution_constraint(model, subgraph, edge_variables, strictly_optimal=False, additional_constraint=0):
	"""

	:param model: a Gurobi model to be optimized
	:param subgraph: a directed graph with attribute 'weight' on all edges, which contains the previous
					 optimal solution for the model
	:param edge_variables: a dictionary of variables corresponding to the variables d_v,w
	:param strictly_optimal: flag which when True does not allow subgraphs that are supergraphs of that in subgraph
	:param additional_constraint: additional amount to subtract from optimal solution, eg if optimal solution had length(5)
							 allow us to only use 3 edges from the subgraph if additional_constraint = 2
	:return:
	"""
	if not strictly_optimal:
		model.addConstr(quicksum(edge_variables[u, v] for u,v in subgraph.edges()) <= max(0, len(subgraph.edges())-1-additional_constraint))
	else:
		model.addConstr(quicksum(edge_variables[u, v] for u,v in subgraph.edges()) - quicksum(edge for edge in edge_variables.values()) <= max(0, len(subgraph.edges())-1-additional_constraint))


	return model



def retreive_and_print_subgraph(model, graph, edge_variables, detailed_output):
	"""

	:param model: an optimized gurobi model
	:param graph: a directed graph with attribute 'weight' on all edges
	:param edge_variables: a dictionary of variables corresponding to the variables d_v,w
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
		return subgraph

