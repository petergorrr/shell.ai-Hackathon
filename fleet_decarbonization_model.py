import random
import pandas as pd


class FleetDecarbonization:
    def __init__(self,
                 carbon_emissions_file,
                 cost_profiles_file,
                 demand_file,
                 fuels_file,
                 vehicles_file,
                 vehicles_fuels_file,
                 hard_constraint_penalty=1000):

        self.hard_constraint_penalty = hard_constraint_penalty

        # Load data
        self.carbon_emissions = pd.read_csv(carbon_emissions_file)
        self.cost_profiles = pd.read_csv(cost_profiles_file)
        self.demand = pd.read_csv(demand_file)
        self.fuels = pd.read_csv(fuels_file)
        self.vehicles = pd.read_csv(vehicles_file)
        self.vehicles_fuels = pd.read_csv(vehicles_fuels_file)

        self.years = list(range(2023, 2039))
        self.size_buckets = ['S1', 'S2', 'S3', 'S4']
        self.distance_buckets = ['D1', 'D2', 'D3', 'D4']

    def create_individual(self):
        individual = []
        for year in self.years:
            for size in self.size_buckets:
                for distance in self.distance_buckets:
                    vehicle_id = random.choice(self.vehicles[(self.vehicles['Size'] == size) & (
                        self.vehicles['Distance'] == distance)]['ID'].values)
                    num_vehicles = random.randint(1, 11)
                    max_distance = self.vehicles[self.vehicles['ID']
                                                 == vehicle_id]['Yearly range (km)'].values[0]
                    distance_covered = random.randint(1, max_distance + 1)
                    individual.append({'Year': year, 'Size': size, 'Distance': distance, 'ID': vehicle_id,
                                      'Num_Vehicles': num_vehicles, 'Distance_per_vehicle': distance_covered})
        return individual

    def get_cost(self, schedule):
        total_cost = 0
        total_emissions = {year: 0 for year in self.years}
        demand_fulfilled = {
            (year, size, distance): 0 for year in self.years for size in self.size_buckets for distance in self.distance_buckets}

        for plan in schedule:
            year = plan['Year']
            size = plan['Size']
            distance = plan['Distance']
            vehicle_id = plan['ID']
            num_vehicles = plan['Num_Vehicles']
            distance_covered = plan['Distance_per_vehicle']

            vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id].iloc[0]
            fuel_type = self.vehicles_fuels[self.vehicles_fuels['ID']
                                            == vehicle_id]['Fuel'].values[0]
            fuel_consumption = self.vehicles_fuels[self.vehicles_fuels['ID']
                                                   == vehicle_id]['Consumption (unit_fuel/km)'].values[0]
            fuel_cost = self.fuels[(self.fuels['Fuel'] == fuel_type) & (
                self.fuels['Year'] == year)]['Cost ($/unit_fuel)'].values[0]
            fuel_emissions = self.fuels[(self.fuels['Fuel'] == fuel_type) & (
                self.fuels['Year'] == year)]['Emissions (CO2/unit_fuel)'].values[0]

            total_cost += vehicle['Cost ($)'] * num_vehicles
            total_cost += fuel_cost * fuel_consumption * distance_covered * num_vehicles
            total_emissions[year] += fuel_emissions * \
                fuel_consumption * distance_covered * num_vehicles

            demand_fulfilled[(year, size, distance)
                             ] += distance_covered * num_vehicles

        # Check constraints
        hard_constraint_violations = 0

        for year in self.years:
            if total_emissions[year] > self.carbon_emissions[self.carbon_emissions['Year'] == year]['Carbon emission CO2/kg'].values[0]:
                hard_constraint_violations += 1
            for size in self.size_buckets:
                for distance in self.distance_buckets:
                    demand_required = self.demand[(self.demand['Year'] == year) & (self.demand['Size'] == size) & (
                        self.demand['Distance'] == distance)]['Demand (km)'].values[0]
                    if demand_fulfilled[(year, size, distance)] < demand_required:
                        hard_constraint_violations += 1

        return self.hard_constraint_penalty * hard_constraint_violations

    def mutate_individual(self, individual):
        for i, plan in enumerate(individual):
            if random.random() < 0.1:
                plan['Num_Vehicles'] = random.randint(1, 11)
                max_distance = self.vehicles[self.vehicles['ID']
                                             == plan['ID']]['Yearly range (km)'].values[0]
                plan['Distance_per_vehicle'] = random.randint(
                    1, max_distance + 1)
        return individual

    def custom_crossover(self, ind1, ind2):
        if len(ind1) > 1 and len(ind2) > 1:
            cxpoint1 = random.randint(1, len(ind1) - 1)
            cxpoint2 = random.randint(1, len(ind2) - 1)
            ind1[cxpoint1:], ind2[cxpoint2:] = ind2[cxpoint2:], ind1[cxpoint1:]
        return ind1, ind2

    def print_solution_info(self, best, logbook, min_value, avg_value):
        # Print summary of the best individual
        print("Best individual:")
        print(best)

        # Print final generation fitness statistics
        print("\nFitness Information:")
        print(f"Final Generation Min Fitness: {min_value[-1]}")
        print(f"Final Generation Avg Fitness: {avg_value[-1]}")

        # Calculate and print total cost of the best individual
        total_cost = self.get_cost(best[0])
        print(f"Total Cost of Best Individual: {total_cost}")

        # Calculate total emissions for each year
        total_emissions = {year: 0 for year in self.years}
        for plan in best:
            year = plan['Year']
            vehicle_id = plan['ID']
            num_vehicles = plan['Num_Vehicles']
            fuel_type = self.vehicles_fuels[self.vehicles_fuels['ID']
                                            == vehicle_id]['Fuel'].values[0]
            distance_covered = plan['Distance_per_vehicle']
            fuel_consumption = self.vehicles_fuels[self.vehicles_fuels['ID']
                                                   == vehicle_id]['Consumption (unit_fuel/km)'].values[0]
            fuel_emissions = self.fuels[(self.fuels['Fuel'] == fuel_type) & (
                self.fuels['Year'] == year)]['Emissions (CO2/unit_fuel)'].values[0]

            total_emissions[year] += fuel_emissions * \
                fuel_consumption * distance_covered * num_vehicles

        # Calculate hard constraint violations
        hard_constraint_violations = 0
        for year in self.years:
            if total_emissions[year] > self.carbon_emissions[self.carbon_emissions['Year'] == year]['Carbon emission CO2/kg'].values[0]:
                hard_constraint_violations += 1

        # Print the number of hard constraint violations
        print(f"Hard Constraint Violations: {hard_constraint_violations}")

    def categorize_vehicles(self, best):
        actions = []

        # Maintain a record of vehicle usage
        vehicle_usage = {year: [] for year in self.years}
        for plan in best:
            year = plan['Year']
            vehicle_id = plan['ID']
            num_vehicles = plan['Num_Vehicles']
            distance = plan['Distance']
            distance_covered = plan['Distance_per_vehicle']
            size = plan['Size']

            vehicle_usage[year].append({
                'ID': vehicle_id,
                'Num_Vehicles': num_vehicles,
                'Distance': distance,
                'Distance_per_vehicle': distance_covered,
                'Size': size
            })

        # Decide actions for each year
        for year in self.years:
            for size in self.size_buckets:
                for distance in self.distance_buckets:
                    required_demand = self.demand[(self.demand['Year'] == year) & (self.demand['Size'] == size) & (
                        self.demand['Distance'] == distance)]['Demand (km)'].values[0]
                    current_capacity = sum([v['Distance_per_vehicle'] * v['Num_Vehicles']
                                           for v in vehicle_usage[year] if v['Size'] == size and v['Distance'] == distance])

                    if required_demand > current_capacity:
                        vehicle_id = self.select_vehicle_to_buy(
                            size, distance, year)
                        num_vehicles_needed = (
                            required_demand - current_capacity) // self.vehicles[self.vehicles['ID'] == vehicle_id]['Yearly range (km)'].values[0]
                        actions.append({'Year': year, 'ID': vehicle_id,
                                       'Num_Vehicles': num_vehicles_needed, 'Type': 'buy'})

            for vehicle in vehicle_usage[year]:
                actions.append({'Year': year, 'ID': vehicle['ID'], 'Num_Vehicles': vehicle['Num_Vehicles'], 'Type': 'use',
                               'Distance_bucket': vehicle['Distance'], 'Distance_per_vehicle(km)': vehicle['Distance_per_vehicle']})

            for vehicle in vehicle_usage[year]:
                if year > vehicle['Year'] + 10:
                    actions.append(
                        {'Year': year, 'ID': vehicle['ID'], 'Num_Vehicles': vehicle['Num_Vehicles'], 'Type': 'sell'})

        return actions

    def select_vehicle_to_buy(self, size, distance, year):
        available_vehicles = self.vehicles[(self.vehicles['Size'] == size) & (
            self.vehicles['Distance'] == distance) & (self.vehicles['Year'] == year)]
        selected_vehicle = available_vehicles.iloc[0]['ID']
        return selected_vehicle

    def save_to_csv(self, best):
        # Categorize vehicles
        solution_data = self.categorize_vehicles(best)

        # Convert the solution data to a DataFrame
        solution_df = pd.DataFrame(solution_data)

        # Save the DataFrame to a CSV file
        solution_df.to_csv('solution.csv', index=False)
        print("Solution saved to solution.csv")
