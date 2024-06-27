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
        self.vehicles_fuel_consumptions = pd.DataFrame(data['vehicle_fuel_consumptions'])
        self.fuels_data = pd.DataFrame(data['fuels_data'])

        # Extract vehicle IDs
        self.vehicle_ids = self._extract_vehicle_ids()
        self.years = list(range(2023, 2039))
        self.size_buckets = list(self.size_mapping.keys())
        self.distance_buckets = list(self.distance_mapping.keys())
        self.actions = ['buy', 'sell', 'use']

        # At most 20% of vehicles can be sold every year
        self.max_sell_percentage = 0.2

        # Initialize percentage values for maintenance, insurance, and resale
        self.initialize_percentage_values()

        # Initialize existing fleet list
        self.existing_fleet = []

    def _extract_vehicle_ids(self):
        return set(self.vehicles_details.keys())

    def initialize_percentage_values(self):
        self.maintenance_percentages = {
            year: self.cost_percentages[year]['maintenance'] for year in self.cost_percentages}
        self.insurance_percentages = {
            year: self.cost_percentages[year]['insurance'] for year in self.cost_percentages}
        self.resale_percentages = {
            year: self.cost_percentages[year]['resale'] for year in self.cost_percentages}

    def get_vehicle_details(self, vehicle_id):
        # Extract the year from the vehicle_id using regex
        match = re.search(r'_(\d{4})$', vehicle_id)
        if not match:
            return None

        purchase_year = int(match.group(1))

        # Retrieve vehicle details from internal JSON data
        if vehicle_id in self.vehicles_details:
            vehicle_data = self.vehicles_details[vehicle_id]
            return {
                'year': purchase_year,
                'cost': vehicle_data['cost'],
                'size': vehicle_data['size'],
                'distance': vehicle_data['distance'],
                'yearly range': vehicle_data['yearly range']
            }
        return None

    def get_resale_value(self, purchase_cost, age):
        return (purchase_cost * self.resale_percentages[str(age)]) + purchase_cost

    def get_maintenance_cost(self, purchase_cost, age):
        return (purchase_cost * self.maintenance_percentages[str(age)]) + purchase_cost

    def get_insurance_cost(self, purchase_cost, age):
        return (purchase_cost * self.insurance_percentages[str(age)]) + purchase_cost

    def calculate_buy_cost(self, individual):
        total_cost = 0
        for vehicle in individual['buy']:
            vehicle_id = vehicle['ID']
            num_vehicles = vehicle['Num_Vehicles']
            vehicle_details = self.get_vehicle_details(vehicle_id)
            if vehicle_details:
                purchase_cost = float(vehicle_details['cost'])
                total_cost += purchase_cost * num_vehicles

        return total_cost

    def calculate_insurance_cost(self, individual, current_year):
        total_cost = 0
        for vehicle in individual['use']:
            vehicle_id = vehicle['ID']
            num_vehicles = vehicle['Num_Vehicles']
            vehicle_details = self.get_vehicle_details(vehicle_id)
            if vehicle_details:
                purchase_year = int(vehicle_details['year'])
                purchase_cost = float(vehicle_details['cost'])
                insurance_cost = self.get_insurance_cost(purchase_cost, current_year - purchase_year)
                total_cost += insurance_cost * num_vehicles
        return total_cost

    def calculate_maintenance_cost(self, individual, current_year):
        total_cost = 0
        for vehicle in individual['use']:
            vehicle_id = vehicle['ID']
            num_vehicles = vehicle['Num_Vehicles']
            vehicle_details = self.get_vehicle_details(vehicle_id)
            if vehicle_details:
                purchase_year = int(vehicle_details['year'])
                purchase_cost = float(vehicle_details['cost'])
                maintenance_cost = self.get_maintenance_cost(purchase_cost, current_year - purchase_year)
                total_cost += maintenance_cost * num_vehicles
        return total_cost

    def calculate_resale_value(self, individual, current_year):
        total_resale_value = 0
        for vehicle in individual['sell']:
            vehicle_id = vehicle['ID']
            num_vehicles_to_sell = vehicle['Num_Vehicles']
            vehicle_details = self.get_vehicle_details(vehicle_id)
            if vehicle_details:
                purchase_year = int(vehicle_details['year'])
                purchase_cost = float(vehicle_details['cost'])
                resale_value = self.get_resale_value(purchase_cost, current_year - purchase_year)
                total_resale_value += resale_value * num_vehicles_to_sell

        return total_resale_value

    def calculate_emissions(self, individual, year):
        total_emissions = 0
        for vehicle in individual['use']:
            vehicle_id = vehicle['ID']
            num_vehicles = vehicle['Num_Vehicles']
            distance_per_vehicle = vehicle['Distance_per_vehicle(km)']
            fuel_type = vehicle['Fuel']

            # Retrieve fuel consumption
            fuel_consumption = 1

            # Calculate emissions for the current vehicle in use
            emissions = num_vehicles * distance_per_vehicle * fuel_consumption 
            total_emissions += emissions

        return total_emissions

    def update_existing_fleet(self, vehicle_id, num_vehicles):
        for vehicle in self.existing_fleet:
            if vehicle['ID'] == vehicle_id:
                vehicle['Num_Vehicles'] += num_vehicles
                return
        self.existing_fleet.append({'ID': vehicle_id, 'Num_Vehicles': num_vehicles})
