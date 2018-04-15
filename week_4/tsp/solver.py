#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
from collections import namedtuple
from random import shuffle
from random import random
from pyscipopt import Model, quicksum, multidict
import time
import networkx

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
    #final_solution, obj = meta_heuristic_annealing(points, solution, obj, nodeCount)

    #obj, final_solution = scip_solver(points)
    obj, final_solution = scip_solver_2(points)

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

'''
MIP using PySCIPOpt.
References:
https://github.com/SCIP-Interfaces/PySCIPOpt
http://scip.zib.de/
'''
def scip_solver(nodes):
    model = Model("tsp")
    #model.hideOutput()
    model.setMinimize()    
    model.setRealParam("limits/gap", 0.1)
    model.setRealParam("limits/time", 3600*12)

    n_c = len(nodes)
    n_range = range(0, n_c)

    x, c, u = {}, {}, {}
    for i in n_range:
        u[i] = model.addVar(lb=0, ub=n_c-1, vtype="C", name="u(%s)"%i)
        for j in n_range:
            if j != i:
                x[i,j] = model.addVar(vtype="B", name="x(%s,%s)"%(i,j))
                c[i,j] = city_dist(nodes[i], nodes[j])

    for i in n_range:
        #model.addCons(quicksum(x[j,i] for j in n_range if j < i) + \
        #                quicksum(x[i,j] for j in n_range if j > i) == 2, "Degree(%s)"%i)
        #model.addCons(quicksum(x[i,j] for j in n_range if j > i) == 1, "Uniq(%s)"%i)
        model.addCons(quicksum(x[i,j] for j in n_range if j != i) == 1, "Out(%s)"%i)
        model.addCons(quicksum(x[j,i] for j in n_range if j != i) == 1, "In(%s)"%i)
        
    for i in range(0,n_c):
        for j in range(1,n_c):
            if i < j:
                model.addCons((x[j,i] + x[i,j]) <= 1, "Perm(%s,%s)"%(i,j))

    for i in range(0,n_c):
        for j in range(1,n_c):
            if i != j:
                model.addCons(u[i] - u[j] + (n_c-1)*x[i,j] <= n_c-2, "MTZ(%s,%s)"%(i,j))

    # for i in range(1,n_c):
    #     model.addCons(-x[0,i] - u[i] + (n_c-3)*x[i,0] <= -2, name="LiftedLB(%s)"%i)
    #     model.addCons(-x[i,0] + u[i] + (n_c-3)*x[0,i] <= n_c-2, name="LiftedUB(%s)"%i)

    model.setObjective(quicksum(c[i,j]*x[i,j] for (i, j) in x), "minimize")

    model.data = x, u
    print "start"
    model.optimize()
    # sols = model.getSols()

    # best_sol = sols[0]
    # print model.getObjVal(best_sol)
    # for i in range(1, len(sols)):
    #     current_obj = model.getObjVal(sols[i])
    #     print current_obj
    #     if current_obj < model.getObjVal(best_sol):
    #         best_sol = sols[i]

    #for (i,j) in x:
    #    if model.getVal(x[i,j]) == 1:
    #        print "x[%s,%s] = %s" % (i,j,model.getVal(x[i,j]))

    #x, u = model.data
    sol = []
    i = 0
    sol.append(i)
    while len(sol) < len(nodes):
        for j in n_range:
            if i != j and model.getVal(x[i,j]) == 1:
                sol.append(j)
                i = j
                break

    #i = 0
    #sol.append(i)
    # while len(sol) < len(nodes):
    #     for j in n_range:
    #         if j != i and not j in sol:
    #             current_val = model.getVal(x[i,j])
    #             if current_val == 1:
    #                 sol.append(j)
    #                 i = j
    #                 break

    obj = model.getObjVal()
    return obj, sol

'''
Another MIP modelling, with cutting edges techniques
applied with SCIP.

Algorithm reference:
https://github.com/SCIP-Interfaces/PySCIPOpt/blob/master/examples/finished/tsp.py
'''
def scip_solver_2(nodes):

    def addcut(cut_edges):
        G = networkx.Graph()
        G.add_edges_from(cut_edges)
        Components = list(networkx.connected_components(G))
        if len(Components) == 1:
            return False
        model.freeTransform()
        for S in Components:
            model.addCons(quicksum(x[i,j] for i in S for j in S if j>i) <= len(S)-1)
            #print("cut: len(%s) <= %s" % (S,len(S)-1))
        return True


    model = Model("tsp")
    model.hideOutput()
    
    n_c = len(nodes)
    n_range = range(0, n_c)

    x, c, u = {}, {}, {}
    for i in n_range:
        for j in n_range:
            if j > i:
                c[i,j] = city_dist(nodes[i], nodes[j])
                x[i,j] = model.addVar(ub=1, name="x(%s,%s)"%(i,j))

    for i in n_range:
        model.addCons(quicksum(x[j,i] for j in n_range if j < i) + \
                        quicksum(x[i,j] for j in n_range if j > i) == 2, "Degree(%s)"%i)

    model.setObjective(quicksum(c[i,j]*x[i,j] for i in n_range for j in n_range if j > i), "minimize")

    EPS = 1.e-6
    isMIP = False
    while True:
        model.optimize()
        edges = []
        for (i,j) in x:
            if model.getVal(x[i,j]) > EPS:
                edges.append( (i,j) )

        if addcut(edges) == False:
            if isMIP:     # integer variables, components connected: solution found
                break
            model.freeTransform()
            for (i,j) in x:     # all components connected, switch to integer model
                model.chgVarType(x[i,j], "B")
                isMIP = True

    obj = model.getObjVal()

    #print obj
    #print edges

    tour = []
    current_vertice = edges[0][1]
    tour.append(edges[0][0])
    tour.append(current_vertice)
    edges.remove(edges[0])
    while len(tour) < len(nodes):
        for edge in edges:
            if current_vertice in edge:
                for v in edge:
                    if v != current_vertice:
                        tour.append(v)
                        current_vertice = v
                        edges.remove(edge)
                        break

    #print tour

    return obj, tour

def city_dist(point1, point2):
    x_dist = math.pow(point1.x - point2.x, 2)
    y_dist = math.pow(point1.y - point2.y, 2)
    return math.sqrt(x_dist + y_dist)

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

'''
Outputs:

428.87 0
26 47 33 0 5 2 28 10 9 45 3 27 41 24 46 8 4 34 23 35 13 7 19 40 18 16 44 14 15 38 50 39 49 17 32 48 22 31 1 25 20 37 21 43 29 42 11 30 12 36 6

20750.76 0
54 92 5 20 87 88 77 37 47 7 83 39 74 66 57 71 24 55 3 51 84 17 79 26 29 14 80 96 16 4 91 69 13 28 62 64 76 34 50 2 89 61 98 67 78 95 73 81 10 75 56 31 27 58 86 65 0 12 93 15 97 33 60 1 36 45 46 30 94 82 49 23 6 85 63 59 41 68 48 42 53 9 18 52 22 8 90 38 70 72 19 25 40 43 44 99 11 32 21 35

29440.41 0
47 143 1 99 29 34 61 195 36 118 50 191 18 135 144 117 123 52 59 43 154 3 92 121 122 187 70 42 76 53 90 38 72 14 153 62 15 151 157 183 106 68 171 136 83 40 146 78 180 12 178 87 164 23 26 179 119 137 51 7 65 37 185 148 33 80 129 174 168 49 0 155 199 125 161 93 31 104 96 166 97 169 48 152 69 138 139 16 89 88 10 167 109 22 41 172 184 21 192 110 102 57 127 28 190 196 175 198 107 128 35 158 74 66 131 6 170 60 111 73 197 194 100 189 120 45 145 124 108 133 156 193 79 75 126 160 134 71 56 30 77 98 44 165 32 67 13 186 64 173 159 85 95 188 142 63 149 58 84 17 5 39 82 2 176 4 115 101 8 9 141 19 24 113 163 181 20 46 132 81 182 103 105 114 11 27 150 55 94 147 130 162 25 86 112 54 177 116 91 140

36934.77 0
155 159 156 153 157 158 145 144 143 142 146 147 148 152 149 150 151 141 140 139 138 137 136 135 134 133 132 131 130 129 128 127 126 125 124 69 70 68 67 66 65 72 71 123 122 121 120 118 119 73 74 75 76 64 62 63 61 60 59 81 80 79 78 77 88 89 94 97 95 96 98 99 100 102 101 551 550 559 558 557 556 552 553 554 555 91 92 93 90 87 86 85 84 51 50 52 53 83 82 57 58 56 55 54 49 48 47 46 45 44 43 42 39 41 40 38 37 36 35 34 33 32 30 31 29 28 27 26 25 24 22 23 12 13 21 20 19 18 17 16 15 14 11 10 9 8 7 6 5 4 3 2 1 0 573 572 571 466 467 468 469 470 471 472 473 474 570 569 568 567 566 565 564 563 562 561 560 549 548 478 477 479 480 476 475 482 481 483 536 484 485 486 487 535 534 488 489 490 529 528 527 512 511 510 509 513 514 515 516 517 520 521 522 523 526 491 492 493 525 524 494 495 518 519 497 496 465 464 463 462 461 460 459 458 457 456 455 454 439 443 444 445 442 446 447 448 449 450 441 440 453 452 499 500 501 498 502 503 504 505 506 507 508 302 301 303 304 306 319 320 321 317 318 305 307 308 309 310 311 451 312 313 316 314 315 374 375 376 377 378 379 380 381 390 389 388 391 392 393 394 395 396 371 372 373 322 323 324 325 326 327 328 329 366 342 365 367 368 369 370 398 397 399 400 404 405 406 407 408 409 384 383 385 387 386 382 431 433 434 435 436 438 437 432 430 429 428 427 426 425 424 423 422 421 420 419 417 418 410 411 412 356 402 403 401 360 359 358 357 355 354 353 352 413 414 416 415 351 350 349 348 347 362 361 363 364 346 345 344 343 341 340 330 331 332 333 339 338 337 336 335 334 283 284 285 286 287 280 281 282 279 278 277 276 288 289 290 291 292 275 274 273 272 271 267 268 269 270 293 294 295 296 297 298 266 265 264 263 262 261 260 259 258 299 300 257 256 255 253 254 252 251 250 249 248 241 242 243 244 245 247 246 238 239 240 237 236 235 234 232 233 530 531 532 533 231 230 229 228 227 189 225 226 190 191 192 193 219 218 220 221 222 224 223 217 216 215 214 213 212 211 210 209 205 206 207 208 203 204 202 201 200 199 198 197 196 195 194 184 185 183 182 186 188 187 538 537 539 540 176 177 178 179 181 180 169 171 170 172 175 174 173 108 109 107 542 541 543 544 545 546 547 103 104 105 106 117 116 115 114 110 111 112 113 161 160 162 168 163 167 166 164 165 154
'''
