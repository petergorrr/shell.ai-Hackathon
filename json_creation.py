import pandas as pd
import json


class FleetDecarbonization:

    def __init__(self, demand_file, vehicles_file):
        # Load the demand and vehicles data
        self.demand = pd.read_csv(demand_file)
        self.vehicles = pd.read_csv(vehicles_file)
        self.size_buckets = ['S1', 'S2', 'S3', 'S4']
        self.distance_buckets = ['D1', 'D2', 'D3', 'D4']

    def aggregate_yearly_demand(self):
        """
        Aggregate the total yearly demand traveled distance for the respective size and distance bucket vehicles.
        """
        years = list(range(2023, 2039))
        yearly_demand = {year: {size: {distance: 0 for distance in self.distance_buckets}
                                for size in self.size_buckets} for year in years}

        for year in years:
            for size in self.size_buckets:
                for distance in self.distance_buckets:
                    total_distance = int(self.demand[(self.demand['Year'] == year) &
                                                     (self.demand['Size'] == size) &
                                                     (self.demand['Distance'] == distance)]['Demand (km)'].sum())
                    yearly_demand[year][size][distance] = total_distance

        return yearly_demand

    def get_vehicle_bucket_coverage(self):
        years = list(range(2023, 2039))
        vehicle_bucket_coverage = {year: {size: {distance: [] for distance in self.distance_buckets} for size in self.size_buckets} for year in years}

        for year in years:
            for size in self.size_buckets:
                for i, distance in enumerate(self.distance_buckets):
                    vehicle_id_list = []
                    for subsequent_distance in self.distance_buckets[i:]:
                        vehicle_ids = self.vehicles[
                            (self.vehicles['Year'] == year) &
                            (self.vehicles['Size'] == size) &
                            (self.vehicles['Distance'] == subsequent_distance)
                        ]['ID'].tolist()
                        vehicle_id_list.extend(vehicle_ids)

                    vehicle_bucket_coverage[year][size][distance].extend(vehicle_id_list)

        return vehicle_bucket_coverage


# Initialize the FleetDecarbonization class with the demand and vehicles files
fleet = FleetDecarbonization('dataset/demand.csv', 'dataset/vehicles.csv')

# Calculate the yearly demand
yearly_demand = fleet.aggregate_yearly_demand()

# Get the vehicle bucket coverage data
vehicle_bucket_coverage = fleet.get_vehicle_bucket_coverage()

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
