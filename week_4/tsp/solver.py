#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
from collections import namedtuple
from random import shuffle
from random import random
import time

Point = namedtuple("Point", ['x', 'y'])

def length(point1, point2):
    return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

def solve_it(input_data):
    # Modify this code to run your optimization algorithm

    # parse the input
    lines = input_data.split('\n')

    nodeCount = int(lines[0])

    points = []
    for i in range(1, nodeCount+1):
        line = lines[i]
        parts = line.split()
        points.append(Point(float(parts[0]), float(parts[1])))

    # build a trivial solution
    # visit the nodes in the order they appear in the file
    solution = range(0, nodeCount)

    # calculate the length of the tour
    obj = calculate_tour_length(points, solution, nodeCount)

    # First meta-heuristic approach: multi-starts
    #final_solution, obj = meta_heuristic_restarts(points, solution, obj, nodeCount)

    # Second meta-heuristic approach: Metropolis/Annealing
    final_solution, obj = meta_heuristic_annealing(points, solution, obj, nodeCount)

    # prepare the solution in the specified output format
    output_data = '%.2f' % obj + ' ' + str(0) + '\n'
    output_data += ' '.join(map(str, final_solution))

    return output_data

def meta_heuristic_restarts(points, current_solution, current_obj, node_count):
    final_solution = []
    starting_points = []
    i = 0
    trivial_obj = current_obj
    while i < 5:
        s = 0
        tmp_solution, tmp_obj = two_opt_neighborhood(points, current_solution, node_count)
        print tmp_obj
        if tmp_obj < current_obj:
            current_obj = tmp_obj
            final_solution = tmp_solution

        shuffle(current_solution)
        if len(starting_points) < int(node_count/2):
            while current_solution[0] in starting_points:
                shuffle(current_solution)
            starting_points.append(current_solution[0])
        current_trivial_obj = calculate_tour_length(points, current_solution, node_count)
        while current_trivial_obj > trivial_obj and s <= int(node_count/2):
            shuffle(current_solution)
            current_trivial_obj = calculate_tour_length(points, current_solution, node_count)
            s += 1
        trivial_obj = current_trivial_obj

        i += 1

    return current_solution, current_obj

def meta_heuristic_annealing(points, current_solution, current_obj, node_count):
    current_solution, obj = two_opt_neighborhood_with_annealing(points, current_solution, node_count)

    return current_solution, obj

    '''
    final_solution = []
    starting_points = []
    i = 0
    trivial_obj = current_obj
    while i < 10:
        s = 0
        tmp_solution, tmp_obj = two_opt_neighborhood_with_annealing(points, current_solution, node_count)
        
        if tmp_obj < current_obj:
            current_obj = tmp_obj
            final_solution = tmp_solution

        shuffle(current_solution)
        if len(starting_points) < int(node_count/2):
            while current_solution[0] in starting_points:
                shuffle(current_solution)
            starting_points.append(current_solution[0])
        current_trivial_obj = calculate_tour_length(points, current_solution, node_count)
        while current_trivial_obj > trivial_obj and s <= int(node_count/2):
            shuffle(current_solution)
            current_trivial_obj = calculate_tour_length(points, current_solution, node_count)
            s += 1
        trivial_obj = current_trivial_obj

        i += 1

    return current_solution, current_obj
    '''

'''
2-opt algorithm implementation.
Source: https://en.wikipedia.org/wiki/2-opt
'''
def two_opt_neighborhood(points, current_solution, node_count):
    # 2-opt implementation
    improvement = 0
    current_improvement = 0
    current_distance = calculate_tour_length(points, current_solution, node_count)
    solution_improved = True
    best_distance = current_distance
    best_solution = current_solution

    while solution_improved == True:
        local_minima_found = False
        while local_minima_found == False:
            local_minima_found, improvement, current_solution, current_distance = \
                find_two_opt_solution(node_count, current_solution, current_distance, points, 0)

        if improvement <= 0:
            solution_improved = False
        else:
            current_improvement = improvement
            if current_distance < best_distance:
                best_distance = current_distance
                best_solution = current_solution

    return best_solution, best_distance

'''
2-opt algorithm with annealing meta-heuristic.
'''
def two_opt_neighborhood_with_annealing(points, current_solution, node_count):
    current_distance = calculate_tour_length(points, current_solution, node_count)
    initial_solution = list(current_solution)
    distances = [current_distance]
    solutions = [current_solution]
    best_distance = current_distance
    best_solution = current_solution
    
    nodes_num_len = len(str(int(node_count)))
    min_mean = 5
    if nodes_num_len == 3:
        min_mean = 500
    if nodes_num_len == 4:
        min_mean = 5000
    if nodes_num_len == 5:
        min_mean = 50000

    start_time = time.time()
    max_time = 60*60*4

    # i = 0
    # while i < 3:
    #     lower_distance = distances[-1]
    #     tmp_solution = list(solutions[-1])
    #     shuffle(tmp_solution)
    #     tmp_distance = calculate_tour_length(points, tmp_solution, node_count)
    #     while tmp_distance >= lower_distance:
    #         shuffle(tmp_solution)
    #         tmp_distance = calculate_tour_length(points, tmp_solution, node_count)
    #     solutions.append(tmp_solution)
    #     distances.append(tmp_distance)
    #     i+= 1

    #for i in range(0, len(solutions)):
    i = 0
    k = 0

    solution = list(best_solution)
    distance = best_distance
    
    while best_distance > 430 and \
        time.time() - start_time < max_time:
        best_distance = 99999999
        last_improvements = []
        
        t_base = 9999999
        t = 1*t_base
        visited_values = [distance]
        num_non_improvements = 0
        num_small_improvements = 0
        last_values = []
        last_best_solutions = [(solution, distance)]
        worst_solution = (list(solution), distance)
        num_repeated_best_solutions = 0
        print "INICIO IERAÇÃO-------------------------------------"
        solution_improved = True
        #if i > 0:
        #    shuffle(solution)

        while solution_improved == True and best_distance > 440 and time.time() - start_time < max_time:
            local_minima_found = False
            while local_minima_found == False and time.time() - start_time < max_time:
                local_minima_found, improvement, solution, distance, accepted_decrease = \
                    find_two_opt_solution_with_metropolis_meta_heuristic(\
                        node_count, solution, distance, points, t, visited_values)
            print distance
            print best_distance

            #if distance > worst_solution[1]:
            #    worst_solution = (list(solution), distance)
                #shuffle(worst_solution[0])

            if len(last_values) > 100:
                last_values = []
            last_values.append(distance)
            
            if improvement == 0 or\
                last_values.count(distance) >= 50:
                last_values = []
                #t *= 10 
                num_non_improvements = 0
                
            elif improvement < 0:
                solution_improved = accepted_decrease
                num_non_improvements += 1
                
                #if accepted_decrease == True:
                #    t *= 0.1
                
                if num_non_improvements == 100:
                    #t *= 0.5
                    num_non_improvements = 0
                    #solution = list(worst_solution[0])
                    #shuffle(solution)
                    #distance = calculate_tour_length(points, solution, node_count)
                
                #num_improvements = 0
            elif improvement > 0:
                if distance < best_distance:
                    best_distance = distance
                    best_solution = list(solution)

                last_improvements.append(distance)
                last_improvements.sort()
                last_improvements.reverse()
                num_non_improvements = 0

                #t *= 0.99
                if len(last_improvements) > 1:
                    improvement_val = last_improvements[-2] - last_improvements[-1]
                    if improvement_val > 0 and \
                        improvement_val <= last_improvements[-2]/1000:
                        #print "ESQUENTA++++++++++++++++++++++++++++++++++++"
                        t = t*10
                        num_small_improvements += 1
                    if num_small_improvements == 5:
                        t = t_base
                        num_small_improvements = 0

                        solution = list(worst_solution[0])
                        #shuffle(solution)
                        distance = calculate_tour_length(points, solution, node_count)
                    del last_improvements[0]
                '''
                if len(last_improvements) > 5:
                    del last_improvements[0]
                    mean = sum(last_improvements) / len(last_improvements)
                    if mean < 5:
                        print "ENTROU!!!!!!!!!!!!!!!!!!!!!!!!!!"
                        t = (i)*t_base
                '''
                #num_improvements += 1
                #if num_improvements == 3:
                #    num_improvements = 0
                #    t *= 100

            '''
            last_best_solutions.append((list(best_solution), best_distance))
            if len(last_best_solutions) > 500:
                del last_best_solutions[0]
                partial_items = last_best_solutions[95:]
                if all(item[1] == best_distance for item in partial_items):
                    solution = list(worst_solution[0])
                    #shuffle(solution)
                    distance = calculate_tour_length(points, solution, node_count)
                    t = t_base
                    last_best_solutions = []
            '''

            k += 1
            if k == node_count*10:
                #print worst_solution
                #exit()
                t *= 0.5
                k = 0
                #solution = list(last_best_solutions[0][0])
                #distance = last_best_solutions[0][1]

        #return result[0], result[1]
        #solutions.append(solution)
        #distances.append(distance)
        i += 1
        #return solution, distance
    return best_solution, best_distance
'''
def two_opt_neighborhood_with_annealing(points, current_solution, node_count):
    # 2-opt implementation
    current_distance = calculate_tour_length(points, current_solution, node_count)
    tmp_solution, tmp_distance = current_solution, current_distance
    solution_improved = True
    t = 0
    i = 0

    while solution_improved == True:
        local_minima_found = False
        while local_minima_found == False:
            local_minima_found, solution_improved, tmp_solution, tmp_distance = \
                find_two_opt_solution_with_metropolis_meta_heuristic(node_count, current_solution, current_distance, points, t)
            if tmp_distance < current_distance:
                current_solution = tmp_solution
                current_distance = tmp_distance

            #i += 1
            #if i == 10:
            #    t /= 2
            #    i = 0

    return current_solution, current_distance
'''
def calculate_tour_length(points, solution, node_count):
    tour_length = length(points[solution[-1]], points[solution[0]])
    for index in range(0, node_count-1):
        tour_length += length(points[solution[index]], points[solution[index+1]])
    return tour_length

def find_two_opt_solution(node_count, current_solution, current_distance, points, improvement):
    for i in range(1, node_count-2):
        for k in range(i+1, node_count-1):
            new_solution = perform_two_opt_swap(current_solution, i, k)
            new_distance = calculate_tour_length(points, new_solution, node_count)
            improvement = current_distance - new_distance
            if new_distance < current_distance:
                current_solution = new_solution
                current_distance = new_distance
                return True, improvement, new_solution, new_distance
    return True, improvement, current_solution, current_distance

'''
The Metropolis meta-heuristics accepts bad moves on the probability
of exp(-d / t), where:

d = f(n) - f(s), being 's' the current solution and 'n' the new one;
t = temperature, a value to indicate how high is this probability.

'''
def find_two_opt_solution_with_metropolis_meta_heuristic(\
    node_count, current_solution, current_distance, points, t, visited_values):
    improvement = 0
    for i in range(1, node_count-2):
        for k in range(i+1, node_count-1):
            new_solution = perform_two_opt_swap(current_solution, i, k)
            new_distance = calculate_tour_length(points, new_solution, node_count)
            if not new_distance in visited_values:
                visited_values.append(new_distance)
                improvement = current_distance - new_distance
                if new_distance <= current_distance:
                    return True, improvement, new_solution, new_distance, False
                elif t > 0 and new_distance > current_distance:
                    rand = random()
                    delta = new_distance - current_distance
                    prob = math.exp(-delta / t)
                    if rand <= prob:
                        current_solution = new_solution
                        current_distance = new_distance
                        return True, improvement, new_solution, new_distance, True
                        #continue
    return True, improvement, current_solution, current_distance, False

def perform_two_opt_swap(current_solution, i, k):
    new_solution = current_solution[0:i]
    swap_part = current_solution[i:k+1]
    swap_part.reverse()
    new_solution.extend(swap_part)
    new_solution.extend(current_solution[k+1:])
    return new_solution

'''
TODO: implement List-Based Simulated Annealing algorithm (LBSA)
Reference: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4808530/
'''

import sys

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        with open(file_location, 'r') as input_data_file:
            input_data = input_data_file.read()
        print(solve_it(input_data))
    else:
        print('This test requires an input file.  Please select one from the data directory. (i.e. python solver.py ./data/tsp_51_1)')

