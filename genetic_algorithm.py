import random
import copy
from fleet_decarbonization_model_final import FleetOptimization
import csv

class GeneticAlgorithm:
    def __init__(self, fleet_optimization, population_size=100, generations=700):
        # Set the seed for reproducibility
        
        self.fleet_optimization = fleet_optimization
        self.population_size = population_size
        self.generations = generations
        self.population = []

    def generate_initial_population(self):
        for _ in range(self.population_size):
            chromosome = []
            for year in range(2023, 2039):
                year_dict = {'buy': [], 'sell': [], 'use': []}
                
                # Randomly decide to buy vehicles
                for vehicle_id in self.fleet_optimization.vehicle_ids:
                    if random.random() < 0.3:  # 30% chance to buy each vehicle type
                        vehicle_details = self.fleet_optimization.get_vehicle_details(vehicle_id)
                        if vehicle_details and vehicle_details['year'] == year:
                            num_vehicles = random.randint(1, 10)
                            year_dict['buy'].append({
                                'ID': vehicle_id,
                                'Num_Vehicles': num_vehicles,
                                'Distance_per_vehicle(km)': vehicle_details['yearly range'],
                                'Distance_bucket': vehicle_details['distance'],
                                'Fuel': random.choice(list(self.fleet_optimization.vehicle_fuel_consumptions[vehicle_id].keys()))
                            })
                
                # Randomly decide to sell vehicles (simplified)
                if year > 2023 and random.random() < 0.2:  # 20% chance to sell
                    for vehicle in chromosome[-1]['use']:
                        if random.random() < 0.1:  # 10% chance to sell each vehicle type
                            year_dict['sell'].append({
                                'ID': vehicle['ID'],
                                'Num_Vehicles': random.randint(1, vehicle['Num_Vehicles']),
                                'Distance_per_vehicle(km)': vehicle['Distance_per_vehicle(km)'],
                                'Distance_bucket': vehicle['Distance_bucket'],
                                'Fuel': vehicle['Fuel']
                            })
                
                # Use all vehicles that weren't sold
                year_dict['use'] = copy.deepcopy(year_dict['buy'])
                if year > 2023:
                    for vehicle in chromosome[-1]['use']:
                        if not any(sell_vehicle['ID'] == vehicle['ID'] for sell_vehicle in year_dict['sell']):
                            year_dict['use'].append(copy.deepcopy(vehicle))
                
                chromosome.append(year_dict)
            
            self.population.append(chromosome)

    def fitness(self, chromosome):
        total_cost = 0
        total_emissions = 0
        for year, year_dict in enumerate(chromosome, start=2023):
            try:
                # Calculate costs
                total_cost += self.fleet_optimization.calculate_buy_cost(year_dict)
                total_cost += self.fleet_optimization.calculate_insurance_cost(year_dict, year)
                total_cost += self.fleet_optimization.calculate_maintenance_cost(year_dict, year)
                total_cost += self.fleet_optimization.calculate_fuel_cost(year_dict)
                total_cost -= self.fleet_optimization.calculate_resale_value(year_dict, year)
                
                # Calculate emissions
                year_emissions = self.fleet_optimization.calculate_emissions(year_dict)
                total_emissions += year_emissions
                
                # Check if emissions exceed the limit
                if year_emissions > self.fleet_optimization.carbon_emissions[str(year)]:
                    return float('inf')  # Return a very high cost if emissions limit is exceeded
                
                # Check if demand is met
                if not self.fleet_optimization.check_fleet_meets_demand(year_dict):
                    return float('inf')  # Return a very high cost if demand is not met
                
            except ValueError:
                return float('inf')  # Return a very high cost if any constraint is violated
        
        return total_cost

    def select_parents(self):
        tournament_size = 5
        tournament = random.sample(self.population, tournament_size)
        return min(tournament, key=self.fitness)

    def crossover(self, parent1, parent2):
        child = []
        for year in range(len(parent1)):
            if random.random() < 0.5:
                child.append(copy.deepcopy(parent1[year]))
            else:
                child.append(copy.deepcopy(parent2[year]))
        return child

    def mutate(self, chromosome):
        for year_dict in chromosome:
            if random.random() < 0.1:  # 10% chance to mutate each year
                action = random.choice(['buy', 'sell', 'use'])
                if year_dict[action]:
                    vehicle = random.choice(year_dict[action])
                    vehicle['Num_Vehicles'] = max(1, vehicle['Num_Vehicles'] + random.randint(-2, 2))
        return chromosome

    def evolve(self):
        self.generate_initial_population()
        
        for generation in range(self.generations):
            new_population = []
            
            for _ in range(self.population_size):
                parent1 = self.select_parents()
                parent2 = self.select_parents()
                child = self.crossover(parent1, parent2)
                child = self.mutate(child)
                new_population.append(child)
            
            self.population = new_population
            
            best_chromosome = min(self.population, key=self.fitness)
            best_fitness = self.fitness(best_chromosome)
            
            print(f"Generation {generation}: Best Fitness = {best_fitness}")
        
        return min(self.population, key=self.fitness)

def save_best_solution(best_solution, filename='best_solution.csv'):
    fieldnames = ['Year', 'Action', 'ID', 'Num_Vehicles', 'Distance_per_vehicle(km)', 'Distance_bucket', 'Fuel']
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for year, year_data in enumerate(best_solution, start=2023):
            for action, vehicles in year_data.items():
                for vehicle in vehicles:
                    writer.writerow({
                        'Year': year,
                        'ID': vehicle['ID'],
                        'Num_Vehicles': vehicle['Num_Vehicles'],
                        'Type': action,
                        'Fuel': vehicle.get('Fuel', ''),
                        'Distance_bucket': vehicle.get('Distance_bucket', ''),
                        'Distance_per_vehicle(km)': vehicle.get('Distance_per_vehicle(km)', '')    
                    })

# Usage
fleet_optimization = FleetOptimization('dataset/mapping_and_cost_data.json')
ga = GeneticAlgorithm(fleet_optimization)
best_solution = ga.evolve()
save_best_solution(best_solution)
