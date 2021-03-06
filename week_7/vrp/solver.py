#!../../../bin/python
# -*- coding: utf-8 -*-

import math
import networkx
import random
import itertools
from collections import namedtuple, OrderedDict
from pyscipopt import Model, quicksum, multidict, Conshdlr, SCIP_RESULT, SCIP_PRESOLTIMING, SCIP_PROPTIMING
from datetime import datetime

# from gurobipy import *

Customer = namedtuple("Customer", ['index', 'demand', 'x', 'y'])


def length(customer1, customer2):
    return math.sqrt((customer1.x - customer2.x) ** 2 + (customer1.y - customer2.y) ** 2)


def solve_it(input_data):
    # Modify this code to run your optimization algorithm

    # parse the input
    lines = input_data.split('\n')

    parts = lines[0].split()
    customer_count = int(parts[0])
    vehicle_count = int(parts[1])
    vehicle_capacity = int(parts[2])

    customers = []
    for i in range(1, customer_count + 1):
        line = lines[i]
        parts = line.split()
        customers.append(Customer(i - 1, int(parts[0]), float(parts[1]), float(parts[2])))

    # the depot is always the first customer in the input
    depot = customers[0]

    obj = None
    # obj, vehicle_tours = trivial_solver(customers, depot, vehicle_count, vehicle_capacity)
    # obj, vehicle_tours = gurobi_solver(customers, customer_count, vehicle_count, vehicle_capacity)
    if customer_count <= 20:
        obj, vehicle_tours = scip_solver_2(customers, customer_count, vehicle_count, vehicle_capacity)
    # obj, vehicle_tours = scip_solver_3(customers, customer_count, vehicle_count, vehicle_capacity)
    else:
        obj, vehicle_tours = scip_solver_4(customers, customer_count, vehicle_count, vehicle_capacity)

    if obj:
        # prepare the solution in the specified output format
        outputData = '%.2f' % obj + ' ' + str(0) + '\n'
        if len(vehicle_tours) > 0:
            for v in range(0, vehicle_count):
                outputData += str(depot.index) + ' ' + ' '.join(
                    [str(customer.index) for customer in vehicle_tours[v]]) + ' ' + str(depot.index) + '\n'

        return outputData

    return None


def trivial_solver(customers, depot, vehicle_count, vehicle_capacity):
    # build a trivial solution
    # assign customers to vehicles starting by the largest customer demands
    vehicle_tours = []

    remaining_customers = set(customers)
    remaining_customers.remove(depot)

    for v in range(0, vehicle_count):
        # print "Start Vehicle: ",v
        vehicle_tours.append([])
        capacity_remaining = vehicle_capacity
        while sum([capacity_remaining >= customer.demand for customer in remaining_customers]) > 0:
            used = set()
            order = sorted(remaining_customers, key=lambda customer: -customer.demand)
            for customer in order:
                if capacity_remaining >= customer.demand:
                    capacity_remaining -= customer.demand
                    vehicle_tours[v].append(customer)
                    # print '   add', ci, capacity_remaining
                    used.add(customer)
            remaining_customers -= used

    # checks that the number of customers served is correct
    assert sum([len(v) for v in vehicle_tours]) == len(customers) - 1

    # calculate the cost of the solution; for each vehicle the length of the route
    obj = 0
    for v in range(0, vehicle_count):
        vehicle_tour = vehicle_tours[v]
        if len(vehicle_tour) > 0:
            obj += length(depot, vehicle_tour[0])
            for i in range(0, len(vehicle_tour) - 1):
                obj += length(vehicle_tour[i], vehicle_tour[i + 1])
            obj += length(vehicle_tour[-1], depot)

    return obj, vehicle_tours


def gurobi_solver(customers, customer_count, vehicle_count, vehicle_capacity):
    c_range = range(0, customer_count)
    cd_range = range(1, customer_count)
    vehicles = range(0, vehicle_count)

    # Dictionary of Euclidean distance between each pair of points
    dist = {(i, j):
                length(customers[i], customers[j])
            for i in c_range for j in c_range}

    # Customer demands
    dem = {i: customers[i].demand for i in c_range}

    m = Model()
    m.modelSense = GRB.MINIMIZE

    # Variable that indicates if two nodes (customers) are connected
    arcs = [(i, j) for i in c_range for j in c_range if i != j]
    x_ij = m.addVars(arcs, vtype=GRB.BINARY, name='x', obj=dist)

    # Variable that represents if a node is visited by a vehicle
    v_ij = m.addVars(vehicles, arcs, vtype=GRB.BINARY, name='v')

    # Constraint: The number of nodes visited by a vehicle cannot exceed its capacity
    m.addConstrs(
        (quicksum(v_ij[v, i, j] * dem[j] for (i, j) in arcs) <= vehicle_capacity for v in vehicles)
    )

    # Constraint: Every vehicle must start and end in the depot position ("customer" 0)
    m.addConstrs(
        (v_ij.sum(v, 0, '*') == v_ij.sum(v, '*', 0) for v in vehicles)
    )
    m.addConstrs(
        (v_ij.sum(v, 0, '*') <= 1 for v in vehicles)
    )
    m.addConstrs(
        (v_ij.sum(v, 0, '*') >= (v_ij.sum(v, '*', '*')) / customer_count for v in vehicles)
    )
    m.addConstrs(
        (v_ij.sum(v, 0, '*') <= (v_ij.sum(v, '*', '*')) for v in vehicles)
    )

    # Constraint: A node (except the depot) has only be visited once and the flow must be conserved
    # 1 - A customer can only be followed by one other customer
    m.addConstrs(
        (x_ij.sum(i, '*') + x_ij.sum('*', i) == 2 for i in cd_range)
    )
    # 2 - A customer can only be connected by one other customer
    # m.addConstrs(
    #    (x_ij.sum('*', i) == 1 for i in cd_range)
    # )
    # 3 - An arc can only exist in a vehicle (or tour) if they are connected
    m.addConstrs(
        (v_ij.sum('*', i, j) == x_ij[i, j] for (i, j) in arcs)
    )
    # 4 - If a node (customer) is visited by a vehicle, it must happen in both directions
    m.addConstrs(
        (v_ij.sum(v, i, '*') == v_ij.sum(v, '*', i) for v in vehicles for i in c_range)
    )
    # 5 - Two customers cannot be connected in both directions (for example, (3, 4) and (4,3))
    m.addConstrs(
        (x_ij[i, j] + x_ij[j, i] <= 1 for i in cd_range for j in cd_range if i != j)
    )

    # 6 - A vehicle moved from a to b, it cannot move to a again, except if it is the depot
    # Ex.: if (2, 3) is true, ('*', 2) cannot happen
    m.addConstrs(
        (x_ij[i, j] + x_ij[j, i] <= 1 for i in cd_range for j in cd_range if i != j)
    )

    # 7 - A node cannot be connected to a node already connected to another one in the same tour (vehicle)
    # m.addConstrs(
    #    (x_ij[i, j] + x_ij[j, z] + x_ij[z, i] <= 2 for i in cd_range for j in cd_range for z in cd_range
    #        if i != j and i != z and j != z)
    # )

    # Objective: minimize the distance
    # m.setObjective(quicksum(x_ij[i, j] * dist[(i, j)] for (i, j) in arcs), GRB.MINIMIZE)

    m.optimize()

    obj = m.objVal
    output = [[]] * vehicle_count

    status = m.status
    if status == GRB.Status.INF_OR_UNBD or status == GRB.Status.INFEASIBLE \
            or status == GRB.Status.UNBOUNDED:
        print('The model cannot be solved because it is infeasible or \
                   unbounded: %s' % status)
        exit(1)

    if status != GRB.Status.OPTIMAL:
        print('Optimization was stopped with status %d' % status)
        exit(0)

    for (i, j) in arcs:
        print('(%s, %s) = %s' % (i, j, x_ij[i, j]))
    for v in vehicles:
        for (i, j) in arcs:
            print('%s: (%s, %s) = %s' % (v, i, j, v_ij[v, i, j]))

    w = 0
    for v in vehicles:
        output[w] = []
        has_nodes = False
        tour_complete = False
        last_arc_out = 0
        while True:
            for (i, j) in arcs:
                val = v_ij[v, i, j].X
                if val > 0:
                    if not has_nodes:
                        # output[w].append(customers[i])
                        output[w].append(customers[j])
                        last_arc_out = j
                        has_nodes = True
                    elif i == last_arc_out:
                        if j == 0:
                            tour_complete = True
                        else:
                            output[w].append(customers[j])
                            last_arc_out = j

                if tour_complete:
                    break

            if tour_complete:
                w += 1
                break

    print obj
    print output

    return obj, output


'''
def scip_solver(customers, customer_count, vehicle_count, vehicle_capacity):
    model = Model("vrp")

    c_range = range(0, customer_count)
    cd_range = range(1, customer_count)
    v_range = range(0, vehicle_count)

    x, d, w, v = {}, {}, {}, {}
    for i in c_range:
        for j in c_range:
            d[i, j] = length(customers[i], customers[j])
            if i != j:
                x[i, j] = model.addVar(vtype="B", name="x(%s, %s)" % (i, j))
            if j > i and i == 0:  # depot
                x[i, j] = model.addVar(ub=2, vtype="I", name="x(%s,%s)" % (i, j))
            elif j > i:
                x[i, j] = model.addVar(ub=1, vtype="I", name="x(%s,%s)" % (i, j))

    model.addCons(quicksum(x[0, j] for j in cd_range) <= 2 * vehicle_count, "DegreeDepot")

    for i in cd_range:
        model.addCons(quicksum(x[j, i] for j in c_range if j < i) +
                      quicksum(x[i, j] for j in c_range if j > i) == 2, "Degree(%s)" % i)

        model.addCons(quicksum(x[j, i] * w[j, i] for j in c_range if j < i) +
                      quicksum(x[i, j] * w[i, j] for j in c_range if j > i) <= 2*vehicle_capacity)

        #for j in c_range:
        #    if j > i:
        #        model.addCons(x[i, j] * w[i, j] <= vehicle_capacity)


    model.setObjective(quicksum(d[i, j] * x[i, j] for i in c_range for j in c_range if j > i), "minimize")

'''


# Source: https://github.com/SCIP-Interfaces/PySCIPOpt/blob/eb4792dbc05a443ab0263fbbf184011083710ba7/examples/unfinished/vrp.py
def scip_solver_2(customers, customer_count, vehicle_count, vehicle_capacity):
    model = Model("vrp")

    c_range = range(0, customer_count)
    cd_range = range(1, customer_count)

    x, d, w, v = {}, {}, {}, {}
    for i in c_range:
        for j in c_range:
            d[i, j] = length(customers[i], customers[j])
            w[i, j] = customers[i].demand + customers[j].demand
            if j > i and i == 0:  # depot
                x[i, j] = model.addVar(ub=2, vtype="I", name="x(%s,%s)" % (i, j))
            elif j > i:
                x[i, j] = model.addVar(ub=1, vtype="I", name="x(%s,%s)" % (i, j))

    model.addCons(quicksum(x[0, j] for j in cd_range) <= 2 * vehicle_count, "DegreeDepot")

    for i in cd_range:
        model.addCons(quicksum(x[j, i] for j in c_range if j < i) +
                      quicksum(x[i, j] for j in c_range if j > i) == 2, "Degree(%s)" % i)

        # model.addCons(quicksum(x[j, i] * w[j, i] for j in c_range if j < i) +
        #              quicksum(x[i, j] * w[i, j] for j in c_range if j > i) <= 2*vehicle_capacity)

        # for j in cd_range:
        #    for z in cd_range:
        #        if j > i and z > j:
        #            x[i, j] + x[j, z] + x[i, z] <= 2

        # for j in c_range:
        #    if j > i:
        #        model.addCons(x[i, j] * w[i, j] <= vehicle_capacity)

    model.setObjective(quicksum(d[i, j] * x[i, j] for i in c_range for j in c_range if j > i), "minimize")

    # model.hideOutput()

    # mip_gaps = [0.9, 0.5, 0.2, 0.03]
    mip_gaps = [0.0]
    runs = 0

    start = datetime.now()
    for gap in mip_gaps:
        model.freeTransform()
        model.setRealParam("limits/gap", gap)
        # model.setRealParam("limits/absgap", 0.3)
        model.setRealParam("limits/time", 60 * 20)  # Time limit in seconds
        # model.setIntParam('limits/bestsol', 1)

        edges, final_edges, runs = optimize(customer_count, customers, model, vehicle_capacity, vehicle_count, x)

    # model.setIntParam('limits/bestsol', -1)
    # model.freeTransform()
    # model.setRealParam("limits/gap", 0)
    # edges, final_edges = optimize(customer_count, customers, model, vehicle_capacity, vehicle_count, x)

    run_time = datetime.now() - start

    print edges
    print final_edges
    output = [[]] * vehicle_count
    for i in range(vehicle_count):
        output[i] = []
        current_item = None
        if len(final_edges) > 0:
            # Get the first edge starting with 0
            for e in final_edges:
                if e[0] == 0:
                    current_item = e
                    break
            if current_item:
                a = current_item[0]
                current_node = current_item[1]
                output[i].append(customers[current_node])
                final_edges.remove(current_item)
                searching_connections = True
                while searching_connections and len(final_edges) > 0:
                    for edge in final_edges:
                        found_connection = False
                        a_edge = edge[0]
                        b_edge = edge[1]

                        # If we find the node connecting with a 0
                        # it means the cycle has been closed
                        if b_edge == current_node and a_edge == 0:
                            final_edges.remove(edge)
                            break

                        if a_edge == current_node:
                            output[i].append(customers[b_edge])
                            current_node = b_edge
                            found_connection = True
                        elif b_edge == current_node:
                            output[i].append(customers[a_edge])
                            current_node = a_edge
                            found_connection = True

                        if found_connection:
                            final_edges.remove(edge)
                            break

                    if not found_connection:
                        searching_connections = False

    print output

    sol = model.getBestSol()
    obj = model.getSolObjVal(sol)

    print("RUN TIME: %s" % str(run_time))
    print("NUMBER OF OPTIMIZATION RUNS: %s" % runs)

    return obj, output


def addcut(cut_edges, model, customers, vehicle_capacity, x):
    """addcut: add constraint to eliminate infeasible solutions
    """
    G = networkx.Graph()
    G.add_edges_from(cut_edges)
    Components = networkx.connected_components(G)
    cut = False
    model.freeTransform()
    for S in Components:
        S_card = len(S)
        q_sum = sum(customers[i].demand for i in S)
        NS = int(math.ceil(float(q_sum) / vehicle_capacity))
        S_edges = [(i, j) for i in S for j in S if i < j and (i, j) in cut_edges]
        if S_card >= 3 and (len(S_edges) >= S_card or NS > 1):
            # if (len(S_edges) >= S_card or NS > 1):
            model.addCons(quicksum(x[i, j] for i in S for j in S if j > i) <= S_card - NS)
            # model.addCons(quicksum(x[i, j] * (customers[i].demand + customers[j].demand)
            #                                  for (i, j) in cut_edges) <= 2*vehicle_capacity)
            cut = True
    return cut


def optimize(customer_count, customers, model, vehicle_capacity, vehicle_count, x, cut=True):
    EPS = 1.e-6
    runs = 0
    while True:
        print("Solving problem with %s customers and %s vehicles..." % (customer_count, vehicle_count))
        model.optimize()
        runs += 1
        sol = model.getBestSol()
        final_edges = []
        edges = []
        for (i, j) in x:
            val = model.getSolVal(sol, x[i, j])
            if val > EPS:
                if i != 0 and j != 0:
                    edges.append((i, j))
                final_edges.append((i, j))

        if not cut:
            break

        if not addcut(edges, model, customers, vehicle_capacity, x):
            break
    return edges, final_edges, runs


'''
#Source: https://scholarworks.waldenu.edu/cgi/viewcontent.cgi?article=1020&context=ijamt
'''


def scip_solver_3(customers, customer_count, vehicle_count, vehicle_capacity):
    """
    #### Notations #### 
    G = Symmetric Graph; G= (T, A) 
    T = Set of Nodes; T = [N ∪ {0, n+1}] 
    A = Set of Arcs linking any pair of nodes, (i.j) ∈ A
    V = Total Number of Vehicles; v = {1,2...V} 
    y[i,j] = Cost of travel from node i to node j 
    d[i] = Delivery requests of node i, i = 1, ..., N
    p[i] = Pickup requests of node i, i = 1, ..., N (NOT TO BE USED IN THIS PROBLEM)
    Q = Capacity of Vehicle 
    TL = Maximum Route Length for any Vehicle v

    #### Decision Variables #### 
    D[i,v] = The load remaining to be delivered by vehicle v when departing from node i
    P[i,v] = The cumulative load picked by vehicle v when departing from node i (NOT TO BE USED IN THIS PROBLEM)
    X[v,i,j] = 1 if vehicle travels from i to j, 0 otherwise

    P[i], d[i], Q, y[i,j] are non-negative integers 

    """

    model = Model("vrp")
    # model.hideOutput()
    model.setMinimize()

    model.setRealParam("limits/gap", 0.03)
    model.setRealParam("limits/absgap", 0.03)
    model.setRealParam("limits/time", 600)  # Time limit in seconds

    T = customers
    V = vehicle_count
    Q = vehicle_capacity
    A = range(0, customer_count)
    Am = range(1, customer_count)
    Vr = range(0, vehicle_count)

    y, d, D, X = {}, {}, {}, {}
    for i in A:
        d[i] = customers[i].demand
        for j in A:
            y[i, j] = length(customers[i], customers[j])
            for v in Vr:
                X[v, i, j] = model.addVar(vtype="B", name="X(%s,%s,%s)" % (v, i, j))
        for v in Vr:
            D[i, v] = model.addVar(lb=0, ub=Q, vtype="I", name="D(%s,%s)" % (i, v))

    """
    Lower Bound for Number of Vehicles
    """
    l = int(sum(d[i] for i in Am) / Q)
    for v in Vr:
        # Constraint: the total delivery load for a route is placed on the vehicle v,
        #             embarking on each trip, at the starting node itself
        # model.addCons(D[0,v] >= quicksum(X[v,i,j]*d[i] for i in Am for j in Am), "c12(%s)" % v)
        model.addCons(D[0, v] == Q, "c12(%s)" % v)

        for i in Am:
            # Constraint: the load on vehicle v, when departing from node i, is always lower than the vehicle capacity
            model.addCons(D[i, v] <= Q, "c11(%s,%s)" % (i, v))
            model.addCons(D[i, v] >= 0, "c17(%s,%s)" % (i, v))

    for j in A:
        if j > 0:
            # Constraint: each node must be visited exactly once
            model.addCons(quicksum(X[v, i, j] for v in Vr for i in A) == 1, "c8(%s)" % (j))
        for v in Vr:
            # Constraint: the same vehicle arrives and departs from each node it serves
            model.addCons(quicksum(X[v, i, j] for i in A) - quicksum(X[v, j, i] for i in A) == 0, "c10(%s,%s)" % (j, v))

    for i in A:
        for j in Am:
            for v in Vr:
                # Constraint: transit load constraints i.e., if arc (i, j) is visited by the vehicle v, then the
                # quantity to be delivered by the vehicle has to decrease by d j
                model.addCons((D[i, v] - d[j] - D[j, v]) * X[v, i, j] == 0, "c14(%s,%s,%s)" % (i, j, v))

    # Constraint: the number of vehicles used should be, at least, the calculated lower bound
    # model.addCons(quicksum(X[v,0,j] for v in Vr for j in Am) >= l, "cBound")

    # Objective function: minimize the total cost of travel
    model.setObjective(quicksum(y[i, j] * X[v, i, j] for i in A for j in A for v in Vr), "minimize")

    model.optimize()
    best_sol = model.getBestSol()
    vehicle_tours = []

    for v in Vr:
        for i in A:
            for j in A:
                print "X[%s,%s,%s]: %s" % (v, i, j, model.getSolVal(best_sol, X[v, i, j]))

    found_conn = 0
    visited_nodes = []
    for v in Vr:
        found_conn = 0
        vehicle_tours.append([])
        for i in A:
            if i == found_conn:
                found_conn = 0
                for j in Am:
                    if not j in visited_nodes:
                        current_val = model.getSolVal(best_sol, X[v, i, j])
                        if current_val >= 0.9:
                            if j > 0:
                                vehicle_tours[v].append(customers[j])
                                visited_nodes.append(j)
                            found_conn = j
                            break
                        if found_conn > 0:
                            break
    print(vehicle_tours)

    obj = model.getSolObjVal(best_sol)

    return obj, vehicle_tours


"""
This solution takes into consideration the approach proposed by Fisher and Kaikumar.
http://neo.lcc.uma.es/vrp/solution-methods/heuristics/cluster-first-route-second-method/
https://apps.dtic.mil/dtic/tr/fulltext/u2/a100992.pdf

The idea is to first cluster the best possible customers for each vehicle,
then resolve a GAP (general assignment problem) on it.
After that, apply the TSP optimization on each one of the vehicles.
"""
def scip_solver_4(customers, customer_count, vehicle_count, vehicle_capacity):
    # Setting up basic variables
    K = vehicle_count
    n = customer_count
    b = vehicle_capacity
    a = {}  # the demand for customer i
    c = {}  # the distance between customer i and j

    for i, x in enumerate(customers):
        a[i] = x.demand

        for j, y in enumerate(customers):
            # if i != j:
            c[(i, j)] = length(x, y)

    best_obj = 99999999
    best_tours = []

    ### VEHICLE CAPACITY SUB-PROBLEM ###
    obj, vehicle_tours = vehicle_assignment_solver(K, a, b, c, customer_count)

    ### TSP ON VEHICLES SUB-PROBLEM ###
    final_obj, final_tours = tsp_solver(c, customers, vehicle_tours)

    if final_obj < best_obj and len([item for elem in final_tours for item in elem]) == n - 1:
        best_obj = final_obj
        best_tours = final_tours
        print("Best solution found: %s" % best_obj)

    print("Best objective cost: %s" % best_obj)

    return best_obj, best_tours


def tsp_solver(c, customers, vehicle_tours):
    def addcut(cut_edges):
        G = networkx.Graph()
        G.add_edges_from(cut_edges)
        Components = list(networkx.connected_components(G))
        if len(Components) == 1:
            return False
        model.freeTransform()
        for S in Components:
            model.addCons(quicksum(x[i, j] for i in S for j in S) <= len(S) - 1)

        return True

    # Add the depot on each vehicle
    vehicle_tours = {k: vehicle_tours[k] + [0] for k in vehicle_tours.keys()}
    final_obj = 0
    final_tours = []
    for key, value in vehicle_tours.iteritems():
        v_customers = value
        model = Model("vrp_tsp")
        #model.hideOutput()
        x = {}

        for i in v_customers:
            for j in v_customers:
                # vehicle moves from customer i to customer j
                x[i, j] = model.addVar(vtype="B", name="x(%s,%s)" % (i, j))

        for i in v_customers:
            # Constraint: every customer can only be visited once
            # (or, every node must be connected and connect to another node)
            model.addCons(quicksum(x[i, j] for j in v_customers) == 1)
            model.addCons(quicksum(x[j, i] for j in v_customers) == 1)

            for j in v_customers:
                if i == j:
                    # Constraint: a node cannot conect to itself
                    model.addCons(x[i, j] == 0)

        # Objective function: minimize total distance of the tour
        model.setObjective(quicksum(x[i, j] * c[(i, j)] for i in v_customers for j in v_customers), "minimize")

        EPS = 1.e-6
        isMIP = False
        while True:
            model.optimize()
            edges = []
            for (i, j) in x:
                if model.getVal(x[i, j]) > EPS:
                    edges.append((i, j))

            if addcut(edges) == False:
                if isMIP:  # integer variables, components connected: solution found
                    break
                model.freeTransform()
                for (i, j) in x:  # all components connected, switch to integer model
                    model.chgVarType(x[i, j], "B")
                    isMIP = True

        # model.optimize()
        best_sol = model.getBestSol()
        sub_tour = []

        # Build the graph path
        # Retrieve the last node of the graph, i.e., the last one connecting to the depot
        last_node = [n for n in edges if n[1] == 0][0][0]
        G = networkx.Graph()
        G.add_edges_from(edges)
        path = list(networkx.all_simple_paths(G, source=0, target=last_node))
        path.sort(reverse=True, key=lambda u: len(u))

        if len(path) > 0:
            path = path[0][1:]
        else:
            path = path[1:]

        obj = model.getSolObjVal(best_sol)
        final_obj += obj
        final_tours.append([customers[i] for i in path])

        # print("Customers visited by vehicle %s: %s" % (key, value))
        # print("Objective cost for vehicle %s: %s" % (key, obj))
        # print("Edges visited by vehicle %s: %s" % (key, edges))
        # print("Path visited by vehicle %s: %s" % (key, path))
    return final_obj, final_tours


def vehicle_assignment_solver(K, a, b, c, customer_count, predefined_vehicle_index=None, predefined_vehicle_nodes=None):
    v_range = range(0, K)
    c_range = range(1, customer_count)
    samples = []

    # First we set the K seeds to use on the clustering
    # Dummy method: order by the customer demand and put the first one in one of the vehicles
    # For the remaining K-1 vehicles, choose the nodes most distance from each other
    a_ord = sorted(a.items(), key=lambda k: k[1])
    a_ord.reverse()
    samples.append(a_ord[0])
    del a_ord[0]

    while True:
        a_ord = sorted(a_ord, key=lambda el: dist_between_nodes(el, samples, c), reverse=True)
        samples.append(a_ord[0])
        del a_ord[0]

        if len(samples) == K:
            break

    w = {}
    for i in v_range:
        w[i] = samples[i][0]

    # else:
    # Dummy method: just get random items
    # sample = random.sample(c_range, current_num_v)
    # if sample in generated_samples:
    #    print("Sample already used. Generating a new one...")
    #    sample = random.sample(c_range, K)

    # generated_samples.append(sample)

    # Resolve MIP problem to find the best possible vehicle-customers combinations
    model = Model("vrp_vehicles")
    #model.hideOutput()

    if customer_count >= 200:
        model.setRealParam("limits/gap", 0.005)


    y = {}
    for v in v_range:
        for i in c_range:
            # customer i is visited by vehicle v
            y[i, v] = model.addVar(vtype="B", name="y(%s,%s)" % (i, v))
    for v in v_range:
        # Constraint: the demand of customers assigned to vehicle V cannot exceed its capacity
        model.addCons(quicksum(a[i] * y[i, v] for i in c_range) <= b)

        # Constraint: for this model, we enforce every vehicle to visit a customer
        # model.addCons(quicksum(y[i, v] for i in c_range) >= 1)

        # Constraint: we enforce the customers on 'w' to be visited by the defined vehicle
        #model.addCons(y[w[v], v] == 1)

        #if predefined_vehicle_nodes and v == predefined_vehicle_index:
        #    for p in predefined_vehicle_nodes:
        #        model.addCons(y[p, predefined_vehicle_index] == 1)

    for i in c_range:
        # if i > 0:
        # Constraint: each customer has to be visited by exactly one vehicle
        model.addCons(quicksum(y[i, v] for v in v_range) == 1)

    model.setObjective(quicksum(quicksum(cost_of_new_customer_in_vehicle(c, i, w[v])*y[i, v]
                                         for i in c_range) for v in v_range), "maximize")

    #model.setObjective(quicksum(
    #    quicksum((c[(i, j)] * y[i, v]) + (c[(i, j)] * y[j, v]) for i in c_range for j in c_range if i != j) for v in
    #    v_range), "minimize")

    model.optimize()
    # best_sol = model.getBestSol()
    vehicle_tours = {}
    for v in v_range:
        vehicle_tours[v] = []
        for i in c_range:
            # val = model.getSolVal(best_sol, y[i, v])
            val = model.getVal(y[i, v])
            if val > 0.5:
                vehicle_tours[v].append(i)
    # obj = model.getSolObjVal(best_sol)
    obj = model.getObjVal()
    # print(obj)
    # print(vehicle_tours)
    return obj, vehicle_tours


def dist_between_nodes(node_to_check, nodes, c):
    """
    Checks the total distance between one node and a list of other nodes
    :param nodes: list of nodes to compare
    :param node_to_check: the node that will be compared to the other ones
    :return: the sum of distances
    """
    sum = 0
    for node in nodes:
        sum += c[(node_to_check[0], node[0])]

    return sum


def cost_of_new_customer_in_vehicle(c, i, w):
    return min(c[(0, i)] + c[(i, w)] + c[(w, 0)], c[(0, w)] + c[(w, i)] + c[(i, 0)]) - (c[(0, w)] + c[w, 0])


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        with open(file_location, 'r') as input_data_file:
            input_data = input_data_file.read()
        print(solve_it(input_data))
    else:

        print(
            'This test requires an input file.  Please select one from the data directory. (i.e. python solver.py ./data/vrp_5_4_1)')
