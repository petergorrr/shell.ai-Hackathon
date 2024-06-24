import pandas as pd
import json

class FleetDecarbonization:

    hard_constraint_penalty = 1000

    def __init__(self,
                 cost_profiles_file,
                 fuels_file,
                 vehicles_file,
                 vehicles_fuels_file,
                 mapping_data_file):

        # Load data
        self.cost_profiles = pd.read_csv(cost_profiles_file)
        self.fuels = pd.read_csv(fuels_file)
        self.vehicles = pd.read_csv(vehicles_file)
        self.vehicles_fuels = pd.read_csv(vehicles_fuels_file)

        # Load mapping data from JSON file
        with open(mapping_data_file, 'r') as f:
            mapping_data = json.load(f)

        # Set attributes from JSON data
        self.distance_mapping = mapping_data['distance_mapping']
        self.size_mapping = mapping_data['size_mapping']
        self.cost_percentages = {int(k): v for k, v in mapping_data['cost_percentages'].items()}
        self.carbon_emissions_dict = {int(k): v for k, v in mapping_data['carbon_emissions_dict'].items()}
        self.yearly_demand = {int(k): {sk: {dk: int(dv) for dk, dv in sv.items()} for sk, sv in v.items()} for k, v in mapping_data['yearly_demand'].items()}

        # Initialize other attributes
        self.size_buckets = list(self.size_mapping.keys())
        self.distance_buckets = list(self.distance_mapping.keys())
        self.gene = ['buy', 'sell', 'use']

        # Get vehicles that can contribute to each demand
        self.distance_buckets_vehicles = self.get_distance_buckets_vehicles()

        # Get total distance covered for each criteria
        self.total_distance = self.calculate_total_distance()
        
        self.vehicle_bucket_coverage = {int(k): {sk: {dk: v for dk, v in sv.items()} for sk, sv in v.items()} for k, v in mapping_data['vehicle_bucket_coverage'].items()}


    def get_resale_value(self, purchase_cost, year):
        """
        Get the resale value of a vehicle based on its purchase cost and the number of years since purchase.
        """
        if year in self.cost_percentages:
            return purchase_cost * self.cost_percentages[year]['resale']
        return purchase_cost * 0.30  # default value for years beyond 10

    def get_insurance_cost(self, purchase_cost, year):
        """
        Get the insurance cost of a vehicle based on its purchase cost and the number of years since purchase.
        """
        if year in self.cost_percentages:
            return purchase_cost * self.cost_percentages[year]['insurance']
        return purchase_cost * 0.14  # default value for years beyond 10

    def get_maintenance_cost(self, purchase_cost, year):
        """
        Get the maintenance cost of a vehicle based on its purchase cost and the number of years since purchase.
        """
        if year in self.cost_percentages:
            return purchase_cost * self.cost_percentages[year]['maintenance']
        return purchase_cost * 0.19  # default value for years beyond 10

    def get_vehicle_info(self, vehicle_id):
        """
        Get the size and distance bucket for a specific vehicle.
        """
        vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
        if vehicle.empty:
            return None, None

        size = vehicle['Size'].values[0]
        distance = vehicle['Distance'].values[0]
        return size, distance

    def get_cost_values(self, purchase_cost, year):
        """
        Get the insurance, resale, and maintenance costs for a vehicle based on its purchase cost and the number of years since purchase.
        """
        resale_value = self.get_resale_value(purchase_cost, year)
        insurance_cost = self.get_insurance_cost(purchase_cost, year)
        maintenance_cost = self.get_maintenance_cost(purchase_cost, year)
        return resale_value, insurance_cost, maintenance_cost

    def get_distance_buckets_vehicles(self):
        years = self.carbon_emissions_dict.keys() 
        distance_bucket_vehicles = {year: {size: {distance: [] for distance in self.distance_buckets} for size in self.size_buckets}for year in years}
        
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
                    
                    distance_bucket_vehicles[year][size][distance].extend(vehicle_id_list)
          
        return distance_bucket_vehicles

    def calculate_total_distance(self):
        # Define this method according to the specific logic required
        pass
    
    
def main():
    # fleet = FleetDecarbonization(
    #     'dataset/cost_profiles.csv',
    #     'dataset/fuels.csv',
    #     'dataset/vehicles.csv',
    #     'dataset/vehicles_fuels.csv',
    #     'dataset/mapping_and_cost_data.json'
    # )
    fleet = FleetDecarbonization(
            'dataset/cost_profiles.csv',
            'dataset/fuels.csv',
            'dataset/vehicles.csv',
            'dataset/vehicles_fuels.csv',
            'dataset/mapping_and_cost_data.json'
        )

    # Test access to vehicle_bucket_coverage
    year = 2029
    size = 'S3'
    distance = 'D4'
    vehicle_ids = fleet.vehicle_bucket_coverage.get(year, {}).get(size, {}).get(distance, [])
    print(f"Year: {year}, Size: {size}, Distance: {distance}, Vehicle IDs: {vehicle_ids}")


    # # Get the distance buckets vehicles data
    # distance_buckets_vehicles = fleet.get_distance_buckets_vehicles()

    # # Convert the data to JSON and save it to a file
    # with open('distance_buckets_vehicles.json', 'w') as json_file:
    #     json.dump(distance_buckets_vehicles, json_file, indent=4)

if __name__ == "__main__":
    main()
