#!/usr/bin/python
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
    
    obj, vehicle_tours = trivial_solver(customers, depot, vehicle_count, vehicle_capacity)
    #obj, vehicle_tours = scip_solver(customers, customer_count, vehicle_count, vehicle_capacity)

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
    model.hideOutput()
    model.setMinimize()

    c_range = range(0, customer_count)
    cd_range = range(1, customer_count)
    v_range = range(0, vehicle_count)

    x, c, d = {}, {}, {}
    for i in v_range:
        for j in c_range:
            # Variable: vehicle i visits customer j
            x[i,j] = model.addVar(vtype="B", name="x(%s,%s)" % (i,j))
            for k in c_range:
                d[j,k] = length(customers[j], customers[k])
                if k > j and j == 0:
                    # Variable: customer j is connected to customer k
	            c[j,k] = model.addVar(ub=2, vtype="I", name="c(%s,%s)" % (j,k))
                elif k > j:
	            c[j,k] = model.addVar(ub=1, vtype="I", name="c(%s,%s)" % (j,k))

    model.addCons(quicksum(c[0,k] for k in cd_range) == 2*vehicle_count, "DepotDegree")
    
    for i in v_range:
        # Constraint: the number of costumers visited by each vehicle cannot exceed its capacity
	model.addCons(quicksum(x[i,j]*customers[j].demand for j in c_range) <= vehicle_capacity, "cap(%s)" % i)
        
        # Constraint: every vehicle must visit the first customer (depot)
        #model.addCons(x[i,0] > 0, "dep(%s)" % i)
    
    for j in cd_range:
        # Constraint: every customer has to be visited by exactly one vehicle
        model.addCons(quicksum(x[i,j] for i in v_range) == 1, "visit(%s)" % j)

        # Constraint: each customer has to have two connections
        model.addCons(quicksum(c[k,j] for k in c_range if k < j) + \
            quicksum(c[j,k] for k in c_range if k > j) == 2, "Degree(%s)"%j)
        
    
    for i in v_range:
        for j in c_range:   
             for k in c_range:
                if k > j and j > 0:
                    # Constraint: if a vehicle visits two customers, they must be connected
                    model.addCons(x[i,j]*x[i,k] == c[j,k], "rel(%s, %s, %s)" %(i,j,k))
    
    # Minimize: sum0..X(vehicleX(dist(depot, firstCustomer) + sum(dist(customerN, customerK)) + dist(lastCustomer, depot)))
    model.setObjective(quicksum(d[j,k]*c[j,k] for j in c_range for k in c_range if k > j))

    #model.data = x, c
    model.optimize()
    best_sol = model.getBestSol()
    vehicle_tours = []
    i = 0
    for j in cd_range:
        vehicle_tours.append([])
        current_val = model.getSolVal(best_sol, c[0,j])
        if current_val > 0:
            vehicle_tours[i].append(customers[j])
            for k in cd_range:
                if k > j:
                    current_val = model.getSolVal(best_sol, c[j,k])
                    if current_val > 0:
                        vehicle_tours[i].append(customers[k])
        i =+ 1
    
    for (j,k) in c:
        print("(%s,%s): %s" % (j,k,model.getSolVal(best_sol, c[j,k])))
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
    obj = model.getSolObjVal(best_sol)

    vehicle_tours = []

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

