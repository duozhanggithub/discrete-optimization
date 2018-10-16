#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import namedtuple
from random import shuffle
import time

Colors = namedtuple('Colors', ['label', 'current_color', 'colors_domain', 'adjacent_nodes', 'checked'])
Solution = namedtuple('Solution', ['colors_count', 'colors'])

def solve_it(input_data):
    # Modify this code to run your optimization algorithm

    # parse the input
    lines = input_data.split('\n')

    first_line = lines[0].split()
    node_count = int(first_line[0])
    edge_count = int(first_line[1])

    edges = []
    nodes = dict()
    best_solution = Solution(node_count, [])
    number_of_randomizations = 5
    start_time = time.time()
    max_time = min(60*60*4, edge_count)
    
    for i in range(1, edge_count + 1):
        line = lines[i]
        parts = line.split()
        node_1 = int(parts[0])
        node_2 = int(parts[1])
        edges.append((node_1, node_2))

        #update_node(nodes, node_1, node_2, node_count)
        #update_node(nodes, node_2, node_1, node_count)

    '''
    ordered_nodes = sorted(nodes.items(), key=lambda item: len(item[1].adjacent_nodes), reverse=True)
    labels = []
    for item in ordered_nodes:
        labels.append(item[1][0])
    ordered_edges = []
    l = 0
    while len(ordered_edges) < len(edges):
        current_label = labels[l]
        for edge in edges:
            if edge[0] == current_label:
                ordered_edges.append(edge)
        l += 1
    '''

    #for item in ordered_nodes:
    #    print len(item[1].adjacent_nodes)

    # Perform randomizations on the input and stop the script
    # after some time
    r = 0
    p = 0
    while (r < number_of_randomizations and\
        time.time() - start_time < max_time):
        shuffle(edges)

        nodes = dict()
        i = 0
        while i < edge_count:
            current_edge = edges[i]
            node_1 = current_edge[0]
            node_2 = current_edge[1]

            update_node(nodes, node_1, node_2, node_count)
            update_node(nodes, node_2, node_1, node_count)

            i += 1

        i = 0
        while i < edge_count:
            current_edge = edges[i]
            node_1 = current_edge[0]
            node_2 = current_edge[1]

            if not update_adjacent_nodes(nodes, nodes[node_1], best_solution.colors_count) or\
                not update_adjacent_nodes(nodes, nodes[node_2], best_solution.colors_count):
                break

            i += 1

        # build a trivial solution
        # every node has its own color
        #solution = range(0, node_count)

        # prepare the solution in the specified output format
        #output_data = str(node_count) + ' ' + str(0) + '\n'
        #output_data += ' '.join(map(str, solution))

        used_colors, num_colors = get_used_colors(nodes)

        if num_colors < best_solution.colors_count:
            best_solution = Solution(num_colors, used_colors)
            print num_colors
            #if p < edge_count:
            #    ordered_edges[p], ordered_edges[p+1] = ordered_edges[p+1], ordered_edges[p]
            #    p += 1
            r += 1
        

    # prepare the solution in the specified output format
    output_data = str(best_solution.colors_count) + ' ' + str(0) + '\n'
    output_data += ' '.join(map(str, best_solution.colors))

    return output_data


def update_node(nodes, current_node, adj_node, node_count):
    if not current_node in nodes:
        nodes[current_node] = Colors(current_node, 0, range(0, node_count), [adj_node], False)
    elif not adj_node in nodes[current_node].adjacent_nodes:
        nodes[current_node].adjacent_nodes.append(adj_node)

def update_adjacent_nodes(nodes, current_node, current_colors_count):
    if current_node.checked == False:
        for node in current_node.adjacent_nodes:
            adj_node = nodes[node]
            if current_node.current_color in adj_node.colors_domain:
                #domain = adj_node.colors_domain
                adj_node.colors_domain.remove(current_node.current_color)
                nodes[node] = Colors(node, adj_node.colors_domain[0], \
                    adj_node.colors_domain, adj_node.adjacent_nodes, adj_node.checked)

                used_colors, num_colors = get_used_colors(nodes)
                if num_colors >= current_colors_count:
                    return False

        nodes[current_node.label] = Colors(current_node.label, current_node.colors_domain[0], \
                    current_node.colors_domain, current_node.adjacent_nodes, True)
        
    return True

def get_used_colors(nodes):
    used_colors = map(lambda node: nodes[node].current_color, nodes.keys())
    num_colors = len(set(used_colors))

    return used_colors, num_colors

import sys

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        with open(file_location, 'r') as input_data_file:
            input_data = input_data_file.read()
        print(solve_it(input_data))
    else:
        print('This test requires an input file.  Please select one from the data directory. (i.e. python solver.py ./data/gc_4_1)')

