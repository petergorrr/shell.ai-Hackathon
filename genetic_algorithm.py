import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from deap import base, creator, tools, algorithms
from fleet_decarbonization_model import FleetDecarbonization
import json

class GA:
    
    def __init__(self, mapping_data_file):
        # Load mapping data from JSON file
        with open(mapping_data_file, 'r') as f:
            mapping_data = json.load(f)

        self.distance_mapping = mapping_data['distance_mapping']
    
    def setup_toolbox(fleet):
        toolbox = base.Toolbox()
        toolbox.register('individual', fleet.create_individual)
        creator.create('fitnessMin', base.Fitness, weights=(-1.0,))
        creator.create('Individual', list, fitness=creator.fitnessMin)
        toolbox.register('individual_creator', tools.initRepeat, creator.Individual, toolbox.individual, len(fleet))
        toolbox.register('population_creator', tools.initRepeat, list, toolbox.individual_creator)
        
        def fitness_function(individual):
            return fleet.get_cost(individual),
        
        toolbox.register('evaluate', fitness_function)
        toolbox.register('select', tools.selTournament, tournsize=3)
        toolbox.register('mate', fleet.custom_crossover)
        toolbox.register('mutate', fleet.mutate_individual)
    
    # Uniform crossover using entire vehicle model for each action (exchaning numbers for num and distance)
    def custom_crossover(self, parent1, parent2):
        offspring1 = {'buy': [], 'sell': [], 'use': []}
        offspring2 = {'buy': [], 'sell': [], 'use': []}
        
        for action in ['buy', 'sell', 'use']:
            for vehicle1, vehicle2 in zip(parent1[action], parent2[action]):
                if random.random() < 0.5:
                    offspring1[action].append(vehicle1)
                    offspring2[action].append(vehicle2)
                else:
                    offspring1[action].append(vehicle2)
                    offspring2[action].append(vehicle1)

        return offspring1, offspring2
    
    def custom_mutate(self, offspring, mutation_rate):
        mutated_offspring = {'buy': [], 'sell': [], 'use': []}
        
        # Store dictionary 
        vehicles_bought = {}
        for vehicle in offspring['buy']:
            vehicle_id = vehicle['ID']
            fuel_type = vehicle['Fuel']
            distance_bucket = vehicle['Distance_bucket']
            if vehicle_id not in vehicles_bought:
                vehicles_bought[vehicle_id] = {}
            
            if fuel_type not in vehicles_bought[vehicle_id]:
                vehicles_bought[vehicle_id][fuel_type] = {}
                
            if distance_bucket not in vehicles_bought[vehicle_id][fuel_type]:
                vehicles_bought[vehicle_id][fuel_type][distance_bucket] = vehicle['Num_Vehicles']
        
        # Mtate offspring
        for action in ['buy', 'sell', 'use']:
            for vehicle in offspring[action]:
                mutated_vehicle = vehicle.copy()
                
                if random.random() < mutation_rate:
                    if action == 'buy':
                        mutated_vehicle['Num_Vehicles'] += random.randint(-2, 2)
                        mutated_vehicle['Num_Vehicles'] = max(mutated_vehicle['Num_Vehicles'], 0) # Ensure Num_vehicles mutated is not below 0
                        # Update the count in vehicles_bought
                        vehicles_bought[mutated_vehicle['ID']][mutated_vehicle['Fuel']][mutated_vehicle['Distance_bucket']] = mutated_vehicle['Num_Vehicles']
                    else:
                        max_vehicles = vehicles_bought.get(mutated_vehicle['ID'], {}).get(mutated_vehicle['Fuel'], {}).get(mutated_vehicle['Distance_bucket'], 0)
                        mutated_vehicle['Num_Vehicles'] += random.randint(-2, 2)
                        # Ensure Num_Vehicles does not go below 0 or above the number bought
                        mutated_vehicle['Num_Vehicles'] = max(mutated_vehicle['Num_Vehicles'], 0)
                        mutated_vehicle['Num_Vehicles'] = min(mutated_vehicle['Num_Vehicles'], max_vehicles)
                
                    # Mutate Distance_per_vehicle only for 'use' action
                    if action == 'use':
                        if mutated_vehicle['Num_Vehicles'] == 0:
                            mutated_vehicle['Distance_per_vehicle'] = 0
                        else:
                            max_distance = self.distance_mapping[mutated_vehicle['Distance_bucket']]
                            mutated_vehicle['Distance_per_vehicle'] += random.randint(-50, 50)
                            # Ensure Distance_per_vehicle does not go below 0
                            mutated_vehicle['Distance_per_vehicle'] = max(mutated_vehicle['Distance_per_vehicle'], 0)
                            # Ensure Distance_per_vehicle does not go above distance bucket limit
                            mutated_vehicle['Distance_per_vehicle'] = min(mutated_vehicle['Distance_per_vehicle'], max_distance)
                    
                    mutated_offspring[action].append(mutated_vehicle)
        
        return mutated_offspring