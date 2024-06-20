import pandas as pd
import random
import matplotlib.pyplot as plt
from deap import base, creator, tools, algorithms
import numpy as np

class FleetDecarbonization:
    def __init__(self, carbon_emissions_file, cost_profiles_file, demand_file, fuels_file, vehicles_file, vehicles_fuels_file, hard_constraint_penalty=1000):
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

        # Check constraints
        hard_constraint_violations = 0
        soft_constraint_violations = 0

        for year in self.years:
            if total_emissions[year] > self.carbon_emissions[self.carbon_emissions['Year'] == year]['Carbon emission CO2/kg'].values[0]:
                hard_constraint_violations += 1
            for size in self.size_buckets:
                for distance in self.distance_buckets:
                    demand_required = self.demand[(self.demand['Year'] == year) & (self.demand['Size'] == size) & (self.demand['Distance'] == distance)]['Demand (km)'].values[0]
                    if demand_fulfilled[(year, size, distance)] < demand_required:
                        hard_constraint_violations += 1

        return self.hard_constraint_penalty * hard_constraint_violations + soft_constraint_violations

    def mutate_individual(self, individual):
        for i, plan in enumerate(individual):
            if isinstance(plan, dict):
                if random.random() < 0.1:
                    try:
                        plan['Num_Vehicles'] = random.randint(1, 11)
                        max_distance = self.vehicles[self.vehicles['ID'] == plan['ID']]['Yearly range (km)'].values[0]
                        plan['Distance_per_vehicle'] = random.randint(1, max_distance + 1)
                        individual[i] = plan
                    except Exception as e:
                        print(f"Error mutating plan: {plan}")
                        print(e)
            else:
                print(f"Plan is not a dictionary: {plan}")
        return individual,

    def custom_crossover(self, ind1, ind2):
        if len(ind1) > 1 and len(ind2) > 1:
            cxpoint1 = random.randint(1, len(ind1) - 1)
            cxpoint2 = random.randint(1, len(ind2) - 1)
            ind1[cxpoint1:], ind2[cxpoint2:] = ind2[cxpoint2:], ind1[cxpoint1:]
        return ind1, ind2

    def run_optimization(self, population_size=50, generations=100, p_crossover=0.9, p_mutation=0.1):
        # Set up the toolbox
        toolbox = base.Toolbox()
        toolbox.register('individual', self.create_individual)
        creator.create('fitnessMin', base.Fitness, weights=(-1.0,))
        creator.create('Individual', list, fitness=creator.fitnessMin)
        toolbox.register('individual_creator', tools.initRepeat, creator.Individual, toolbox.individual, 1)
        toolbox.register('population_creator', tools.initRepeat, list, toolbox.individual_creator)

        # Set up fitness function
        def fitness_function(individual):
            return self.get_cost(individual[0]),

        # Set up the genetic operators
        toolbox.register('evaluate', fitness_function)
        toolbox.register('select', tools.selTournament, tournsize=3)
        toolbox.register('mate', self.custom_crossover)
        toolbox.register('mutate', self.mutate_individual)

        # Define and run the algorithm
        population = toolbox.population_creator(n=population_size)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register('min', np.min)
        stats.register('avg', np.mean)

        hof = tools.HallOfFame(5)

        final_population, logbook = algorithms.eaSimple(
            population,
            toolbox,
            cxpb=p_crossover,
            mutpb=p_mutation,
            ngen=generations,
            stats=stats,
            halloffame=hof,
            verbose=True
        )

        min_value, avg_value = logbook.select('min', 'avg')

        plt.plot(min_value, color='red')
        plt.plot(avg_value, color='green')
        plt.xlabel('Generations')
        plt.ylabel('Min/Avg Fitness per Generation')
        plt.show()

        best = hof[0]
        print("Best individual:", best)
        return best

