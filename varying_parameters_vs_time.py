import matplotlib.pyplot as plt
from ILP_solver.ILP_solver import solve_TCP_instance
from graph_tools.graph_generator import generate_graph


def modulate_num_nodes():
	num_nodes = [25*i for i in range(1,9)]
	times = []
	for node_count in num_nodes:
		graph, existence_for_node_time, connectivity_demand = generate_graph(num_nodes=node_count)
		times.append(solve_TCP_instance(graph, existence_for_node_time, connectivity_demand, time_output=True))
	print num_nodes, times
	plot(num_nodes, times, "Number of Nodes", "Time (Seconds)", "TCP Runtime for Nodes vs Time ")

def modulate_edge_percentage_active():
	percentage_edges_active = [0.05*i for i in range(1,21)]
	times = []
	for percentage in percentage_edges_active:
		graph, existence_for_node_time, connectivity_demand = generate_graph(edge_connectivity=percentage)
		times.append(solve_TCP_instance(graph, existence_for_node_time, connectivity_demand, time_output=True))
	print percentage_edges_active, times
	plot(percentage_edges_active, times, "Percentage of Edges Active", "Time (Seconds)", "TCP Runtime for Percentage of Edge Active vs Time ")

def modulate_node_percentage_active():
	percentage_nodes_active = [0.05*i for i in range(1,21)]
	times = []
	for percentage in percentage_nodes_active:
		graph, existence_for_node_time, connectivity_demand = generate_graph(active_time_percent=percentage)
		times.append(solve_TCP_instance(graph, existence_for_node_time, connectivity_demand, time_output=True))
	print percentage_nodes_active, times
	plot(percentage_nodes_active, times, "Percentage of Edges Active", "Time (Seconds)", "TCP Runtime for Percentage of Edge Active vs Time ")

def plot(x,y, x_axis, y_axis, title):
	plt.title(title)
	plt.xlabel(x_axis)
	plt.ylabel(y_axis)
	plt.plot(x, y, "-o")
	plt.show()

#modulate_num_nodes()
#modulate_edge_percentage_active()
#modulate_node_percentage_active()
