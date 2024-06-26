import pandas as pd
import random
import json
import os


class FleetDecarbonization:

    hard_constraint_penalty = 1000

    def __init__(self, cost_profiles_file, fuels_file, vehicles_file, vehicles_fuels_file, mapping_data_file, leftover_vehicles_file):
        # Load data
        self.cost_profiles = pd.read_csv(cost_profiles_file)
        self.fuels = pd.read_csv(fuels_file)
        self.vehicles = pd.read_csv(vehicles_file)
        self.vehicles_fuels = pd.read_csv(vehicles_fuels_file)

        # Load mapping data from JSON file
        with open(mapping_data_file, 'r') as f:
            mapping_data = json.load(f)

        self.leftover_vehicles_file = leftover_vehicles_file
        self.all_previous_vehicles_leftover = self.load_from_json(
            self.leftover_vehicles_file)

        # Set attributes from JSON data
        self.distance_mapping = mapping_data['distance_mapping']
        self.size_mapping = mapping_data['size_mapping']
        self.cost_percentages = {
            int(k): v for k, v in mapping_data['cost_percentages'].items()}
        self.carbon_emissions_dict = {
            int(k): v for k, v in mapping_data['carbon_emissions_dict'].items()}
        self.yearly_demand = {int(k): {sk: {dk: int(dv) for dk, dv in sv.items(
        )} for sk, sv in v.items()} for k, v in mapping_data['yearly_demand'].items()}
        self.vehicle_bucket_coverage = {int(k): {sk: {dk: v for dk, v in sv.items(
        )} for sk, sv in v.items()} for k, v in mapping_data['vehicle_bucket_coverage'].items()}
        self.vehicle_fuel_types = mapping_data['vehicle_fuel_types']
        self.distance_buckets_map = mapping_data['distance_buckets_mapping']

        # Initialize other attributes
        self.size_buckets = list(self.size_mapping.keys())
        self.distance_buckets = list(self.distance_mapping.keys())
        self.years = list(range(2023, 2039))
        self.action = ['buy', 'sell', 'use']
        self.current_year = self.years[0]  

    def __len__(self):
        return len(self.action)

    def load_from_json(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, 'r') as json_file:
                try:
                    return json.load(json_file)
                except json.JSONDecodeError:
                    return {}
        else:
            return {}

    def get_vehicle_details(self, vehicle_id):
        vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
        if vehicle.empty:
            return None, None, None, None

        size = vehicle['Size'].values[0]
        distance = vehicle['Distance'].values[0]
        purchase_year = int(vehicle['Year'].values[0])
        purchase_cost = int(vehicle['Cost ($)'].values[0])
        return size, distance, purchase_year, purchase_cost

    def get_vehicle_info(self, vehicle_id):
        size, distance, _, _ = self.get_vehicle_details(vehicle_id)
        return size, distance

    def get_resale_value(self, purchase_cost, year):
        if year in self.cost_percentages:
            return purchase_cost * self.cost_percentages[year]['resale']
        return purchase_cost * 0.30  # default value for years beyond 10

    def get_insurance_cost(self, purchase_cost, year):
        if year in self.cost_percentages:
            return purchase_cost * self.cost_percentages[year]['insurance']
        return purchase_cost * 0.14  # default value for years beyond 10

    def get_maintenance_cost(self, purchase_cost, year):
        if year in self.cost_percentages:
            return purchase_cost * self.cost_percentages[year]['maintenance']
        return purchase_cost * 0.19  # default value for years beyond 10

    def calculate_buy_cost(self, individual):
        total_cost = 0
        for vehicle in individual['buy']:
            vehicle_id = vehicle['ID']
            num_vehicles = vehicle['Num_Vehicles']
            _, _, _, cost_per_vehicle = self.get_vehicle_details(vehicle_id)
            total_cost += float(cost_per_vehicle * num_vehicles)
        return total_cost

    def calculate_insurance_cost(self, individual):
        total_cost = 0
        for vehicle in individual['use']:
            vehicle_id = vehicle['ID']
            num_vehicles = vehicle['Num_Vehicles']
            _, _, purchase_year, purchase_cost = self.get_vehicle_details(
                vehicle_id)
            insurance_cost = self.get_insurance_cost(
                purchase_cost, self.current_year - purchase_year)
            total_cost += float(insurance_cost * num_vehicles)
        return total_cost

    def calculate_maintenance_cost(self, individual):
        total_cost = 0
        for vehicle in individual['buy']:
            vehicle_id = vehicle['ID']
            num_vehicles = vehicle['Num_Vehicles']
            _, _, purchase_year, purchase_cost = self.get_vehicle_details(
                vehicle_id)
            maintenance_cost = self.get_maintenance_cost(
                purchase_cost, self.current_year - purchase_year)
            total_cost += float(maintenance_cost * num_vehicles)
        return total_cost

    def calculate_fuel_cost(self, individual):
        total_cost = 0
        for vehicle in individual['use']:
            vehicle_id = vehicle['ID']
            num_vehicles = vehicle['Num_Vehicles']
            distance_covered = vehicle['Distance_per_vehicle']
            fuel_type = vehicle['Fuel']
            fuel_consumption = float(self.vehicles_fuels.loc[(self.vehicles_fuels['ID'] == vehicle_id) & (
                self.vehicles_fuels['Fuel'] == fuel_type), 'Consumption (unit_fuel/km)'].values[0])
            fuel_cost_per_unit = self.fuels[(self.fuels['Fuel'] == fuel_type) & (
                self.fuels['Year'] == self.current_year)]['Cost ($/unit_fuel)'].values[0]
            total_cost += float(distance_covered * num_vehicles *
                                fuel_consumption * fuel_cost_per_unit)
        return total_cost

    def calculate_selling_profit(self, individual):
        total_profit = 0
        for vehicle in individual['sell']:
            vehicle_id = vehicle['ID']
            num_vehicles_to_sell = vehicle['Num_Vehicles']
            _, _, purchase_year, purchase_cost = self.get_vehicle_details(
                vehicle_id)
            resale_value = self.get_resale_value(
                purchase_cost, self.current_year - purchase_year)
            total_profit += float(resale_value * num_vehicles_to_sell)
        return total_profit

    def calculate_carbon_emission(self, individual):
        total_emission = 0
        for vehicle in individual['use']:
            vehicle_id = vehicle['ID']
            num_vehicles = vehicle['Num_Vehicles']
            distance_covered = vehicle['Distance_per_vehicle']
            fuel_type = vehicle['Fuel']
            fuel_consumption = float(self.vehicles_fuels.loc[(self.vehicles_fuels['ID'] == vehicle_id) & (
                self.vehicles_fuels['Fuel'] == fuel_type), 'Consumption (unit_fuel/km)'].values[0])
            carbon_emission_per_unit = self.fuels[(self.fuels['Fuel'] == fuel_type) & (
                self.fuels['Year'] == self.current_year)]['Emissions (CO2/unit_fuel)'].values[0]
            total_emission += float(distance_covered * num_vehicles *
                                    fuel_consumption * carbon_emission_per_unit)
        return total_emission

    ###### Hard constraints ######

    def check_purchase_year(self, vehicle_id, purchase_year):
        vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
        if vehicle.empty:
            return False, f"Vehicle ID {vehicle_id} not found."

        model_year = int(vehicle_id.split('_')[-1])
        if purchase_year != model_year:
            return False, f"Vehicle ID {vehicle_id} can only be bought in the year {model_year}."
        return True, ""

    def check_vehicle_lifetime(self, vehicle_id, current_year):
        vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
        if vehicle.empty:
            return False, f"Vehicle ID {vehicle_id} not found."

        purchase_year = int(vehicle_id.split('_')[-1])
        if current_year > purchase_year + 10:
            return False, f"Vehicle ID {vehicle_id} must be sold by the end of {purchase_year + 10}."
        return True, ""

    def sell_violation(self, fleet):
        total_vehicles = sum(vehicle['Num_Vehicles'] for vehicle in fleet)
        total_sold = sum(vehicle['Num_Vehicles_Sold'] for vehicle in fleet)

        if total_sold > total_vehicles:
            return True
        if total_sold > 0.20 * total_vehicles:
            return True
        return False

    def use_violation(self, fleet):
        total_vehicles = sum(vehicle['Num_Vehicles'] for vehicle in fleet)
        total_used = sum(vehicle['Num_Vehicles_Used'] for vehicle in fleet)

        if total_used > total_vehicles:
            return True
        return False

    def distance_limit_violation(self, fleet):
        violations = 0
        for vehicle in fleet['use']:
            distance_bucket = vehicle['Distance_bucket']
            distance = vehicle['Distance_per_vehicle']
            max_distance = self.distance_mapping[distance_bucket]

            if distance > max_distance:
                violations += 1

        return violations

    def calculate_total_distance(self, fleet):
        total_distance = {year: {size: {distance: 0 for distance in self.distance_buckets}
                                 for size in self.size_buckets} for year in self.carbon_emissions_dict.keys()}
        for plan in fleet:
            vehicle_id = plan['ID']
            num_vehicles = plan['Num_Vehicles']
            distance_covered = plan['Distance_per_vehicle']

            for year in self.years:
                for size in self.size_buckets:
                    for distance in self.distance_buckets:
                        if vehicle_id in self.distance_buckets_vehicles[year][size][distance]:
                            total_distance[year][size][distance] += distance_covered * num_vehicles

        return total_distance

    def verify_distance_meets_demand(self):
        if not hasattr(self, 'total_distance'):
            # Ensure this method is called to initialize total_distance
            self.total_distance = self.calculate_total_distance(self.vehicles)
        for year in self.years:
            for size in self.size_buckets:
                for distance in self.distance_buckets:
                    if self.total_distance[year][size][distance] < self.yearly_demand[year][size][distance]:
                        return False

        return True

    def exceed_carbon_emission_limit_violation(self, individual):
        total_emission = self.calculate_carbon_emission(individual)
        carbon_limit = self.carbon_emissions_dict[self.current_year]

        if total_emission > carbon_limit:
            return True
        return False

    # Use on hof. It updates the sold vehicle for other years and create a new entry for the current year.

    def get_current_leftover_vehicles(self, current_individual):

        for vehicle in current_individual['buy']:
            current_year = vehicle['Year']
            if current_year not in self.all_previous_vehicles_leftover:
                self.all_previous_vehicles_leftover[current_year] = {}

            vehicle_id = vehicle['ID']
            fuel_type = vehicle['Fuel']
            distance_bucket = vehicle['Distance_bucket']
            num_vehicles_bought = vehicle['Num_Vehicles']

            if vehicle_id not in self.all_previous_vehicles_leftover[current_year]:
                self.all_previous_vehicles_leftover[current_year][vehicle_id] = {
                }

            if fuel_type not in self.all_previous_vehicles_leftover[current_year][vehicle_id]:
                self.all_previous_vehicles_leftover[current_year][vehicle_id][fuel_type] = {
                }

            if distance_bucket not in self.all_previous_vehicles_leftover[current_year][vehicle_id]:
                self.all_previous_vehicles_leftover[current_year][vehicle_id][
                    fuel_type][distance_bucket] = num_vehicles_bought

        for vehicle in current_individual['sell']:
            current_year = vehicle['Year']
            vehicle_id = vehicle['ID']
            fuel_type = vehicle['Fuel']
            distance_bucket = vehicle['Distance_bucket']
            num_vehicles_sold = vehicle['Num_Vehicles']

            self.all_previous_vehicles_leftover[current_year][vehicle_id][
                fuel_type][distance_bucket] -= num_vehicles_sold

        self.cleanup_all_vehicles_leftover()
        self.update_json_with_new_data(
            self.all_previous_vehicles_leftover, self.leftover_vehicles_file)

    def cleanup_all_vehicles_leftover(self):
        # Iterate through all years in self.all_previous_vehicles_leftover
        for year in list(self.all_previous_vehicles_leftover.keys()):
            vehicles_leftover = self.all_previous_vehicles_leftover[year]

            # Remove distance buckets with zero values
            for vehicle_id in list(vehicles_leftover.keys()):
                for fuel_type in list(vehicles_leftover[vehicle_id].keys()):
                    distance_buckets = vehicles_leftover[vehicle_id][fuel_type]
                    for distance_bucket in list(distance_buckets.keys()):
                        if distance_buckets[distance_bucket] == 0:
                            del distance_buckets[distance_bucket]

                    # Remove fuel types with no distance buckets
                    if not distance_buckets:
                        del vehicles_leftover[vehicle_id][fuel_type]

                # Remove vehicle IDs with no fuel types
                if not vehicles_leftover[vehicle_id]:
                    del vehicles_leftover[vehicle_id]

            # Remove the year if it has no vehicle IDs
            if not vehicles_leftover:
                del self.all_previous_vehicles_leftover[year]

        # Can remove but I just want to know when it ends hehe
        return self.all_previous_vehicles_leftover

    # Get a list of possible vehicles to be populated on the chromosome
    def get_previous_leftover_vehicles(self, current_year):
        vehicle_details = []

        # Ensure the range is within valid bounds
        min_year = min(self.all_previous_vehicles_leftover.keys(),
                       default=current_year)
        start_year = max(current_year - 9, min_year)

        for year in range(start_year, current_year + 1):
            if year in self.all_previous_vehicles_leftover:
                vehicles = self.all_previous_vehicles_leftover[year]
                for vehicle_id, fuel_data in vehicles.items():
                    for fuel_type, distance_buckets in fuel_data.items():
                        for distance_bucket, num_vehicles in distance_buckets.items():
                            if num_vehicles > 0:  # Only include non-zero values
                                vehicle_details.append({
                                    'Vehicle_ID': vehicle_id,
                                    'Fuel_Type': fuel_type,
                                    'Distance_Bucket': distance_bucket,
                                    'Num_Vehicles': num_vehicles
                                })

        return vehicle_details

    def create_individual(self):
        """
        The current vehicle_id_list should only be used for 'buy' only.
        Need to combine vehicle_id_list with the one from self.get_previous_leftover_vehicles.
        Then, the combined one is used for use and sell <- not including the distance or number of vehicles <- these are needed to be used as limit for random.int
        """
        individual = {'buy': [], 'sell': [], 'use': []}
        vehicles_bought = {}

        for action in self.action:
            # Populate current year vehicle into buy, sell, and use
            for size in self.size_buckets:
                for distance in self.distance_buckets:
                    vehicle_id_list = self.vehicles[
                        (self.vehicles['Year'] == self.current_year) &
                        (self.vehicles['Size'] == size) &
                        (self.vehicles['Distance'] == distance)
                    ]['ID'].tolist()
                    vehicle_buckets = self.distance_buckets_map[distance]

                    for vehicle_id in vehicle_id_list:
                        fuel_type = self.vehicle_fuel_types[vehicle_id]
                        if vehicle_id not in vehicles_bought:
                            vehicles_bought[vehicle_id] = {}

                        for fuel in fuel_type:
                            if fuel not in vehicles_bought[vehicle_id]:
                                vehicles_bought[vehicle_id][fuel] = {}

                            for d_bucket in vehicle_buckets:
                                if d_bucket not in vehicles_bought[vehicle_id][fuel]:
                                    vehicles_bought[vehicle_id][fuel][d_bucket] = {
                                    }

                                if action == 'buy':
                                    num_vehicles = random.randint(0, 20)
                                    vehicles_bought[vehicle_id][fuel][d_bucket] = num_vehicles

                                elif action == 'sell' or action == 'use':
                                    # Since buy is populated first, no need to check
                                    max_sell_use = vehicles_bought[vehicle_id][fuel][d_bucket]
                                    num_vehicles = random.randint(
                                        0, max_sell_use)
                                else:
                                    print(f'Invalid action: {action}')

                                if action == 'buy' or action == 'sell':
                                    distance_covered = 0
                                else:
                                    # Distance is the yearly one so do not use the distance mapping
                                    # Regardless of distance bucket, the same vehicle model in different year has the same yearly range
                                    max_distance = int(self.vehicles.loc[
                                        (self.vehicles['ID'] == vehicle_id) &
                                        (self.vehicles['Year']
                                         == self.current_year),
                                        'Yearly range (km)'
                                    ].values[0])
                                    distance_covered = random.randint(
                                        0, max_distance + 1)

                                # Ensure distance_covered is 0 if num_vehicles is 0
                                if num_vehicles == 0:
                                    distance_covered = 0

                                individual[action].append({
                                    'ID': vehicle_id,
                                    'Num_Vehicles': num_vehicles,
                                    'Distance_per_vehicle': distance_covered,
                                    'Fuel': fuel,
                                    'Distance_bucket': d_bucket,
                                    'Year': self.current_year
                                })

            # Populate leftover vehicles for use and sell
            if action == 'sell' or action == 'use':
                for year, vehicle_data in self.all_previous_vehicles_leftover.items():
                    for vehicle_id2, fuel_data in vehicle_data.items():
                        for fuel2, distance_data in fuel_data.items():
                            for d_bucket2, num_vehicles_left in distance_data.items():
                                num_vehicles2 = random.randint(
                                    0, num_vehicles_left)

                                if action == 'sell':
                                    distance_covered2 = 0
                                elif action == 'use':
                                    max_distance = int(self.vehicles.loc[
                                        (self.vehicles['ID'] == vehicle_id2),
                                        'Yearly range (km)'
                                    ].values[0])
                                    distance_covered2 = random.randint(
                                        0, max_distance + 1)
                                else:
                                    print('Invalid action')

                                if num_vehicles2 == 0:
                                    distance_covered2 = 0

                                individual[action].append({
                                    'ID': vehicle_id2,
                                    'Num_Vehicles': num_vehicles2,
                                    'Distance_per_vehicle': distance_covered2,
                                    'Fuel': fuel2,
                                    'Distance_bucket': d_bucket2,
                                    'Year': year
                                })

        return individual

    def load_from_json(self, filename):
        """
        Load existing data from a JSON file.
        """
        if os.path.exists(filename):
            with open(filename, 'r') as json_file:
                try:
                    data = json.load(json_file)
                except json.JSONDecodeError:
                    data = {}
        else:
            data = {}
        return data

    def save_to_json(self, data, filename):
        """
        Save data to a JSON file.
        """
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def update_json_with_new_data(self, new_data, filename):
        """
        Update the JSON file with new data.
        """
        existing_data = self.load_from_json(filename)
        existing_data.update(new_data)
        self.save_to_json(existing_data, filename)
