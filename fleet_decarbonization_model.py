import pandas as pd
import json


class FleetDecarbonization:

    hard_constraint_penalty = 1000

    def __init__(self,
                 cost_profiles_file,
                 fuels_file,
                 vehicles_file,
                 vehicles_fuels_file,
                 mapping_data_file):
        """
        Initialize the FleetDecarbonization class with data files.
        """
        self.cost_profiles = pd.read_csv(cost_profiles_file)
        self.fuels = pd.read_csv(fuels_file)
        self.vehicles = pd.read_csv(vehicles_file)
        self.vehicles_fuels = pd.read_csv(vehicles_fuels_file)

        with open(mapping_data_file, 'r') as f:
            mapping_data = json.load(f)

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

        self.size_buckets = list(self.size_mapping.keys())
        self.distance_buckets = list(self.distance_mapping.keys())
        self.years = list(range(2023, 2039))
        self.actions = ['buy', 'sell', 'use']

        self.total_distance = self.calculate_total_distance()

    def get_resale_value(self, purchase_cost, year):
        """
        Get the resale value of a vehicle based on its purchase cost and the number of years since purchase.
        """
        return purchase_cost * self.cost_percentages.get(year, {}).get('resale', 0.30)

    def get_insurance_cost(self, purchase_cost, year):
        """
        Get the insurance cost of a vehicle based on its purchase cost and the number of years since purchase.
        """
        return purchase_cost * self.cost_percentages.get(year, {}).get('insurance', 0.14)

    def get_maintenance_cost(self, purchase_cost, year):
        """
        Get the maintenance cost of a vehicle based on its purchase cost and the number of years since purchase.
        """
        return purchase_cost * self.cost_percentages.get(year, {}).get('maintenance', 0.19)

    def get_vehicle_info(self, vehicle_id):
        """
        Get the size and distance bucket for a specific vehicle.
        """
        vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
        if vehicle.empty:
            return None, None

        size = vehicle['Size'].values[0]
        distance = vehicle['Distance'].values[0]
        return size, distance

    def calculate_total_distance(self):
        # Implement the logic to calculate the total distance
        pass

#     def calculate_buy_cost(self, individual):
#         """
#         Calculate the total cost of buying vehicles for an individual.
#         """
#         total_cost = 0
#         for plan in individual:
#             vehicle_id = plan['ID']
#             vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
#             num_vehicles = plan['Num_Vehicles']
#             cost_per_vehicle = vehicle['Cost ($)'].values[0]
#             total_cost += cost_per_vehicle * num_vehicles
#         return total_cost

#     def calculate_insurance_cost(self, individual, year):
#         """
#         Calculate the total insurance cost for an individual in a given year.
#         """
#         total_cost = 0
#         for plan in individual:
#             vehicle_id = plan['ID']
#             purchase_year = plan['Year']
#             vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
#             num_vehicles = plan['Num_Vehicles']
#             purchase_cost = vehicle['Cost ($)'].values[0]
#             insurance_cost = self.get_insurance_cost(
#                 purchase_cost, year - purchase_year)
#             total_cost += insurance_cost * num_vehicles
#         return total_cost

#     def calculate_maintenance_cost(self, individual, year):
#         """
#         Calculate the total maintenance cost for an individual in a given year.
#         """
#         total_cost = 0
#         for plan in individual:
#             vehicle_id = plan['ID']
#             purchase_year = plan['Year']
#             vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
#             num_vehicles = plan['Num_Vehicles']
#             purchase_cost = vehicle['Cost ($)'].values[0]
#             maintenance_cost = self.get_maintenance_cost(
#                 purchase_cost, year - purchase_year)
#             total_cost += maintenance_cost * num_vehicles
#         return total_cost

#     def calculate_fuel_cost(self, individual, year):
#         """
#         Calculate the total fuel cost for an individual in a given year.
#         """
#         total_cost = 0
#         for plan in individual:
#             vehicle_id = plan['ID']
#             num_vehicles = plan['Num_Vehicles']
#             distance_covered = plan['Distance_per_vehicle']
#             fuel_type = self.vehicles_fuels[self.vehicles_fuels['ID']
#                                             == vehicle_id]['Fuel'].values[0]
#             fuel_consumption = self.vehicles_fuels[self.vehicles_fuels['ID']
#                                                    == vehicle_id]['Consumption (unit_fuel/km)'].values[0]
#             fuel_cost_per_unit = self.fuels[(self.fuels['Fuel'] == fuel_type) & (
#                 self.fuels['Year'] == year)]['Cost ($/unit_fuel)'].values[0]
#             total_cost += distance_covered * num_vehicles * \
#                 fuel_consumption * fuel_cost_per_unit
#         return total_cost

#     def calculate_selling_profit(self, individual, year):
#         """
#         Calculate the total selling profit for an individual in a given year.
#         """
#         total_profit = 0
#         for plan in individual:
#             vehicle_id = plan['ID']
#             vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
#             num_vehicles_to_sell = plan.get('Num_Vehicles_to_Sell', 0)
#             purchase_year = plan['Year']
#             purchase_cost = vehicle['Cost ($)'].values[0]
#             resale_value = self.get_resale_value(
#                 purchase_cost, year - purchase_year)
#             total_profit += resale_value * num_vehicles_to_sell
#         return total_profit


#     ### Hard constraints ###

#     def check_purchase_year(self, vehicle_id, purchase_year):
#         """
#         Check if the vehicle model can only be bought in its specified year.
#         """
#         vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
#         if vehicle.empty:
#             return False, f"Vehicle ID {vehicle_id} not found."

#         model_year = int(vehicle_id.split('_')[-1])
#         if purchase_year != model_year:
#             return False, f"Vehicle ID {vehicle_id} can only be bought in the year {model_year}."
#         return True, ""

#     def check_vehicle_lifetime(self, vehicle_id, current_year):
#         """
#         Check if the vehicle's lifetime has exceeded 10 years and if it needs to be sold.
#         """
#         vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
#         if vehicle.empty:
#             return False, f"Vehicle ID {vehicle_id} not found."

#         purchase_year = int(vehicle_id.split('_')[-1])
#         if current_year > purchase_year + 10:
#             return False, f"Vehicle ID {vehicle_id} must be sold by the end of {purchase_year + 10}."
#         return True, ""

#     def sell_violation(self, fleet):
#         """
#         Check for sell constraint violations:
#         1. Ensure that the number of vehicles sold is less than the total number of vehicles.
#         2. Ensure that no more than 20% of the total vehicles are sold in a year.
#         """
#         total_vehicles = sum(fleet['Num_Vehicles'])
#         total_sold = sum(fleet['Num_Vehicles_Sold'])

#         if total_sold > total_vehicles:
#             return True
#         if total_sold > 0.20 * total_vehicles:
#             return True
#         return False

#     def use_violation(self, fleet):
#         """
#         Check for use constraint violations:
#         Ensure that the number of vehicles used is less than or equal to the total number of vehicles.
#         """
#         total_vehicles = sum(fleet['Num_Vehicles'])
#         total_used = sum(fleet['Num_Vehicles_Used'])

#         if total_used > total_vehicles:
#             return True
#         return False

#     # Constraint 4 (Helper)
#     def calculate_total_distance(self, fleet):
#         total_distance = {year: {size: {distance: 0 for distance in self.distance_buckets}
#                                  for size in self.size_buckets} for year in self.years}
#         for plan in fleet:
#             vehicle_id = plan['ID']
#             num_vehicles = plan['Num_Vehicles']
#             distance_covered = plan['Distance_per_vehicle']

#             for year in self.years:
#                 for size in self.size_buckets:
#                     for distance in self.distance_buckets:
#                         if vehicle_id in self.distance_buckets_vehicles[year][size][distance]:
#                             total_distance[year][size][distance] += distance_covered * num_vehicles

#         return total_distance

#     # Constraint 4
#     def verify_distance_meets_demand(self):
#         for year in self.years:
#             for size in self.size_buckets:
#                 for distance in self.distance_buckets:
#                     if self.total_distance[year][size][distance] < self.yearly_demand[year][size][distance]:
#                         return False

#         return True

#     # Constraint to limit vehicle usage, should not be 0 or maximum limit
#     def distance_limit_violation(self):
#         """
#         Distance limit violation, usage should not be 0 or over limit of bucket
#         """
#         pass

#     def create_individual(self):
#         individual = []
#         current_year = self.years[0]  # 2023
#         for size in self.size_buckets:
#             for distance in self.distance_buckets:
#                 vehicle_id = random.choice(self.vehicles[(self.vehicles['Year'] == current_year) & (self.vehicles['Size'] == size) & (
#                     self.vehicles['Distance'] == distance)]['ID'].tolist())
#                 num_vehicles = random.randint(1, 11)
#                 max_distance = self.vehicles[self.vehicles['ID']
#                                              == vehicle_id]['Yearly range (km)'].values[0]
#                 distance_covered = random.randint(1, max_distance + 1)
#                 individual.append(
#                     {'ID': vehicle_id, 'Num_Vehicles': num_vehicles, 'Distance_per_vehicle': distance_covered})
#         return individual
