#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import namedtuple
import math
from pyscipopt import Model, quicksum, multidict

Point = namedtuple("Point", ['x', 'y'])
Facility = namedtuple("Facility", ['index', 'setup_cost', 'capacity', 'location'])
Customer = namedtuple("Customer", ['index', 'demand', 'location'])

def length(point1, point2):
    return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

def solve_it(input_data):
    # Modify this code to run your optimization algorithm

    # parse the input
    lines = input_data.split('\n')

    parts = lines[0].split()
    facility_count = int(parts[0])
    customer_count = int(parts[1])
    
    facilities = []
    for i in range(1, facility_count+1):
        parts = lines[i].split()
        facilities.append(Facility(i-1, float(parts[0]), int(parts[1]), Point(float(parts[2]), float(parts[3])) ))

    customers = []
    for i in range(facility_count+1, facility_count+1+customer_count):
        parts = lines[i].split()
        customers.append(Customer(i-1-facility_count, int(parts[0]), Point(float(parts[1]), float(parts[2]))))

    obj, solution = scip_solver(customers, facilities)

    # prepare the solution in the specified output format
    output_data = '%.2f' % obj + ' ' + str(0) + '\n'
    output_data += ' '.join(map(str, solution))

    return output_data

# build a trivial solution
# pack the facilities one by one until all the customers are served
def trivial_solver(customers, facilities):
    # build a trivial solution
    # pack the facilities one by one until all the customers are served
    solution = [-1]*len(customers)
    capacity_remaining = [f.capacity for f in facilities]

    facility_index = 0
    for customer in customers:
        if capacity_remaining[facility_index] >= customer.demand:
            solution[customer.index] = facility_index
            capacity_remaining[facility_index] -= customer.demand
        else:
            facility_index += 1
            assert capacity_remaining[facility_index] >= customer.demand
            solution[customer.index] = facility_index
            capacity_remaining[facility_index] -= customer.demand

    used = [0]*len(facilities)
    for facility_index in solution:
        used[facility_index] = 1

    # calculate the cost of the solution
    obj = sum([f.setup_cost*used[f.index] for f in facilities])
    for customer in customers:
        obj += length(customer.location, facilities[solution[customer.index]].location)
    return obj, solution

'''
Trying out MIP using PySCIPOpt.
References:
https://github.com/SCIP-Interfaces/PySCIPOpt
http://scip.zib.de/
'''
def scip_solver(customers, facilities):
    '''
    Data structure:

    Point = namedtuple("Point", ['x', 'y'])
    Facility = namedtuple("Facility", ['index', 'setup_cost', 'capacity', 'location'])
    Customer = namedtuple("Customer", ['index', 'demand', 'location'])
    '''
    
    n_f = len(facilities)
    n_c = len(customers)

    m = Model("Facility")
    m.hideOutput
    m.setMinimize()

    # Variables to define if customer 'c' is assinged to facility 'f'
    x, s = {}, {}
    for i in range(0, n_f):
        for j in range(0, n_c):
            x[i,j] = m.addVar(vtype="B", name="x(%s,%s)"%(i,j))

    # Costs for each facility
    c_f = {}
    for i in range(0, n_f):
        c_f[i] = facilities[i].setup_cost
    #c_f = [i.setup_cost for i in facilities]

    # Distance between facilities and customers
    d = {}
    for i in range(0, n_f):
        for j in range(0, n_c):
            d[i,j] = facility_customer_dist(facilities[i], customers[j])

    # Constraint 1: The sum of the demand from all the consumers 'c'
    # assigned to facility 'f' should be equal or less than the
    # facility's capacity.
    for i in range(0, n_f):
        m.addCons(quicksum(x[i,j]*customers[j].demand for j in range(0, n_c)) <= facilities[i].capacity, "Cap(%s)"%i)

    # Constraint 2: Each customer must be served by exactly one facility
    for j in range(0, n_c):
        m.addCons(quicksum(x[i,j] for i in range(0, n_f)) == 1, "Cust(%s)"%j)

    # Objective function
    #  + quicksum(x[i,j] for (i,j) in x)
    #m.setObjective(quicksum(c_f[i] for (i,j) in x if x[i,j] == 1), "minimize")
    m.setObjective(quicksum(x[i,j]*d[i,j] for (i,j) in x) + quicksum(c_f[i] for i in c_f if facility_is_alocated(x, i)), "minimize")

    #m.data = x
    m.optimize()

    vals = m.getVars()
    i_v = 0
    sol = [0 for i in range(0, n_c)]
    for i in range(0, n_f):
        for j in range(0, n_c):
            current_val = m.getVal(vals[i_v])
            if current_val == 1:
                sol[j] = i
                #print "Customer %s assigned to facility %s"%(j,i)
            i_v += 1

    obj = m.getObjVal()
    return obj, sol

def facility_customer_dist(facility, customer):
    x_dist = math.pow(facility.location.x - customer.location.x, 2)
    y_dist = math.pow(facility.location.y - customer.location.y, 2)
    return math.sqrt(x_dist + y_dist)

def facility_is_alocated(x, f):
    for i, j in x:
        return (x[f, j]) >= (1)
    return False

import sys

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        with open(file_location, 'r') as input_data_file:
            input_data = input_data_file.read()
        print(solve_it(input_data))
    else:
        print('This test requires an input file.  Please select one from the data directory. (i.e. python solver.py ./data/fl_16_2)')

