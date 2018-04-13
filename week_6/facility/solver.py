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
    m.setRealParam("limits/gap", 0.01)
    m.setRealParam("limits/time", 3600*10)

    # Variables to define if customer 'c' is assinged to facility 'f'
    # and if facility is active.
    x, f, d = {}, {}, {}
    for i in range(0, n_f):
        f[i] = m.addVar(vtype="B", name="f(%s)"%(i))
        for j in range(0, n_c):
            x[i,j] = m.addVar(vtype="B", name="x(%s,%s)"%(i,j))

            # Distance between facilities and customers
            d[i,j] = facility_customer_dist(facilities[i], customers[j])
        
    for i in range(0, n_f):
        # Constraint 1: The sum of the demand from all the consumers 'c'
        # assigned to facility 'f' should be equal or less than the
        # facility's capacity.
        m.addCons(quicksum(x[i,j]*customers[j].demand for j in range(0, n_c)) <= facilities[i].capacity, "Cap(%s)"%i)

        # Constraint to make sure a not open facility is not assigned
        m.addCons(quicksum(x[i,j] - f[i] for j in range(0, n_c)) <= f[i], "Fac(%s)"%i)

    # Constraint 2: Each customer must be served by exactly one facility
    for j in range(0, n_c):
        m.addCons(quicksum(x[i,j] for i in range(0, n_f)) == 1, "Cust(%s)"%j)

    # Objective function
    m.setObjective(quicksum(x[i,j]*d[i,j] for (i,j) in x) + quicksum(f[i]*facilities[i].setup_cost for i in f), "minimize")

    m.data = x, f
    m.optimize()

    sol = []
    for j in range(0, n_c):
        for i in range(0, n_f):
            current_val = m.getVal(x[i,j])
            if current_val == 1:
                sol.append(i)

    #assert len(sol) == len(customers)

    '''
    sol = [0 for i in range(0, n_c)]
    for i in range(0, n_f):
        for j in range(0, n_c):
            current_val = m.getVal(x[i,j])
            if current_val == 1:
                #print "x[%s,%s] = %s" % (i,j,current_val)
                sol[j] = i
    '''

    obj = m.getObjVal()
    return obj, sol

def facility_customer_dist(facility, customer):
    x_dist = math.pow(facility.location.x - customer.location.x, 2)
    y_dist = math.pow(facility.location.y - customer.location.y, 2)
    return math.sqrt(x_dist + y_dist)

def facility_is_alocated(x, f):
    for i, j in x:
        if(f == i):
            return True
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

'''
Outputs:

3276471.40 0
7 7 7 7 7 7 6 7 7 7 10 7 7 7 7 7 7 6 7 7 7 7 7 7 7 7 21 7 7 7 7 7 7 16 7 7 11 6 7 7 7 7 7 7 7 7 7 7 9 7

3756860.34 0
28 24 19 25 14 15 34 3 9 24 35 42 41 24 49 3 16 26 43 45 45 41 9 34 9 13 19 8 38 24 24 7 9 25 31 33 28 9 28 25 38 40 35 7 2 19 40 25 41 9 34 44 41 18 35 5 9 31 14 35 31 35 44 43 9 4 8 14 25 45 28 33 41 39 42 6 8 35 6 24 40 47 31 24 31 24 24 45 34 16 7 2 5 39 25 35 24 40 31 3 47 6 39 16 31 44 2 16 9 13 8 9 47 35 15 24 43 25 42 16 35 28 34 35 13 5 8 35 18 11 38 39 43 41 47 44 9 41 9 38 38 28 19 9 28 28 42 41 47 16 35 38 29 9 45 49 16 25 26 31 38 5 49 10 7 40 44 29 34 10 2 41 35 31 40 28 47 49 44 33 4 2 16 47 28 9 3 31 11 16 31 25 5 42 13 31 8 40 44 45

1965.55 0
70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70 70

22726936.83 0
19 68 64 56 64 34 51 51 51 68 19 64 19 64 51 68 34 51 64 68 51 51 56 64 51 51 68 51 34 51 56 68 19 19 48 48 48 56 51 51 48 19 64 56 56 51 51 19 48 56 51 64 51 51 64 64 51 19 19 51 64 56 68 34 51 19 51 48 51 19 51 34 51 64 48 51 68 34 51 64 34 19 34 19 51 56 56 56 48 51 51 34 64 19 19 19 56 51 64 51 64 19 51 68 51 51 19 68 68 19 64 51 51 56 51 48 51 68 51 64 68 51 51 56 64 19 56 48 51 51 48 56 51 51 51 34 51 48 48 19 51 56 51 56 68 68 68 51 64 51 68 51 51 34 51 19 51 51 51 51 51 51 51 48 68 64 34 19 64 51 48 48 51 19 34 51 51 56 34 64 48 34 64 56 51 19 51 68 34 56 51 48 68 68 51 51 51 34 51 51 51 51 19 51 68 56 64 48 51 34 51 19 51 51 64 68 64 19 19 68 68 68 56 48 34 51 51 19 64 51 64 64 19 56 51 48 51 56 51 51 68 34 68 34 64 68 34 64 64 51 56 51 34 51 34 51 51 51 56 51 19 48 51 56 19 51 48 48 19 56 56 19 48 51 51 56 64 64 48 51 68 48 19 19 34 68 51 34 56 19 48 51 51 19 51 48 51 68 51 56 34 56 56 64 56 34 19 64 34 48 51 68 34 56 56 51 34 64 56 51 68 48 51 51 48 51 64 51 19 51 48 48 51 51 51 34 51 64 68 64 51 51 51 68 51 48 19 64 51 34 51 51 56 68 51 51 48 51 19 51 48 51 56 68 51 51 56 19 51 51 51 64 51 56 51 51 68 51 68 68 51 51 68 64 48 64 51 19 51 56 51 51 19 19 51 64 56 34 56 34 64 19 51 51 64 34 48 51 51 19 64 51 64 68 51 51 48 48 51 64 68 51 51 56 64 64 48 68 51 51 56 51 51 56 19 51 19 51 56 64 51 34 48 48 51 64 51 51 56 68 64 51 56 64 68 34 51 64 51 34 51 51 56 51 68 51 51 34 51 19 48 56 34 51 19 64 64 48 68 68 51 56 51 48 51 19 64 68 34 64 64 19 51 48 68 19 56 56 19 51 34 68 68 56 51 48 51 19 51 51 51 56 19 51 34 51 64 48 34 51 64 68 51 64 56 64 51 51 64 48 19 51 48 51 34 34 34 64 51 51 51 51 34 51 68 48 51 56 51 51 51 64 68 51 64 19 56 51 51 56 51 68 51 48 48 51 51 19 51 51 68 64 64 68 51 48 48 68 19 51 68 64 34 19 56 19 34 34 51 51 19 51 51 51 51 48 34 51 34 51 64 64 34 51 56 51 48 64 34 51 19 56 51 19 51 51 68 48 48 56 64 51 56 64 51 19 51 56 51 51 51 68 19 51 34 48 51 51 51 68 34 51 51 64 51 64 34 64 51 51 68 19 19 19 51 34 51 34 51 56 48 68 51 51 51 48 34 51 19 64 19 51 51 68 48 64 64 68 51 51 34 48 48 64 51 64 64 56 51 68 51 51 64 48 51 51 68 34 34 19 51 51 34 51 48 51 34 51 56 64 48 64 51 34 48 19 51 51 51 51 68 68 48 51 51 34 51 51 34 64 68 51 68 51 64 34 68 64 51 19 51 51 56 68 68 19 19 64 19 34 48 64 51 34 64 19 56 64 51 51 64 51 51 19 56 64 19 51 48 34 51 48 19 51 51 56 56 51 51 51 51 51 64 51 51 48 51 51 19 51 34 51 19 56 51 51 56 48 19 19 51 34 51 51 19 64 19 48 56 51 48 68 48 64 64 48 51 48 64 68 56 51 56 64 56 34 34 51 68 19 64 51 64 48 51 64 64 51 64 51 51 68 48 64 64 64 51 56 48 68 51 56 51 51 34 51 51 19 51 19 51 56 68 64 64 19 51 64 48 51 51 51 48 51 51 68 64 64 48 68 19 51 64 64 51 48 51 51 51 19 34 64 51 51 51 51 56 19 51 51 48 68 64 68 51 19 51 51 51 48 51 51 34 68 51 68 56 56 56 51 56 19 19 64 64 19 51 64 68 56 51 56 48 48 51 51 51 64 51 34 64 48 51 68 51 34 51 48 51 56 51 51 34 51 68 48 68 51 34 19 34 34 56 68 56 48 64 48 51 19 68 51 56 56 68 64 48 64 68 64 51 51 51 51 51 68 19 68 51 19 56 64 51 51 64 56 19 51 19 51

4717579.36 0
155 0 132 66 76 33 116 120 6 161 167 19 35 98 136 183 99 169 35 46 60 85 139 192 167 9 95 118 51 151 68 180 72 175 3 28 20 157 120 114 180 49 151 175 142 35 102 9 123 30 133 18 4 157 90 99 162 3 160 118 183 167 3 26 51 37 25 25 90 198 18 162 146 60 118 70 159 30 123 132 57 92 37 71 146 153 2 180 18 30 139 98 85 33 141 94 162 90 113 108 149 119 46 118 175 192 140 173 144 99 34 120 28 30 165 33 139 69 37 32 185 0 171 180 192 6 197 66 6 76 4 123 155 98 66 49 18 105 60 85 133 69 32 140 3 119 4 142 92 197 160 0 113 176 22 146 146 32 101 160 123 118 32 121 9 56 123 151 135 146 85 49 32 22 185 45 95 167 9 60 94 199 139 177 177 151 151 118 26 178 60 49 26 35 100 185 123 144 68 9 119 176 183 136 19 173 121 102 28 25 68 94 4 108 165 116 92 72 175 28 99 34 165 60 186 55 177 32 2 160 114 99 6 94 159 85 133 123 118 167 37 100 95 100 105 197 45 151 45 133 172 90 89 9 7 152 101 28 186 144 133 30 198 85 126 153 126 173 4 98 19 132 108 34 137 161 71 45 169 2 100 116 113 123 56 114 37 0 157 167 189 152 151 70 20 94 113 52 159 46 70 76 18 120 175 26 189 197 26 169 157 137 28 199 185 169 116 199 101 135 141 116 120 118 198 159 22 25 51 30 35 144 22 178 102 71 70 89 161 3 19 69 171 168 69 185 135 108 35 90 141 25 89 126 183 126 116 171 79 51 189 34 101 197 92 70 68 92 79 0 71 116 100 66 57 165 119 153 69 51 157 133 89 0 178 161 20 98 178 76 140 90 45 35 180 137 79 105 192 151 79 175 183 162 94 169 113 189 178 139 92 9 120 0 159 70 198 197 151 116 120 155 144 68 71 69 52 153 159 186 188 6 3 159 7 188 57 57 60 18 99 7 37 52 183 19 173 157 26 188 34 7 34 132 173 22 159 167 136 136 142 137 26 46 152 25 25 22 71 126 70 144 101 113 102 144 68 137 113 89 171 30 141 56 135 146 3 172 132 186 46 144 186 52 69 119 0 188 149 144 45 89 45 176 197 162 95 100 160 102 22 175 7 188 123 180 9 19 119 178 3 144 9 159 7 45 186 144 123 70 177 168 173 71 140 120 60 72 160 159 71 192 177 2 167 70 142 139 135 161 186 173 6 108 92 146 94 66 101 34 55 165 92 176 95 34 72 168 135 2 68 149 198 180 186 137 28 160 185 89 172 176 140 101 146 142 157 102 160 139 114 183 94 66 160 188 46 171 183 183 157 3 108 141 108 108 171 72 7 98 33 6 33 95 4 177 32 192 3 165 26 0 135 176 101 134 185 72 149 199 198 180 121 94 49 121 199 66 72 197 162 185 92 68 173 121 162 167 57 165 2 35 95 142 95 133 7 51 26 137 57 19 72 60 46 126 85 45 136 30 71 178 197 37 171 178 56 185 167 142 66 34 168 175 32 100 165 55 153 199 57 4 114 146 51 2 19 66 72 19 157 51 180 101 173 98 118 4 28 52 56 90 85 9 34 102 52 51 60 186 34 60 185 60 76 186 144 28 189 137 153 161 30 69 139 135 76 157 168 37 57 79 185 116 173 172 140 94 7 52 185 168 56 133 183 105 51 152 69 32 175 113 33 169 105 26 189 33 141 139 0 86 157 199 180 178 79 22 114 56 105


'''
