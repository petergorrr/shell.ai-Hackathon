import pandas as pd
import json

# Load data
demand_file = 'dataset/demand.csv'
vehicles_file = 'dataset/vehicles.csv'
vehicles_fuels_file = 'dataset/vehicles_fuels.csv'

demand = pd.read_csv(demand_file)
vehicles = pd.read_csv(vehicles_file)
vehicles_fuels = pd.read_csv(vehicles_fuels_file)

size_buckets = ['S1', 'S2', 'S3', 'S4']
distance_buckets = ['D1', 'D2', 'D3', 'D4']
years = list(range(2023, 2039))

# Aggregate Yearly Demand
yearly_demand = {year: {size: {distance: int(demand[(demand['Year'] == year) &
                                                    (demand['Size'] == size) &
                                                    (demand['Distance'] == distance)]['Demand (km)'].sum())
                               for distance in distance_buckets}
                        for size in size_buckets}
                 for year in years}

# Get Vehicle Bucket Coverage
vehicle_bucket_coverage = {year: {size: {distance: [
    id for past_year in range(max(year - 9, min(years)), year + 1)
    for id in vehicles[(vehicles['Year'] == past_year) &
                       (vehicles['Size'] == size) &
                       (vehicles['Distance'].isin(distance_buckets[i:]))]['ID'].tolist()]
    for i, distance in enumerate(distance_buckets)}
    for size in size_buckets}
    for year in years}

# Get Fuel Type
fuel_dict = vehicles_fuels.groupby('ID')['Fuel'].apply(list).to_dict()

# Existing mapping data
data = {
    "distance_mapping": {
        'D1': 300,
        'D2': 400,
        'D3': 500,
        'D4': 600
    },
    "size_mapping": {
        'S1': 17,
        'S2': 44,
        'S3': 50,
        'S4': 64
    },
    "distance_buckets_mapping": {
        'D4': ['D1', 'D2', 'D3', 'D4'],
        'D3': ['D1', 'D2', 'D3'],
        'D2': ['D1', 'D2'],
        'D1': ['D1']
    },
    "cost_percentages": {
        1: {'resale': 0.90, 'insurance': 0.05, 'maintenance': 0.01},
        2: {'resale': 0.80, 'insurance': 0.06, 'maintenance': 0.03},
        3: {'resale': 0.70, 'insurance': 0.07, 'maintenance': 0.05},
        4: {'resale': 0.60, 'insurance': 0.08, 'maintenance': 0.07},
        5: {'resale': 0.50, 'insurance': 0.09, 'maintenance': 0.09},
        6: {'resale': 0.40, 'insurance': 0.10, 'maintenance': 0.11},
        7: {'resale': 0.30, 'insurance': 0.11, 'maintenance': 0.13},
        8: {'resale': 0.30, 'insurance': 0.12, 'maintenance': 0.15},
        9: {'resale': 0.30, 'insurance': 0.13, 'maintenance': 0.17},
        10: {'resale': 0.30, 'insurance': 0.14, 'maintenance': 0.19}
    },
    "carbon_emissions_dict": {
        2023: 11677957,
        2024: 10510161,
        2025: 9459145,
        2026: 8513230,
        2027: 7661907,
        2028: 6895716,
        2029: 6206145,
        2030: 5585530,
        2031: 5026977,
        2032: 4524279,
        2033: 4071851,
        2034: 3664666,
        2035: 3298199,
        2036: 2968379,
        2037: 2671541,
        2038: 2404387
    }
}

# Add yearly demand data to the existing dictionary
data["yearly_demand"] = yearly_demand

# Add vehicle bucket coverage data to the existing dictionary
data["vehicle_bucket_coverage"] = vehicle_bucket_coverage

# Add vehicle fuel types to the existing dictionary
data["vehicle_fuel_types"] = fuel_dict

# Specify the file path
file_path = 'dataset/mapping_and_cost_data.json'

# Write the data to a JSON file
with open(file_path, 'w') as json_file:
    json.dump(data, json_file, indent=4)

print(f"Data successfully written to {file_path}")
