#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import namedtuple
Item = namedtuple("Item", ['index', 'value', 'weight'])

def solve_it(input_data):
    # Modify this code to run your optimization algorithm

    # parse the input
    lines = input_data.split('\n')

    firstLine = lines[0].split()
    item_count = int(firstLine[0])
    capacity = int(firstLine[1])

    items = []

    for i in range(1, item_count+1):
        line = lines[i]
        parts = line.split()
        items.append(Item(i-1, int(parts[0]), int(parts[1])))

    if len(items) < 40:
        value, taken = depth_first_relaxed_capacity_simple(items, capacity)
    elif len(items) <= 200 or len(items) == 1000:
        value, taken = dynamic_programming_simple(items, capacity)
    else:
        value, taken = greedy_most_value_density_items(items, capacity)
    #value, taken = greedy_simple(items, capacity)
    #value, taken = greedy_max_number_of_items(items, capacity)
    #value, taken = greedy_most_valuable_items(items, capacity)
    #value, taken = greedy_most_value_density_items(items, capacity)
    #value, taken = greedy_unique_weight_oredered(items, capacity)
    #value, taken = dynamic_programming_simple(items, capacity)
    #value, taken = depth_first_relaxed_capacity_simple(items, capacity)
    #value, taken = depth_first_relaxed_value_per_kg_simple(items, capacity)
    #value, taken = depth_first_ordered_by_weight(items, capacity)

    # prepare the solution in the specified output format
    output_data = str(value) + ' ' + str(0) + '\n'
    output_data += ' '.join(map(str, taken))
    return output_data

'''
a trivial greedy algorithm for filling the knapsack
it takes items in-order until the knapsack is full

Obtained value in ks_4_0: 18
Obtained value in ks_100_2: 9869
Obtained value in ks_500_0: 49877
Obtained value in ks_1000_0: 99488
Obtained value in ks_10000_0: 1012574
Obtained value in ks_slides: 10
Obtained value in ks_30_0: 
Obtained value in ks_50_0: 
Obtained value in ks_200_0: 
Obtained value in ks_400_0: 
'''
def greedy_simple(items, capacity):
    value = 0
    weight = 0
    taken = [0]*len(items)

    for item in items:
        if weight + item.weight <= capacity:
            taken[item.index] = 1
            value += item.value
            weight += item.weight
    
    return value, taken

'''
Greedy algorithm that takes in consideration
smaller items first se we can take the max
number of items

Obtained value in ks_4_0: 12
Obtained value in ks_100_2: 9628
Obtained value in ks_500_0: 50502
Obtained value in ks_1000_0: 99488
Obtained value in ks_10000_0: 994412
Obtained value in ks_slides: 10
'''
def greedy_max_number_of_items(items, capacity):
    items_ordered = sorted(items, key=lambda x: x.weight)
    return greedy_simple(items_ordered, capacity)

'''
Greedy algorithm that takes in consideration
most valuable items first

Obtained value in ks_4_0: 19
Obtained value in ks_100_2: 10547
Obtained value in ks_500_0: 54408
Obtained value in ks_1000_0: 107768
Obtained value in ks_10000_0: 1094968
Obtained value in ks_slides: 14
'''
def greedy_most_valuable_items(items, capacity):
    items_ordered = sorted(items, key=lambda x: x.value, reverse=True)
    return greedy_simple(items_ordered, capacity)

'''
Greedy algorithm that takes in consideration
the value and then the value density ($/kg)

Obtained value in ks_4_0: 18
Obtained value in ks_100_2: 10710
Obtained value in ks_500_0: 54408
Obtained value in ks_1000_0: 107801
Obtained value in ks_10000_0: 10946968
Obtained value in ks_slides: 20
'''
def greedy_most_value_density_items(items, capacity):
    items_ordered = sorted(items, key=lambda x: x.value, reverse=True)
    items_ordered = sorted(items_ordered, key=lambda x: x.value/x.weight, reverse=True)
    return greedy_simple(items_ordered, capacity)

'''
Greedy algorithm that order the items by their weight
but takes only one item of each weight.

Obtained value in ks_4_0: 18
Obtained value in ks_100_2: 9869
Obtained value in ks_500_0: 49877
Obtained value in ks_1000_0: 100891
Obtained value in ks_10000_0: 1012574
Obtained value in ks_slides: 18
'''
def greedy_unique_weight_oredered(items, capacity):
    items_ordered = sorted(items, key=lambda x: x.weight)
    current_weight = 0

    value = 0
    weight = 0
    taken = [0]*len(items)

    for item in items:
        if weight + item.weight <= capacity and item.weight != current_weight:
            taken[item.index] = 1
            value += item.value
            weight += item.weight
            current_weight = item.weight
    
    return value, taken

'''
Implementation of Dynamic Programming algorithm
that just reads the input in the default order

Obtained value in ks_4_0: 19 (0.04s)
Obtained value in ks_100_2: 10892 (5.20s)
Obtained value in ks_500_0: 54939 (18.07s)
Obtained value in ks_1000_0: 109899 (70.93s)
Obtained value in ks_10000_0: (too slow)
Obtained value in ks_slides: 20 (0.02s)
'''
def dynamic_programming_simple(items, capacity):
    capacity_range = range(0, capacity+1)
    items_range = range(0, len(items)+1)

    # Setup result table
    # [[v0k0, v0k1, v0k2...], [v1k0, v1k1, v1k2...], ...]
    result_matrix = [[0 for x in capacity_range] for y in items_range]

    # First, we fill the first item's column
    for j in range(1, len(capacity_range)):
        current_item = items[0]
        if current_item.weight <= j:
            result_matrix[1][j] = current_item.value

    for i in range(2, len(items_range)):
        for j in range(1, len(capacity_range)):
            current_item = items[i-1]
            prev_item_value = result_matrix[i-1][j]
            if current_item.weight <= j:
                # This variable retrieves the value on the previous column 
                # where the line is the current capacity (j) minus the weight
                # of the current item.
                plausible_item_previous_column_val = \
                    result_matrix[i-1][j-current_item.weight]
                result_matrix[i][j] = max(result_matrix[i-1][j],\
                    current_item.value + plausible_item_previous_column_val)
            else:
                result_matrix[i][j] = prev_item_value

    # Tracing back
    i = len(items)
    j = capacity
    value = 0
    weight = 0
    taken = [0]*i

    while i > 0 and j > 0:
        current_value = result_matrix[i][j]
        prev_value = result_matrix[i-1][j]
        if prev_value != current_value:
            taken[i-1] = 1
            value += items[i-1].value
            j -= items[i-1].weight
        i -= 1

    return value, taken

'''
Implementation of Depth-first algorithm
with capacity relaxation.

Obtained value in ks_4_0: 19 (0.02s)
Obtained value in ks_30_0: 99798 (0.13s)
'''
def depth_first_relaxed_capacity_simple(items, capacity, relaxed_estimate=None):
    if not relaxed_estimate:
        relaxed_estimate = get_relaxed_capacity_value(items)
    num_items = len(items)
    taken = [0]*num_items

    max_val, taken = process_depth_first(items, capacity, relaxed_estimate, 0, 0, num_items, 0, taken, True)
    max_val, taken = process_depth_first(items, capacity, relaxed_estimate, 0, 0, num_items, max_val, taken, False)

    return max_val, taken

def depth_first_relaxed_value_per_kg_simple(items, capacity):
    items_ordered = sorted(items, key=lambda x: x.value, reverse=True)
    items_ordered = sorted(items_ordered, key=lambda x: x.value/x.weight, reverse=True)
    relaxed_estimate = get_relaxed_value_per_kg_value(items_ordered, capacity)

    max_val, taken = depth_first_relaxed_capacity_simple(items_ordered, capacity, relaxed_estimate)
    return max_val, taken

def depth_first_ordered_by_weight(items, capacity):
    items_ordered = sorted(items, key=lambda x: x.weight, reverse=True)
    relaxed_estimate = get_relaxed_value_per_kg_value(items_ordered, capacity)

    max_val, taken = depth_first_relaxed_capacity_simple(items_ordered, capacity, relaxed_estimate)
    return max_val, taken

def process_depth_first(items, capacity, estimate, i, value, num_items, current_max_value, taken, select):
    max_val = current_max_value
    if i < num_items:
        current_item = items[i]
        if select == True:
            value += current_item.value
            capacity -= current_item.weight
        else:
            estimate -= current_item.value
        
        if capacity < 0:
            return current_max_value, taken
        if estimate <= current_max_value:
            return current_max_value, taken
        if value == estimate:
            taken = [0]*num_items
            taken[i] = int(select)
            return value, taken

        max_val, taken = process_depth_first(items, capacity, estimate, i+1, value, num_items, max_val, taken, True)
        max_val, taken = process_depth_first(items, capacity, estimate, i+1, value, num_items, max_val, taken, False)
    
        if max_val > current_max_value:
            taken[i] = int(select)
    return max_val, taken

def get_relaxed_capacity_value(items):
    value = 0
    for item in items:
        value += item.value

    return value

def get_relaxed_value_per_kg_value(items, capacity):
    value = 0
    weight = 0
    i = 0
    while weight <= capacity and i < len(items):
        item = items[0]
        weight += item.weight
        if weight <= capacity:
            value += item.value
        else:
            diff = capacity - weight - item.weight
            proportion = item.weight/diff
            value += item.value/proportion
        i += 1

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        with open(file_location, 'r') as input_data_file:
            input_data = input_data_file.read()
        print(solve_it(input_data))
    else:
        print('This test requires an input file.  Please select one from the data directory. (i.e. python solver.py ./data/ks_4_0)')

