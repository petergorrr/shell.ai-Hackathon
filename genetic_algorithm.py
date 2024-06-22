import random
from deap import base, creator, tools, algorithms
import matplotlib.pyplot as plt
import numpy as np
from fleet_decarbonization import FleetDecarbonization


def main():
    fleet = FleetDecarbonization(
        'dataset/carbon_emissions.csv',
        'dataset/cost_profiles.csv',
        'dataset/demand.csv',
        'dataset/fuels.csv',
        'dataset/vehicles.csv',
        'dataset/vehicles_fuels.csv'
    )
    random.seed(20)

    # Set up GA parameters
    population_size = 50
    generations = 30
    p_crossover = 0.9
    p_mutation = 0.1

    # Set up the toolbox
    toolbox = base.Toolbox()
    toolbox.register('individual', fleet.create_individual)
    creator.create('fitnessMin', base.Fitness, weights=(-1.0,))
    creator.create('Individual', list, fitness=creator.fitnessMin)
    toolbox.register('individual_creator', tools.initRepeat,
                     creator.Individual, toolbox.individual, 1)
    toolbox.register('population_creator', tools.initRepeat,
                     list, toolbox.individual_creator)

    # Set up fitness function
    def fitness_function(individual):
        return fleet.get_cost(individual[0]),

    # Set up the genetic operators
    toolbox.register('evaluate', fitness_function)
    toolbox.register('select', tools.selTournament, tournsize=3)
    toolbox.register('mate', fleet.custom_crossover)
    toolbox.register('mutate', fleet.mutate_individual)

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


if __name__ == "__main__":
    main()
