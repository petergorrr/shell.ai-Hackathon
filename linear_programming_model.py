import pandas as pd
import json
from pulp import *

# Load data from JSON file
file_path = 'dataset/mapping_and_cost_data.json'
with open(file_path) as f:
    data = json.load(f)

# Check the data structure
data_structure = {key: type(value) for key, value in data.items()}
print(data_structure)

# Define years and other sets
years = list(range(2023, 2039))
vehicle_types = list(data['vehicle_fuel_types'].keys())
size_buckets = data['size_mapping'].keys()
distance_buckets = data['distance_mapping'].keys()
fuels = ['Electricity', 'LNG', 'BioLNG', 'B20', 'HVO']

# Create the LP problem
prob = LpProblem("Fleet_Decarbonization", LpMinimize)

# Decision variables
X = LpVariable.dicts("Buy", (years, vehicle_types), 0, None, LpInteger)
U = LpVariable.dicts("Use", (years, vehicle_types), 0, None, LpInteger)
S = LpVariable.dicts("Sell", (years, vehicle_types), 0, None, LpInteger)
D = LpVariable.dicts("Distance", (years, vehicle_types, distance_buckets), 0, None, LpContinuous)
F = LpVariable.dicts("Fuel", (years, vehicle_types, fuels), 0, None, LpContinuous)

# Ensure the keys exist in the data
vehicles_data = data.get('vehicles', {})
fuel_data = data.get('fuels', {})
yearly_demand = data.get('yearly_demand', {})
carbon_emissions = data.get('carbon_emissions_dict', {})
cost_percentages = data.get('cost_percentages', {})

# Objective function
C_buy = lpSum([X[y][v] * vehicles_data.get(v, {}).get('Cost ($)', 0) for y in years for v in vehicle_types])
C_ins = lpSum([U[y][v] * cost_percentages.get(str(min(y-x, 10)), {}).get('insurance', 0) * vehicles_data.get(v, {}).get('Cost ($)', 0) for y in years for v in vehicle_types for x in range(10)])
C_mnt = lpSum([U[y][v] * cost_percentages.get(str(min(y-x, 10)), {}).get('maintenance', 0) * vehicles_data.get(v, {}).get('Cost ($)', 0) for y in years for v in vehicle_types for x in range(10)])
C_fuel = lpSum([F[y][v][f] * fuel_data.get(f, {}).get('Cost ($/unit_fuel)', 0) for y in years for v in vehicle_types for f in fuels])
C_sell = lpSum([S[y][v] * cost_percentages.get(str(min(y-x, 10)), {}).get('resale', 0) * vehicles_data.get(v, {}).get('Cost ($)', 0) for y in years for v in vehicle_types for x in range(10)])

prob += C_buy + C_ins + C_mnt + C_fuel - C_sell

# Constraints
for y in years:
    for s in size_buckets:
        for d in distance_buckets:
            prob += lpSum([D[y][v][d] for v in vehicle_types if vehicles_data.get(v, {}).get('Size') == s]) >= yearly_demand.get(str(y), {}).get(s, {}).get(d, 0)

for y in years:
    prob += lpSum([D[y][v][d] * data['vehicle_fuel_types'][v][0] * fuel_data.get(f, {}).get('Emissions (CO2/unit_fuel)', 0) for v in vehicle_types for f in fuels for d in distance_buckets]) <= carbon_emissions.get(str(y), 0)

for y in years:
    for v in vehicle_types:
        prob += U[y][v] <= X[y][v] + lpSum([X[ty][v] - S[ty][v] for ty in range(max(2023, y-9), y+1)])

for y in years:
    for v in vehicle_types:
        if y-10 in years:
            prob += S[y][v] >= X[y-10][v]

for y in years:
    for v in vehicle_types:
        prob += S[y][v] <= 0.2 * lpSum([X[ty][v] - S[ty][v] for ty in range(max(2023, y-10), y+1)])

# Solve the problem
prob.solve()

# Check the status of the solution
print(f"Status: {LpStatus[prob.status]}")

# Print the values of the decision variables if the solution is feasible
if LpStatus[prob.status] == 'Optimal':
    # Create a DataFrame to store the output
    output_data = []
    for y in years:
        for v in vehicle_types:
            if X[y][v].varValue > 0:
                output_data.append([y, v, int(X[y][v].varValue), "Buy", "", "", ""])
            if U[y][v].varValue > 0:
                for d in distance_buckets:
                    if D[y][v][d].varValue > 0:
                        fuel_type = data['vehicle_fuel_types'][v][0]  # Assuming the first fuel type
                        distance_per_vehicle = D[y][v][d].varValue / U[y][v].varValue
                        output_data.append([y, v, int(U[y][v].varValue), "Use", fuel_type, d, distance_per_vehicle])
            if S[y][v].varValue > 0:
                output_data.append([y, v, int(S[y][v].varValue), "Sell", "", "", ""])

    # Load the provided sample submission format
    sample_submission_path = 'dataset/sample_submission.csv'
    sample_submission = pd.read_csv(sample_submission_path)

    # Populate the DataFrame
    output_df = pd.DataFrame(output_data, columns=sample_submission.columns)

    # Save the DataFrame to a CSV file
    output_csv_path = 'dataset/solution.csv'
    output_df.to_csv(output_csv_path, index=False)

    print(f"Solution saved to {output_csv_path}")
else:
    print("No feasible solution found.")
