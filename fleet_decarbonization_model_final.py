import json
import re


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
        self.vehicle_details = data['vehicle_details']
        self.vehicle_bucket_coverage = data['vehicle_bucket_coverage']
        self.vehicle_fuel_consumptions = data['vehicle_fuel_consumptions']
        self.fuels_data = data['fuels_data']

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
        return set(self.vehicle_details.keys())

    def initialize_percentage_values(self):
        self.maintenance_percentages = {
            year: self.cost_percentages[year]['maintenance'] for year in self.cost_percentages}
        self.insurance_percentages = {
            year: self.cost_percentages[year]['insurance'] for year in self.cost_percentages}
        self.resale_percentages = {
            year: self.cost_percentages[year]['resale'] for year in self.cost_percentages}

    def get_vehicle_details(self, vehicle_id):
        match = re.search(r'_(\d{4})$', vehicle_id)
        if not match:
            return None

        purchase_year = int(match.group(1))

        if vehicle_id in self.vehicle_details:
            vehicle_data = self.vehicle_details[vehicle_id]
            return {
                'year': purchase_year,
                'cost': vehicle_data['cost'],
                'size': vehicle_data['size'],
                'distance': vehicle_data['distance'],
                'yearly range': vehicle_data['yearly range']
            }
        return None

    def get_resale_value(self, purchase_cost, age):
        if age == 0:
            age_key = '1'
        elif str(age) in self.resale_percentages:
            age_key = str(age)
        else:
            age_key = max(self.resale_percentages.keys())
        return (purchase_cost * self.resale_percentages[age_key]) + purchase_cost

    def get_insurance_cost(self, purchase_cost, age):
        if age == 0:
            age_key = '1'
        elif str(age) in self.insurance_percentages:
            age_key = str(age)
        else:
            age_key = max(self.insurance_percentages.keys())
        return (purchase_cost * self.insurance_percentages[age_key]) + purchase_cost

    def get_maintenance_cost(self, purchase_cost, age):
        if age == 0:
            age_key = '1'
        elif str(age) in self.maintenance_percentages:
            age_key = str(age)
        else:
            age_key = max(self.maintenance_percentages.keys())
        return (purchase_cost * self.maintenance_percentages[age_key]) + purchase_cost

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

    def calculate_costs(self, individual, current_year, cost_type):
        total_cost = 0
        for vehicle in individual['use']:
            vehicle_id = vehicle['ID']
            num_vehicles = vehicle['Num_Vehicles']
            vehicle_details = self.get_vehicle_details(vehicle_id)
            if vehicle_details:
                purchase_year = int(vehicle_details['year'])
                purchase_cost = float(vehicle_details['cost'])
                age = current_year - purchase_year

                if cost_type == 'insurance':
                    cost = self.get_insurance_cost(purchase_cost, age)
                elif cost_type == 'maintenance':
                    cost = self.get_maintenance_cost(purchase_cost, age)

                total_cost += cost * num_vehicles

        return total_cost

    def calculate_insurance_cost(self, individual, current_year):
        return self.calculate_costs(individual, current_year, 'insurance')

    def calculate_maintenance_cost(self, individual, current_year):
        return self.calculate_costs(individual, current_year, 'maintenance')

    def calculate_resale_value(self, individual, current_year):
        total_resale_value = 0
        for vehicle in individual['sell']:
            vehicle_id = vehicle['ID']
            num_vehicles_to_sell = vehicle['Num_Vehicles']
            vehicle_details = self.get_vehicle_details(vehicle_id)
            if vehicle_details:
                purchase_year = int(vehicle_details['year'])
                purchase_cost = float(vehicle_details['cost'])
                resale_value = self.get_resale_value(
                    purchase_cost, current_year - purchase_year)
                total_resale_value += resale_value * num_vehicles_to_sell

        return total_resale_value

    def calculate_emissions(self, individual):
        total_emissions = 0
        for vehicle in individual['use']:
            vehicle_info = self.get_vehicle_details(vehicle['ID'])
            current_year = vehicle_info['year']
            vehicle_id = vehicle['ID']
            num_vehicles = vehicle['Num_Vehicles']
            distance_per_vehicle = vehicle['Distance_per_vehicle(km)']
            fuel_type = vehicle['Fuel']

            fuel_consumption = self.vehicle_fuel_consumptions[vehicle_id][fuel_type]
            fuel_emission = self.fuels_data[fuel_type][str(
                current_year)]["Emissions (CO2/unit_fuel)"]

            emissions = num_vehicles * distance_per_vehicle * fuel_consumption * fuel_emission
            total_emissions += emissions

        return total_emissions

    def calculate_fuel_cost(self, individual):
        total_cost = 0
        for vehicle in individual['use']:
            vehicle_info = self.get_vehicle_details(vehicle['ID'])
            vehicle_id = vehicle['ID']
            current_year = vehicle_info['year']
            num_vehicles = vehicle['Num_Vehicles']
            distance_covered = vehicle['Distance_per_vehicle(km)']
            fuel_type = vehicle['Fuel']

            fuel_consumption = self.vehicle_fuel_consumptions[vehicle_id][fuel_type]
            fuel_cost_per_unit = self.fuels_data[fuel_type][str(
                current_year)]['Cost ($/unit_fuel)']

            total_cost += float(distance_covered * num_vehicles *
                                fuel_consumption * fuel_cost_per_unit)
        return total_cost

    def update_existing_fleet(self, year, action, vehicle_id, num_vehicles):
        existing_vehicle = next(
            (v for v in self.existing_fleet if v['ID'] == vehicle_id), None)

        if action == 'buy':
            if existing_vehicle:
                existing_vehicle['Num_Vehicles'] += num_vehicles
            else:
                self.existing_fleet.append({
                    'ID': vehicle_id,
                    'Num_Vehicles': num_vehicles,
                    'Purchase_Year': year
                })

        elif action == 'sell':
            if existing_vehicle:
                existing_vehicle['Num_Vehicles'] -= num_vehicles
                if existing_vehicle['Num_Vehicles'] <= 0:
                    self.existing_fleet.remove(existing_vehicle)
            else:
                raise ValueError(
                    f"Cannot sell vehicle {vehicle_id} that is not in the fleet.")

        elif action == 'use':
            if not existing_vehicle:
                raise ValueError(
                    f"Cannot use vehicle {vehicle_id} that is not in the fleet.")

        else:
            raise ValueError(
                f"Invalid action: {action}. Must be 'buy', 'sell', or 'use'.")

        self.existing_fleet = [v for v in self.existing_fleet
                               if (year - v['Purchase_Year']) < 10]

    def check_fleet_meets_demand(self, individual):
        total_distance_demand = self.yearly_demand
        total_distance = 0

        for vehicle in individual['use']:
            vehicle_id = vehicle['ID']
            num_vehicles = vehicle['Num_Vehicles']
            distance_per_vehicle = vehicle['Distance_per_vehicle(km)']
            vehicle_info = self.get_vehicle_details(vehicle_id)

            size = vehicle_info['size']
            current_year = vehicle_info['year']
            distance_bucket = vehicle['Distance_bucket']
            demand = total_distance_demand[str(
                current_year)][size][distance_bucket]
            total_distance += num_vehicles * distance_per_vehicle

            if total_distance > demand:
                return True

        return False

    def buy_vehicles(self, year, vehicle_id, num_vehicles):
        vehicle_details = self.get_vehicle_details(vehicle_id)
        if not vehicle_details:
            raise ValueError(f"Invalid vehicle ID: {vehicle_id}")

        if year != vehicle_details['year']:
            raise ValueError(
                f"Vehicle {vehicle_id} can only be bought in year {vehicle_details['year']}")

        purchase_cost = vehicle_details['cost'] * num_vehicles
        self.update_existing_fleet(year, 'buy', vehicle_id, num_vehicles)

        return purchase_cost

    def sell_vehicles(self, year, vehicle_id, num_vehicles):
        existing_vehicle = next(
            (v for v in self.existing_fleet if v['ID'] == vehicle_id), None)
        if not existing_vehicle:
            raise ValueError(
                f"Cannot sell vehicle {vehicle_id} that is not in the fleet.")
        if num_vehicles > existing_vehicle['Num_Vehicles']:
            raise ValueError(
                f"Cannot sell {num_vehicles} of vehicle {vehicle_id}. Only {existing_vehicle['Num_Vehicles']} available.")
        total_fleet_size = sum(v['Num_Vehicles'] for v in self.existing_fleet)
        if num_vehicles > total_fleet_size * self.max_sell_percentage:
            raise ValueError(
                f"Cannot sell more than {self.max_sell_percentage * 100}% of the fleet in a year.")

        purchase_year = existing_vehicle['Purchase_Year']
        vehicle_age = year - purchase_year
        vehicle_details = self.get_vehicle_details(vehicle_id)
        resale_value = self.get_resale_value(
            vehicle_details['cost'], vehicle_age) * num_vehicles
        self.update_existing_fleet(year, 'sell', vehicle_id, num_vehicles)

        return resale_value

    def use_vehicles(self, year, vehicle_id, num_vehicles, distance_per_vehicle, fuel_type, distance_bucket):
        existing_vehicle = next(
            (v for v in self.existing_fleet if v['ID'] == vehicle_id), None)
        if not existing_vehicle:
            raise ValueError(
                f"Cannot use vehicle {vehicle_id} that is not in the fleet.")
        if num_vehicles > existing_vehicle['Num_Vehicles']:
            raise ValueError(
                f"Cannot use {num_vehicles} of vehicle {vehicle_id}. Only {existing_vehicle['Num_Vehicles']} available.")
        vehicle_details = self.get_vehicle_details(vehicle_id)

        if self.distance_buckets_mapping[vehicle_details['distance']] < self.distance_buckets_mapping[distance_bucket]:
            raise ValueError(
                f"Vehicle {vehicle_id} cannot cover distance bucket {distance_bucket}")
        if distance_per_vehicle > vehicle_details['yearly range']:
            raise ValueError(
                f"Distance per vehicle ({distance_per_vehicle}) exceeds yearly range ({vehicle_details['yearly range']})")

        fuel_consumption = self.vehicle_fuel_consumptions[vehicle_id][fuel_type]
        fuel_cost_per_unit = self.fuels_data[fuel_type][str(
            year)]['Cost ($/unit_fuel)']
        total_fuel_cost = num_vehicles * distance_per_vehicle * \
            fuel_consumption * fuel_cost_per_unit

        fuel_emission = self.fuels_data[fuel_type][str(
            year)]["Emissions (CO2/unit_fuel)"]
        total_emissions = num_vehicles * distance_per_vehicle * \
            fuel_consumption * fuel_emission

        self.update_existing_fleet(year, 'use', vehicle_id, num_vehicles)
        return total_fuel_cost, total_emissions