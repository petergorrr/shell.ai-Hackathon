import pandas as pd
import json

# Load data
demand_file = 'dataset/demand.csv'
vehicles_file = 'dataset/vehicles.csv'
demand = pd.read_csv(demand_file)
vehicles = pd.read_csv(vehicles_file)

size_buckets = ['S1', 'S2', 'S3', 'S4']
distance_buckets = ['D1', 'D2', 'D3', 'D4']
years = list(range(2023, 2039))

# Aggregate Yearly Demand
def aggregate_yearly_demand(demand, size_buckets, distance_buckets, years):
    yearly_demand = {year: {size: {distance: 0 for distance in distance_buckets}
                            for size in size_buckets} for year in years}

    for year in years:
        for size in size_buckets:
            for distance in distance_buckets:
                total_distance = int(demand[(demand['Year'] == year) &
                                            (demand['Size'] == size) &
                                            (demand['Distance'] == distance)]['Demand (km)'].sum())
                yearly_demand[year][size][distance] = total_distance

    return yearly_demand

# Get Vehicle Bucket Coverage
def get_vehicle_bucket_coverage(vehicles, size_buckets, distance_buckets, years):
    vehicle_bucket_coverage = {year: {size: {distance: []
                                             for distance in distance_buckets} for size in size_buckets} for year in years}

    for year in years:
        for size in size_buckets:
            for i, distance in enumerate(distance_buckets):
                vehicle_id_list = []
                for subsequent_distance in distance_buckets[i:]:
                    vehicle_ids = vehicles[
                        (vehicles['Year'] == year) &
                        (vehicles['Size'] == size) &
                        (vehicles['Distance'] == subsequent_distance)
                    ]['ID'].tolist()
                    vehicle_id_list.extend(vehicle_ids)

                vehicle_bucket_coverage[year][size][distance].extend(
                    vehicle_id_list)

    return vehicle_bucket_coverage

# Calculate the yearly demand
yearly_demand = aggregate_yearly_demand(demand, size_buckets, distance_buckets, years)

# Get the vehicle bucket coverage data
vehicle_bucket_coverage = get_vehicle_bucket_coverage(vehicles, size_buckets, distance_buckets, years)

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

# Specify the file path
file_path = 'dataset/mapping_and_cost_data.json'

# Write the data to a JSON file
with open(file_path, 'w') as json_file:
    json.dump(data, json_file, indent=4)

print(f"Data successfully written to {file_path}")
