import json
import re
import pandas as pd


class FleetOptimization:
    def __init__(self, json_file_path):
        self.hard_constraint_penalty = 1000

        # Load the JSON file
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        # Initialize attributes from JSON data
        self.size_mapping = data['size_mapping']
        self.distance_mapping = data['distance_mapping']
        self.distance_buckets_mapping = data['distance_buckets_mapping']
        self.cost_percentages = data['cost_percentages']
        self.carbon_emissions = data['carbon_emissions']
        self.yearly_demand = data['yearly_demand']
        self.vehicles_details = data['vehicles_details']
        self.vehicle_bucket_coverage = data['vehicle_bucket_coverage']
        self.vehicles_fuel_consumptions = pd.DataFrame(
            data['vehicle_fuel_consumptions'])
        self.fuels_data = pd.DataFrame(data['fuels_data'])

        # One year 12 models of vehicles
        self.vehicle_ids = self._extract_vehicle_ids()
        self.years = list(range(2023, 2039))
        self.size_buckets = list(self.size_mapping.keys())
        self.distance_buckets = list(self.distance_mapping.keys())
        self.actions = ['buy', 'sell', 'use']

        # at most 20% of vehicles can be sold every year
        self.max_sell_percentage = 0.2

        # Initialize percentage values for maintenance, insurance, and resale
        self.initialize_percentage_values()

    def _extract_vehicle_ids(self):
        return set(self.vehicles_details.keys())

    def initialize_percentage_values(self):
        self.maintenance_percentages = {
            year: self.cost_percentages[year]['maintenance'] for year in self.cost_percentages}
        self.insurance_percentages = {
            year: self.cost_percentages[year]['insurance'] for year in self.cost_percentages}
        self.resale_percentages = {
            year: self.cost_percentages[year]['resale'] for year in self.cost_percentages}
        
# Example usage
json_file_path = 'dataset/mapping_and_cost_data.json'
fleet_optimization = FleetOptimization(json_file_path)

print(type(fleet_optimization.maintenance_percentages['1']))