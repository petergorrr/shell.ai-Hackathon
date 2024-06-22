import random
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

    # Run the optimization
    best = fleet.run_optimization(
        population_size=50,
        generations=30,
        p_crossover=0.9,
        p_mutation=0.1
    )
    print("Best individual:", best)


if __name__ == "__main__":
    main()
