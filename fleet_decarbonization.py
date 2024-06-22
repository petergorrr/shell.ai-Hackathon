import pandas as pd
import random

class FleetDecarbonization:
    def __init__(self, carbon_emissions_file, cost_profiles_file, demand_file, fuels_file, vehicles_file, vehicles_fuels_file, hard_constraint_penalty=1000):
        self.hard_constraint_penalty = hard_constraint_penalty
        self.carbon_emissions = pd.read_csv(carbon_emissions_file)
        self.cost_profiles = pd.read_csv(cost_profiles_file)
        self.demand = pd.read_csv(demand_file)
        self.fuels = pd.read_csv(fuels_file)
        self.vehicles = pd.read_csv(vehicles_file)
        self.vehicles_fuels = pd.read_csv(vehicles_fuels_file)

        self.years = list(range(2023, 2039))
        self.size_buckets = ['S1', 'S2', 'S3', 'S4']
        self.distance_buckets = ['D1', 'D2', 'D3', 'D4']

    def __len__(self):
        return len(self.years) * len(self.size_buckets) * len(self.distance_buckets)

    def create_individual(self):
        individual = []
        for year in self.years:
            for size in self.size_buckets:
                for distance in self.distance_buckets:
                    vehicle_id = random.choice(self.vehicles[(self.vehicles['Size'] == size) & (self.vehicles['Distance'] == distance)]['ID'].values)
                    num_vehicles = random.randint(1, 11)
                    max_distance = self.vehicles[self.vehicles['ID'] == vehicle_id]['Yearly range (km)'].values[0]
                    distance_covered = random.randint(1, max_distance + 1)
                    individual.append({'Year': year, 'Size': size, 'Distance': distance, 'ID': vehicle_id, 'Num_Vehicles': num_vehicles, 'Distance_per_vehicle': distance_covered})
        return individual

    def get_cost(self, schedule):
        total_cost = 0
        total_emissions = {year: 0 for year in self.years}
        demand_fulfilled = {(year, size, distance): 0 for year in self.years for size in self.size_buckets for distance in self.distance_buckets}

        for plan in schedule:
            year = plan['Year']
            size = plan['Size']
            distance = plan['Distance']
            vehicle_id = plan['ID']
            num_vehicles = plan['Num_Vehicles']
            distance_covered = plan['Distance_per_vehicle']

            vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id].iloc[0]
            fuel_type = self.vehicles_fuels[self.vehicles_fuels['ID'] == vehicle_id]['Fuel'].values[0]
            fuel_consumption = self.vehicles_fuels[self.vehicles_fuels['ID'] == vehicle_id]['Consumption (unit_fuel/km)'].values[0]
            fuel_cost = self.fuels[(self.fuels['Fuel'] == fuel_type) & (self.fuels['Year'] == year)]['Cost ($/unit_fuel)'].values[0]
            fuel_emissions = self.fuels[(self.fuels['Fuel'] == fuel_type) & (self.fuels['Year'] == year)]['Emissions (CO2/unit_fuel)'].values[0]

            total_cost += vehicle['Cost ($)'] * num_vehicles
            total_cost += fuel_cost * fuel_consumption * distance_covered * num_vehicles
            total_emissions[year] += fuel_emissions * fuel_consumption * distance_covered * num_vehicles

            demand_fulfilled[(year, size, distance)] += distance_covered * num_vehicles

        hard_constraint_violations = sum(
            total_emissions[year] > self.carbon_emissions[self.carbon_emissions['Year'] == year]['Carbon emission CO2/kg'].values[0]
            for year in self.years
        ) + sum(
            demand_fulfilled[(year, size, distance)] < self.demand[(self.demand['Year'] == year) & (self.demand['Size'] == size) & (self.demand['Distance'] == distance)]['Demand (km)'].values[0]
            for year in self.years
            for size in self.size_buckets
            for distance in self.distance_buckets
        )

        return self.hard_constraint_penalty * hard_constraint_violations

    def mutate_individual(self, individual):
        for plan in individual:
            if random.random() < 0.1:
                plan['Num_Vehicles'] = random.randint(1, 11)
                max_distance = self.vehicles[self.vehicles['ID'] == plan['ID']]['Yearly range (km)'].values[0]
                plan['Distance_per_vehicle'] = random.randint(1, max_distance + 1)
        return individual,

    def custom_crossover(self, ind1, ind2):
        if len(ind1) > 1 and len(ind2) > 1:
            cxpoint1 = random.randint(1, len(ind1) - 1)
            cxpoint2 = random.randint(1, len(ind2) - 1)
            ind1[cxpoint1:], ind2[cxpoint2:] = ind2[cxpoint2:], ind1[cxpoint1:]
        return ind1, ind2
