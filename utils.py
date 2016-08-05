import datetime

def execution_time(start_time, end_time):
	execution_delta = datetime.timedelta(seconds=end_time - start_time)
	return execution_delta.days, execution_delta.seconds // 3600, (execution_delta.seconds // 60) % 60, execution_delta.seconds % 60

def print_edges_in_graph(graph, edges_per_line=5):
	edges_string = ''
	edges_printed_in_line = 0

	for u,v in graph.edges_iter():
		edges_string += '%s -> %s        ' % (u, v)
		edges_printed_in_line += 1
		if edges_printed_in_line >= edges_per_line:
			edges_printed_in_line = 0
			edges_string += '\n'

	print edges_string