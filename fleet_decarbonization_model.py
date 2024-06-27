import json
import random
import os


class FleetOptimization:
    def __init__(self, json_file_path, left_over_file):
        # Initialize all previous vehicles leftover
        self.leftover_vehicles_file = left_over_file
        self.all_previous_vehicles_leftover = self.load_from_json(
            self.leftover_vehicles_file)

    def get_demand(self, fleet):
        total_demand = {}
        satisfied_demand_vehicles = {}

        # Initialize the total demand structure
        for size in self.size_buckets:
            total_demand[size] = {}
            for distance in self.distance_buckets:
                total_demand[size][distance] = 0

        # Create a hierarchy of distance buckets
        distance_hierarchy = {'D1': 1, 'D2': 2, 'D3': 3, 'D4': 4}

        # Process the fleet
        for vehicle in fleet['use']:
            vehicle_id = vehicle['ID']
            fuel_type = vehicle['Fuel']
            vehicle_distance_bucket = vehicle['Distance_bucket']
            num_vehicles = vehicle['Num_Vehicles']
            distance_per_vehicle = vehicle['Distance_per_vehicle']
            vehicle_size = vehicle_id.split('_')[1]

            if vehicle_id not in satisfied_demand_vehicles:
                satisfied_demand_vehicles[vehicle_id] = {}

            if fuel_type not in satisfied_demand_vehicles[vehicle_id]:
                satisfied_demand_vehicles[vehicle_id][fuel_type] = []

            # Check for the size buckets this vehicle can satisfy
            for size in self.size_buckets:
                for distance in self.distance_buckets:
                    vehicles_to_satisfy = self.vehicle_bucket_coverage[self.current_year][size][distance]
                    if vehicle_id in vehicles_to_satisfy and distance_hierarchy[vehicle_distance_bucket] >= distance_hierarchy[distance] and vehicle_distance_bucket not in satisfied_demand_vehicles[vehicle_id][fuel_type]:
                        current_demand = self.yearly_demand[self.current_year][size][distance]
                        if total_demand[size][distance] < current_demand:
                            contribution = num_vehicles * distance_per_vehicle

                            total_demand[size][distance] += contribution

                            satisfied_demand_vehicles[vehicle_id][fuel_type].append(
                                vehicle_distance_bucket)

                            if total_demand[size][distance] >= current_demand:
                                break
        return total_demand

    def check_demand_met(self, fleet):
        violations = 0
        all_demands = self.get_demand(fleet)
        for size in self.size_buckets:
            for distance in self.distance_buckets:
                year_distance_demand = self.yearly_demand[self.current_year][size][distance]
                current_distance = all_demands[size][distance]
                if current_distance < year_distance_demand:
                    violations += 1

        return violations

    def calculate_fuel_cost(self, individual, current_year):
        total_cost = 0
        for vehicle in individual['use']:
            vehicle_id = vehicle['ID']
            num_vehicles = vehicle['Num_Vehicles']
            distance_covered = vehicle['Distance_per_vehicle']
            fuel_type = vehicle['Fuel']
            fuel_consumption = float(self.vehicles_fuels[(self.vehicles_fuels['ID'] == vehicle_id) &
                                                         (self.vehicles_fuels['Fuel'] == fuel_type)]['Consumption (unit_fuel/km)'].values[0])
            fuel_cost_per_unit = float(self.fuels[(self.fuels['Fuel'] == fuel_type) &
                                                  (self.fuels['Year'] == str(current_year))]['Cost ($/unit_fuel)'].values[0])
            total_cost += float(distance_covered * num_vehicles *
                                fuel_consumption * fuel_cost_per_unit)
        return total_cost

    def create_individual(self):
        individual = {'buy': [], 'sell': [], 'use': []}
        vehicles_bought = {}
        total_distances_dict = {}
        for action in self.actions:
            # Populate current year vehicle into buy, sell, and use
            for size in self.size_buckets:
                for distance in self.distance_buckets:
                    vehicle_id_list = self.vehicles_fuels[(self.vehicles_fuels['Year'] == self.current_year) &
                                                          (self.vehicles_fuels['Size'] == size) &
                                                          (self.vehicles_fuels['Distance'] == distance)]['ID'].tolist()
                    vehicle_buckets = self.distance_buckets_mapping[distance]

                    for vehicle_id in vehicle_id_list:
                        fuel_type = self.vehicles_fuels[self.vehicles_fuels['ID'] == vehicle_id]['Fuel'].tolist(
                        )
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
                                    num_vehicles = random.randint(0, 10)
                                    vehicles_bought[vehicle_id][fuel][d_bucket] = num_vehicles
                                    individual[action].append({'ID': vehicle_id, 'Num_Vehicles': num_vehicles,
                                                               'Distance_per_vehicle': 0, 'Fuel': fuel,
                                                               'Distance_bucket': d_bucket, 'Year': self.current_year})

                                elif action in ['sell', 'use']:
                                    if vehicle_id in vehicles_bought and fuel in vehicles_bought[vehicle_id] and d_bucket in vehicles_bought[vehicle_id][fuel]:
                                        max_sell_use = vehicles_bought[vehicle_id][fuel][d_bucket]
                                        num_vehicles = random.randint(
                                            0, max_sell_use)
                                        vehicles_bought[vehicle_id][fuel][d_bucket] -= num_vehicles

                                        distance_covered = 0
                                        if action == 'use' and num_vehicles > 0:
                                            yearly_limit = int(
                                                self.vehicles_fuels[self.vehicles_fuels['ID'] == vehicle_id]['Yearly range (km)'].values[0])
                                            if vehicle_id not in total_distances_dict:
                                                total_distances_dict[vehicle_id] = 0
                                            max_distance = (
                                                yearly_limit - total_distances_dict[vehicle_id]) // num_vehicles
                                            distance_covered = random.randint(
                                                0, max_distance)
                                            new_total_distance = total_distances_dict[vehicle_id] + (
                                                distance_covered * num_vehicles)

                                            if new_total_distance <= yearly_limit:
                                                total_distances_dict[vehicle_id] = new_total_distance
                                            else:
                                                leftover_distance = yearly_limit - \
                                                    total_distances_dict[vehicle_id]
                                                distance_per_vehicle = leftover_distance // num_vehicles
                                                distance_covered = distance_per_vehicle
                                                total_distances_dict[vehicle_id] = yearly_limit

                                        individual[action].append({'ID': vehicle_id, 'Num_Vehicles': num_vehicles,
                                                                   'Distance_per_vehicle': distance_covered, 'Fuel': fuel,
                                                                   'Distance_bucket': d_bucket, 'Year': self.current_year})

            # Populate leftover vehicles for use and sell
            if action in ['sell', 'use']:
                for year, vehicle_data in self.all_previous_vehicles_leftover.items():
                    for vehicle_id2, fuel_data in vehicle_data.items():
                        for fuel2, distance_data in fuel_data.items():
                            for d_bucket2, num_vehicles_left in distance_data.items():
                                num_vehicles2 = random.randint(
                                    0, num_vehicles_left)

                                distance_covered2 = 0
                                if action == 'use' and num_vehicles2 > 0:
                                    yearly_limit2 = int(
                                        self.vehicles_fuels[self.vehicles_fuels['ID'] == vehicle_id2]['Yearly range (km)'].values[0])
                                    if vehicle_id2 not in total_distances_dict:
                                        total_distances_dict[vehicle_id2] = 0
                                    max_distance2 = (
                                        yearly_limit2 - total_distances_dict[vehicle_id2]) // num_vehicles2
                                    distance_covered2 = random.randint(
                                        0, max_distance2)
                                    new_total_distance2 = total_distances_dict[vehicle_id2] + (
                                        distance_covered2 * num_vehicles2)

                                    if new_total_distance2 <= yearly_limit2:
                                        total_distances_dict[vehicle_id2] = new_total_distance2
                                    else:
                                        leftover_distance2 = yearly_limit2 - \
                                            total_distances_dict[vehicle_id2]
                                        distance_per_vehicle2 = leftover_distance2 // num_vehicles2
                                        distance_covered2 = distance_per_vehicle2
                                        total_distances_dict[vehicle_id2] = yearly_limit2

                                individual[action].append({'ID': vehicle_id2, 'Num_Vehicles': num_vehicles2,
                                                           'Distance_per_vehicle': distance_covered2, 'Fuel': fuel2,
                                                           'Distance_bucket': d_bucket2, 'Year': year})

        return individual

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

            if distance_bucket not in self.all_previous_vehicles_leftover[current_year][vehicle_id][fuel_type]:
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

    def cleanup_all_vehicles_leftover(self):
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

        return self.all_previous_vehicles_leftover

    def get_previous_leftover_vehicles(self, current_year):
        vehicle_details = []
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

    def sum_nested_dict(self, d):
        total_sum = 0
        for key, value in d.items():
            if isinstance(value, dict):
                total_sum += self.sum_nested_dict(value)
            else:
                total_sum += value
        return total_sum

    def evaluate_chromosome(self, chromosome):
        total_cost = 0
        total_emissions = 0
        demand_fulfilled = True  # Initialize demand fulfillment status

        for year, actions in enumerate(chromosome, start=2023):
            self.current_year = year
            total_cost += self.calculate_buy_cost(actions)
            total_cost += self.calculate_insurance_cost(
                actions, self.current_year)
            total_cost += self.calculate_maintenance_cost(
                actions, self.current_year)
            total_cost += self.calculate_fuel_cost(actions, self.current_year)
            total_selling_profit = self.calculate_selling_profit(
                actions, self.current_year)
            total_cost -= total_selling_profit  # Selling profit reduces the total cost

            # Get yearly demand for each size and distance bucket
            yearly_demand = self.yearly_demand.get(str(year), {})
            demand_coverage = {size: {
                bucket: 0 for bucket in self.distance_buckets} for size in self.size_buckets}

            for action in actions['use']:
                vehicle_id = action['ID']
                num_vehicles = action['Num_Vehicles']
                distance_per_vehicle = action['Distance_per_vehicle']
                size = self.get_vehicle_details(vehicle_id)['Size']
                distance_bucket = action['Distance_bucket']

                if size in demand_coverage and distance_bucket in demand_coverage[size]:
                    # check if each vehicle fulfills its demand coverage
                    demand_coverage[size][distance_bucket] += num_vehicles * \
                        distance_per_vehicle

                total_emissions += self.calculate_emissions(
                    year, vehicle_id, num_vehicles, distance_per_vehicle)

            # Check if total emissions exceed the carbon emission limit for the year
            if total_emissions > self.carbon_emissions_dict[str(year)]:
                total_cost += (total_emissions -
                               self.carbon_emissions_dict[str(year)]) * self.hard_constraint_penalty

            # Check if demand is fulfilled for each size and distance bucket
            for size, buckets in yearly_demand.items():
                for bucket, required_distance in buckets.items():
                    if demand_coverage.get(size, {}).get(bucket, 0) < required_distance:
                        demand_fulfilled = False
                        break
                if not demand_fulfilled:
                    break

        # Integrate sell_violation logic
        if self.sell_violation(chromosome) > 0:
            total_cost += self.hard_constraint_penalty

        # Add penalty if demand is not fulfilled
        if not demand_fulfilled:
            total_cost += self.hard_constraint_penalty

        return total_cost

    def get_total_vehicles(self, fleet):
        previous_years_number_initially = self.sum_nested_dict(
            self.all_previous_vehicles_leftover)
        current_year_number_initially = sum(
            vehicle['Num_Vehicles'] for vehicle in fleet['buy'])
        return previous_years_number_initially + current_year_number_initially

    def sell_violation(self, fleet):
        violations = 0
        total_vehicles = self.get_total_vehicles(fleet)
        total_sold = sum(vehicle['Num_Vehicles'] for vehicle in fleet['sell'])

        if total_sold > 0.20 * total_vehicles:
            violations += 1

        return violations

    def load_from_json(self, filename):
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
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def update_json_with_new_data(self, new_data, filename):
        existing_data = self.load_from_json(filename)
        existing_data.update(new_data)
        self.save_to_json(existing_data, filename)
