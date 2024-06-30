import pandas as pd
import json

# Load data
demand_file = 'dataset/demand.csv'
vehicles_file = 'dataset/vehicles.csv'
vehicles_fuels_file = 'dataset/vehicles_fuels.csv'
fuels_file = 'dataset/fuels.csv'

demand = pd.read_csv(demand_file)
vehicles = pd.read_csv(vehicles_file)
vehicles_fuels = pd.read_csv(vehicles_fuels_file)
fuels = pd.read_csv(fuels_file)

size_buckets = ['S1', 'S2', 'S3', 'S4']
distance_buckets = ['D1', 'D2', 'D3', 'D4']
years = list(range(2023, 2039))

# Aggregate Yearly Demand
yearly_demand = {
    year: {
        size: {
            distance: int(demand[(demand['Year'] == year) & (demand['Size'] == size) & (
                demand['Distance'] == distance)]['Demand (km)'].sum())
            for distance in distance_buckets
        }
        for size in size_buckets
    }
    for year in years
}


def extract_vehicles_for_demand(vehicles, size_buckets, years):
    distance_levels = {'D1': 1, 'D2': 2, 'D3': 3, 'D4': 4}
    inverse_distance_levels = {v: k for k, v in distance_levels.items()}

    return {
        year: {
            size_bucket: {
                inverse_distance_levels[distance_level]: vehicles[
                    (vehicles['Year'] <= year) &
                    (vehicles['Year'] >= year - 9) &
                    (vehicles['Size'] == size_bucket) &
                    (vehicles['Distance'].apply(
                        lambda x: distance_levels[x] >= distance_level))
                ]['ID'].tolist()
                for distance_level in range(1, 5)
            }
            for size_bucket in size_buckets
        }
        for year in years
    }


# Get Fuel Type with Consumption
fuel_consumption_dict = vehicles_fuels.groupby('ID').apply(
    lambda x: x.set_index('Fuel')['Consumption (unit_fuel/km)'].to_dict()).to_dict()

# Extract eligible vehicles for each year, size, and distance bucket
eligible_vehicles = extract_vehicles_for_demand(vehicles, size_buckets, years)

# Extract cost and yearly range data for each vehicle
vehicle_data = vehicles.set_index(
    'ID')[['Cost ($)', 'Yearly range (km)']].to_dict('index')

# Create vehicles_details structure
vehicles_details = {}
for year in years:
    for size, size_dict in eligible_vehicles[year].items():
        for distance, vehicle_list in size_dict.items():
            for vehicle in vehicle_list:
                if vehicle in vehicle_data:
                    vehicles_details[vehicle] = {
                        "cost": vehicle_data[vehicle]['Cost ($)'],
                        "size": size,
                        "distance": distance,
                        "yearly range": vehicle_data[vehicle]['Yearly range (km)']
                    }

# Extract fuels data
fuels_data = fuels.to_dict(orient='records')

# Reorganize fuels data to match the required format
fuels_reorganized = {}
for record in fuels_data:
    fuel = record.pop("Fuel")
    year = record.pop("Year")
    if fuel not in fuels_reorganized:
        fuels_reorganized[fuel] = {}
    fuels_reorganized[fuel][year] = record

# Existing mapping data
data = {
    "size_mapping": {
        'S1': 17,
        'S2': 44,
        'S3': 50,
        'S4': 64
    },
    "distance_mapping": {
        'D1': 300,
        'D2': 400,
        'D3': 500,
        'D4': 600
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
    "carbon_emissions": {
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
    },
    "yearly_demand": yearly_demand,
    "vehicle_bucket_coverage": eligible_vehicles,
    "vehicle_details": vehicles_details,
    "vehicle_fuel_consumptions": fuel_consumption_dict,
    "fuels_data": fuels_reorganized
}

# Specify the file path
file_path = 'dataset/mapping_and_cost_data.json'

# Write the data to a JSON file
with open(file_path, 'w') as json_file:
    json.dump(data, json_file, indent=4)

print(f"Data successfully written to {file_path}")
