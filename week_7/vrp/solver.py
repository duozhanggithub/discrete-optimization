<<<<<<< HEAD
#!../../../bin/python
=======
#!/usr/bin/python
>>>>>>> 302717814fa2618fc99a8acd8b9dd50a967d2efa
# -*- coding: utf-8 -*-

import math
import networkx
from collections import namedtuple
from pyscipopt import Model, quicksum, multidict

Customer = namedtuple("Customer", ['index', 'demand', 'x', 'y'])

def length(customer1, customer2):
    return math.sqrt((customer1.x - customer2.x)**2 + (customer1.y - customer2.y)**2)

def solve_it(input_data):
    # Modify this code to run your optimization algorithm

    # parse the input
    lines = input_data.split('\n')

    parts = lines[0].split()
    customer_count = int(parts[0])
    vehicle_count = int(parts[1])
    vehicle_capacity = int(parts[2])
    
    customers = []
    for i in range(1, customer_count+1):
        line = lines[i]
        parts = line.split()
        customers.append(Customer(i-1, int(parts[0]), float(parts[1]), float(parts[2])))

    #the depot is always the first customer in the input
    depot = customers[0]
    
<<<<<<< HEAD
    try:
        #obj, vehicle_tours = trivial_solver(customers, depot, vehicle_count, vehicle_capacity)
        #obj, vehicle_tours = scip_solver(customers, customer_count, vehicle_count, vehicle_capacity)
        #obj, vehicle_tours = scip_solver_2(customers, customer_count, vehicle_count, vehicle_capacity)
        obj, vehicle_tours = scip_solver_3(customers, customer_count, vehicle_count, vehicle_capacity)
    except Exception as e:
        print(e)
=======
    #obj, vehicle_tours = trivial_solver(customers, depot, vehicle_count, vehicle_capacity)
    #obj, vehicle_tours = scip_solver(customers, customer_count, vehicle_count, vehicle_capacity)
    #obj, vehicle_tours = scip_solver_2(customers, customer_count, vehicle_count, vehicle_capacity)
    obj, vehicle_tours = scip_solver_3(customers, customer_count, vehicle_count, vehicle_capacity)
>>>>>>> 302717814fa2618fc99a8acd8b9dd50a967d2efa
    
    # prepare the solution in the specified output format
    outputData = '%.2f' % obj + ' ' + str(0) + '\n'
    if len(vehicle_tours) > 0:
        for v in range(0, vehicle_count):
            outputData += str(depot.index) + ' ' + ' '.join([str(customer.index) for customer in vehicle_tours[v]]) + ' ' + str(depot.index) + '\n'

    return outputData

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
            obj += length(depot,vehicle_tour[0])
            for i in range(0, len(vehicle_tour)-1):
                obj += length(vehicle_tour[i],vehicle_tour[i+1])
            obj += length(vehicle_tour[-1],depot)

    return obj, vehicle_tours

def scip_solver(customers, customer_count, vehicle_count, vehicle_capacity):
    model = Model("vrp")
    #model.hideOutput()
    model.setMinimize()

    c_range = range(0, customer_count)
    cd_range = range(1, customer_count)
    v_range = range(0, vehicle_count)

    x, c, d = {}, {}, {}
    for i in v_range:
        for j in c_range:
            # Variable: vehicle i visits customer j
            #x[i,j] = model.addVar(vtype="B", name="x(%s,%s)" % (i,j))
       
    #for i in v_range:
        #for j in c_range:
            for k in c_range:
                d[j,k] = length(customers[j], customers[k])
                if k > j and j == 0:
                    # Variable: customer j is connected to customer k
                    c[j,k] = model.addVar(ub=2, vtype="I", name="c(%s,%s)" % (j,k))
                elif k > j:
	            c[j,k] = model.addVar(ub=1, vtype="I", name="c(%s,%s)" % (j,k))
        # Constraint: the number of costumers visited by each vehicle cannot exceed its capacity
	#model.addCons(quicksum(x[i,j]*customers[j].demand for j in c_range) <= vehicle_capacity, "cap(%s)" % i)
    
    model.addCons(quicksum(c[0,k] for k in cd_range) == 2*vehicle_count, "DepotDegree")
    
    #for i in v_range:
        # Constraint: the number of costumers visited by each vehicle cannot exceed its capacity
	#model.addCons(quicksum(x[i,j]*customers[j].demand for j in c_range) <= vehicle_capacity, "cap(%s)" % i)
        
        # Constraint: every vehicle must visit the first customer (depot)
        #model.addCons(x[i,0] > 0, "dep(%s)" % i)
    
    for j in cd_range:
        # Constraint: every customer has to be visited by exactly one vehicle
        #model.addCons(quicksum(x[i,j] for i in v_range) == 1, "visit(%s)" % j)

        # Constraint: each customer has to have two connections
        model.addCons(quicksum(c[k,j] for k in c_range if k < j) + \
            quicksum(c[j,k] for k in c_range if k > j) == 2, "Degree(%s)"%j)
        
    '''
    for i in v_range:
        for j in c_range:   
             for k in c_range:
                if k > j and j > 0:
                    # Constraint: if a vehicle visits two customers, they must be connected
                    model.addCons(x[i,j]*x[i,k] == c[j,k], "rel(%s, %s, %s)" %(i,j,k))
    '''    

    # Minimize: sum0..X(vehicleX(dist(depot, firstCustomer) + sum(dist(customerN, customerK)) + dist(lastCustomer, depot)))
    model.setObjective(quicksum(d[j,k]*c[j,k] for j in c_range for k in c_range if k > j), "minimize")

    for (j,k) in d:
        print "(%s,%s): %s" % (j,k,d[j,k])

    #model.data = x, c
    model.optimize()
    #best_sol = model.getBestSol()
    vehicle_tours = []
    added_indexes = []
    i = 0
    for j in cd_range:
        vehicle_tours.append([])
        #current_val = model.getSolVal(best_sol, c[0,j])
        current_val = model.getVal(c[0,j])
        if current_val > 0 and not j in added_indexes:
            vehicle_tours[i].append(customers[j])
            added_indexes.append(j)
            for k in cd_range:
                if k > j:
                    #current_val = model.getSolVal(best_sol, c[j,k])
                    current_val = model.getVal(c[j,k])
                    if current_val > 0 and not k in added_indexes:
                        vehicle_tours[i].append(customers[k])
                        added_indexes.append(k)
                    elif k < j:
                        #current_val = model.getSolVal(best_sol, c[k,j])
                        current_val = model.getVal(c[k,j])
                        if current_val > 0 and not k in added_indexes:
                            vehicle_tours[i].append(customers[k])
                            added_indexes.append(k)
        i =+ 1
    
    print vehicle_tours
    
    for (j,k) in c:
        #print("c(%s,%s): %s" % (j,k,model.getSolVal(best_sol, c[j,k])))
        print("c(%s,%s): %s" % (j,k,model.getVal(c[j,k])))

    '''
    for (i,j) in x:
        print("x(%s,%s): %s" %(i,j,model.getSolVal(best_sol, x[i,j])))
    '''
    '''
    for i in v_range:
        vehicle_tours.append([])
        for j in c_range:
            current_val = model.getSolVal(best_sol, c[i,j])
            print current_val
            if current_val >= 0.9:
                vehicle_tours[i].append(customers[j])
                break
    print(vehicle_tours)
    '''

    #obj = model.getSolObjVal(best_sol)
    obj = model.getObjVal()

    return obj, vehicle_tours

'''
Source: https://github.com/SCIP-Interfaces/PySCIPOpt/blob/eb4792dbc05a443ab0263fbbf184011083710ba7/examples/unfinished/vrp.py
'''
def scip_solver_2(customers, customer_count, vehicle_count, vehicle_capacity):
    def addcut(cut_edges):
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
            NS = int(math.ceil(float(q_sum)/vehicle_capacity))
            S_edges = [(i,j) for i in S for j in S if i<j and (i,j) in cut_edges]
            if S_card >= 3 and (len(S_edges) >= S_card or NS > 1):
                add = model.addCons(quicksum(x[i,j] for i in S for j in S if j > i) <= S_card-NS)
                cut = True
        return cut

    model = Model("vrp")

    c_range = range(0, customer_count)
    cd_range = range(1, customer_count)
    v_range = range(0, vehicle_count)
    
    x, d = {}, {}
    for i in c_range:
        for j in c_range:
            d[i,j] = length(customers[i], customers[j])
            if j > i and i == 0:       # depot
                x[i,j] = model.addVar(ub=2, vtype="I", name="x(%s,%s)"%(i,j))
            elif j > i:
                x[i,j] = model.addVar(ub=1, vtype="I", name="x(%s,%s)"%(i,j))
    
    model.addCons(quicksum(x[0,j] for j in cd_range) == 2*vehicle_count, "DegreeDepot")
    for i in cd_range:
        model.addCons(quicksum(x[j,i] for j in c_range if j < i) +
                        quicksum(x[i,j] for j in c_range if j > i) == 2, "Degree(%s)"%i)

    model.setObjective(quicksum(d[i,j]*x[i,j] for i in c_range for j in c_range if j>i), "minimize")

    model.hideOutput()

    EPS = 1.e-6
    while True:
        model.optimize()
        edges = []
        for (i,j) in x:
            if model.getVal(x[i,j]) > EPS:
                if i != 0 and j != 0:
                    edges.append((i,j))
        if addcut(edges) == False:
            break

    print edges
    return model.getObjVal(),[]

'''
Source: https://scholarworks.waldenu.edu/cgi/viewcontent.cgi?article=1020&context=ijamt
'''
def scip_solver_3(customers, customer_count, vehicle_count, vehicle_capacity):
    '''
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

    '''

    model = Model("vrp")
    #model.hideOutput()
    model.setMinimize()

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
            y[i,j] = length(customers[i], customers[j])
            for v in Vr:
                X[v,i,j] = model.addVar(vtype="B", name="X(%s,%s,%s)" % (v,i,j))
        for v in Vr:
	    D[i,v] = model.addVar(lb=0, ub=Q, vtype="I", name="D(%s,%s)" % (i,v))

    '''
    Lower Bound for Number of Vehicles
    '''
    l = int(sum(d[i] for i in Am)/Q)
    for v in Vr:
        # Constraint: the total delivery load for a route is placed on the vehicle v,
        #             embarking on each trip, at the starting node itself
        #model.addCons(D[0,v] >= quicksum(X[v,i,j]*d[i] for i in Am for j in Am), "c12(%s)" % v)
        model.addCons(D[0,v] == Q, "c12(%s)" % v)

        for i in Am:
            # Constraint: the load on vehicle v, when departing from node i, is always lower than the vehicle capacity
            model.addCons(D[i,v] <= Q, "c11(%s,%s)" % (i,v))
            model.addCons(D[i,v] >= 0, "c17(%s,%s)" % (i,v))

        #model.addCons(quicksum(X[v,0,j] for j in Am) <= 1, "c2(%s)" % v)

            #for j in A:
                #model.addCons(X[v,i,j] == X[v,j,i], "c10(%s,%s,%s)" % (v,i,j))

           #     if j == i:
                    # Constraint: a vehicle always moves to another node, not the same
           #         model.addCons(X[v,i,j] == 0, "c18(%s,%s,%s)" % (v,i,j))

                #iif j > 0 and i > 0:
                    # Constraint: transit load constraints i.e., if arc (i, j) is visited by the vehicle v, then the
                    # quantity to be delivered by the vehicle has to decrease by d j
                #    model.addCons((D[i,v] - d[j] - D[j,v])*X[v,i,j] == 0, "c14(%s,%s,%s)" % (v,i,j))

    #for i in A:
    #    # Constraint: each node must be visited exactly once
    #    model.addCons(quicksum(X[v,i,j] for v in Vr for j in A) == 1, "c8(%s)" % (i))

    for j in A:
        if j > 0:
            # Constraint: each node must be visited exactly once
            model.addCons(quicksum(X[v,i,j] for v in Vr for i in A) == 1, "c8(%s)" % (j))
        for v in Vr:
            # Constraint: the same vehicle arrives and departs from each node it serves
            model.addCons(quicksum(X[v,i,j] for i in A) - quicksum(X[v,j,i] for i in A) == 0, "c10(%s,%s)" % (j,v))
    
    for i in A:
        for j in Am:
            for v in Vr:
                # Constraint: transit load constraints i.e., if arc (i, j) is visited by the vehicle v, then the
                # quantity to be delivered by the vehicle has to decrease by d j
                model.addCons((D[i,v] - d[j] - D[j,v])*X[v,i,j] == 0, "c14(%s,%s,%s)" % (i,j,v))

    # Constraint: the number of vehicles used should be, at least, the calculated lower bound
    #model.addCons(quicksum(X[v,0,j] for v in Vr for j in Am) >= l, "cBound")

    # Objective function: minimize the total cost of travel
    model.setObjective(quicksum(y[i,j]*X[v,i,j] for i in A for j in A for v in Vr), "minimize")

    model.optimize()
    best_sol = model.getBestSol()
    vehicle_tours = []

    for v in Vr:
        for i in A:
            for j in A:
                print "X[%s,%s,%s]: %s" % (v,i,j,model.getSolVal(best_sol, X[v,i,j]))

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
                        current_val = model.getSolVal(best_sol, X[v,i,j])
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

import sys

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        with open(file_location, 'r') as input_data_file:
            input_data = input_data_file.read()
        print(solve_it(input_data))
    else:

        print('This test requires an input file.  Please select one from the data directory. (i.e. python solver.py ./data/vrp_5_4_1)')

