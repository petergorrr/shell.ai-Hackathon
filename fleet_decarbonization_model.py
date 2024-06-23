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

        # Initialize years and buckets
        self.years = list(range(2023, 2039))
        self.size_buckets = ['S1', 'S2', 'S3', 'S4']
        self.distance_buckets = ['D1', 'D2', 'D3', 'D4']

        # Distance bucket mappings
        self.distance_mapping = {
            'D1': 300,
            'D2': 400,
            'D3': 500,
            'D4': 600
        }

        # Size bucket mappings
        self.size_mapping = {
            'S1': 17,
            'S2': 44,
            'S3': 50,
            'S4': 64
        }

        # Resale, insurance, and maintenance costs as a percentage of purchase cost by year
        self.cost_percentages = {
            1: {'resale': 0.90, 'insurance': 0.05, 'maintenance': 0.01},
            2: {'resale': 0.80, 'insurance': 0.06, 'maintenance': 0.03},
            3: {'resale': 0.70, 'insurance': 0.07, 'maintenance': 0.05},
            4: {'resale': 0.60, 'insurance': 0.08, 'maintenance': 0.07},
            5: {'resale': 0.50, 'insurance': 0.09, 'maintenance': 0.09},
            6: {'resale': 0.40, 'insurance': 0.10, 'maintenance': 0.11},
            7: {'resale': 0.30, 'insurance': 0.11, 'maintenance': 0.13},
            8: {'resale': 0.30, 'insurance': 0.12, 'maintenance': 0.15},
            9: {'resale': 0.30, 'insurance': 0.13, 'maintenance': 0.17},
            10: {'resale': 0.30, 'insurance': 0.14, 'maintenance': 0.19}
        }

        # Encode yearly demand for each size and distance bucket
        self.yearly_demand = self.calculate_yearly_demand()

    def get_resale_value(self, purchase_cost, year):
        """
        Get the resale value of a vehicle based on its purchase cost and the number of years since purchase.
        """
        if year in self.cost_percentages:
            return purchase_cost * self.cost_percentages[year]['resale']
        return purchase_cost * 0.30  # default value for years beyond 10

    def get_insurance_cost(self, purchase_cost, year):
        """
        Get the insurance cost of a vehicle based on its purchase cost and the number of years since purchase.
        """
        if year in self.cost_percentages:
            return purchase_cost * self.cost_percentages[year]['insurance']
        return purchase_cost * 0.14  # default value for years beyond 10

    def get_maintenance_cost(self, purchase_cost, year):
        """
        Get the maintenance cost of a vehicle based on its purchase cost and the number of years since purchase.
        """
        if year in self.cost_percentages:
            return purchase_cost * self.cost_percentages[year]['maintenance']
        return purchase_cost * 0.19  # default value for years beyond 10

    def calculate_yearly_demand(self):
        """
        Calculate the total yearly demand traveled distance for the respective size and distance bucket vehicles.
        """
        yearly_demand = {year: {size: {distance: 0 for distance in self.distance_buckets}
                                for size in self.size_buckets} for year in self.years}

        for year in self.years:
            for size in self.size_buckets:
                for distance in self.distance_buckets:
                    total_distance = self.demand[(self.demand['Year'] == year) &
                                                 (self.demand['Size'] == size) &
                                                 (self.demand['Distance'] == distance)]['Demand (km)'].sum()
                    yearly_demand[year][size][distance] = total_distance

        return yearly_demand

    def get_vehicle_yearly_demand(self, vehicle_id):
        """
        Get the yearly demand for a specific vehicle based on its ID.
        """
        vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
        if vehicle.empty:
            return f"Vehicle ID {vehicle_id} not found."

        year = vehicle['Year'].values[0]
        size = vehicle['Size'].values[0]
        distance = vehicle['Distance'].values[0]

        demand = self.yearly_demand[year][size][distance]
        return demand

    def calculate_buy_cost(self, individual):
        """
        Calculate the total cost of buying vehicles for an individual.
        """
        total_cost = 0
        for plan in individual:
            vehicle_id = plan['ID']
            vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
            num_vehicles = plan['Num_Vehicles']
            cost_per_vehicle = vehicle['Cost ($)'].values[0]
            total_cost += cost_per_vehicle * num_vehicles
        return total_cost

    def calculate_insurance_cost(self, individual, year):
        """
        Calculate the total insurance cost for an individual in a given year.
        """
        total_cost = 0
        for plan in individual:
            vehicle_id = plan['ID']
            purchase_year = plan['Year']
            vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
            num_vehicles = plan['Num_Vehicles']
            purchase_cost = vehicle['Cost ($)'].values[0]
            insurance_cost = self.get_insurance_cost(
                purchase_cost, year - purchase_year)
            total_cost += insurance_cost * num_vehicles
        return total_cost

    def calculate_maintenance_cost(self, individual, year):
        """
        Calculate the total maintenance cost for an individual in a given year.
        """
        total_cost = 0
        for plan in individual:
            vehicle_id = plan['ID']
            purchase_year = plan['Year']
            vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
            num_vehicles = plan['Num_Vehicles']
            purchase_cost = vehicle['Cost ($)'].values[0]
            maintenance_cost = self.get_maintenance_cost(
                purchase_cost, year - purchase_year)
            total_cost += maintenance_cost * num_vehicles
        return total_cost

    def calculate_fuel_cost(self, individual, year):
        """
        Calculate the total fuel cost for an individual in a given year.
        """
        total_cost = 0
        for plan in individual:
            vehicle_id = plan['ID']
            num_vehicles = plan['Num_Vehicles']
            distance_covered = plan['Distance_per_vehicle']
            fuel_type = self.vehicles_fuels[self.vehicles_fuels['ID']
                                            == vehicle_id]['Fuel'].values[0]
            fuel_consumption = self.vehicles_fuels[self.vehicles_fuels['ID']
                                                   == vehicle_id]['Consumption (unit_fuel/km)'].values[0]
            fuel_cost_per_unit = self.fuels[(self.fuels['Fuel'] == fuel_type) & (
                self.fuels['Year'] == year)]['Cost ($/unit_fuel)'].values[0]
            total_cost += distance_covered * num_vehicles * \
                fuel_consumption * fuel_cost_per_unit
        return total_cost

    def calculate_selling_profit(self, individual, year):
        """
        Calculate the total selling profit for an individual in a given year.
        """
        total_profit = 0
        for plan in individual:
            vehicle_id = plan['ID']
            vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
            num_vehicles_to_sell = plan.get('Num_Vehicles_to_Sell', 0)
            purchase_year = plan['Year']
            purchase_cost = vehicle['Cost ($)'].values[0]
            resale_value = self.get_resale_value(
                purchase_cost, year - purchase_year)
            total_profit += resale_value * num_vehicles_to_sell
        return total_profit

    def calculate_carbon_emission(self, individual, year):
        """
        Calculate the total carbon emissions for an individual in a given year.
        """
        total_emission = 0
        for plan in individual:
            vehicle_id = plan['ID']
            num_vehicles = plan['Num_Vehicles']
            distance_covered = plan['Distance_per_vehicle']
            fuel_type = self.vehicles_fuels[self.vehicles_fuels['ID']
                                            == vehicle_id]['Fuel'].values[0]
            fuel_consumption = self.vehicles_fuels[self.vehicles_fuels['ID']
                                                   == vehicle_id]['Consumption (unit_fuel/km)'].values[0]
            carbon_emission_per_unit = self.fuels[(self.fuels['Fuel'] == fuel_type) & (
                self.fuels['Year'] == year)]['Emissions (CO2/unit_fuel)'].values[0]
            total_emission += distance_covered * num_vehicles * \
                fuel_consumption * carbon_emission_per_unit
        return total_emission

    ### Hard constraints ###

    def check_purchase_year(self, vehicle_id, purchase_year):
        """
        Check if the vehicle model can only be bought in its specified year.
        """
        vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
        if vehicle.empty:
            return False, f"Vehicle ID {vehicle_id} not found."

        model_year = int(vehicle_id.split('_')[-1])
        if purchase_year != model_year:
            return False, f"Vehicle ID {vehicle_id} can only be bought in the year {model_year}."
        return True, ""

    def check_vehicle_lifetime(self, vehicle_id, current_year):
        """
        Check if the vehicle's lifetime has exceeded 10 years and if it needs to be sold.
        """
        vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
        if vehicle.empty:
            return False, f"Vehicle ID {vehicle_id} not found."

        purchase_year = int(vehicle_id.split('_')[-1])
        if current_year > purchase_year + 10:
            return False, f"Vehicle ID {vehicle_id} must be sold by the end of {purchase_year + 10}."
        return True, ""

    def sell_violation(self, fleet):
        """
        Check for sell constraint violations:
        1. Ensure that the number of vehicles sold is less than the total number of vehicles.
        2. Ensure that no more than 20% of the total vehicles are sold in a year.
        """
        total_vehicles = sum(fleet['Num_Vehicles'])
        total_sold = sum(fleet['Num_Vehicles_Sold'])

        if total_sold > total_vehicles:
            return True
        if total_sold > 0.20 * total_vehicles:
            return True
        return False

    def use_violation(self, fleet):
        """
        Check for use constraint violations:
        Ensure that the number of vehicles used is less than or equal to the total number of vehicles.
        """
        total_vehicles = sum(fleet['Num_Vehicles'])
        total_used = sum(fleet['Num_Vehicles_Used'])

        if total_used > total_vehicles:
            return True
        return False

    def verify_vehicle_yearly_demand(self, vehicle_id):
        """
        Verify if a vehicle can meet the yearly demand for its size and distance bucket.
        """
        vehicle = self.vehicles[self.vehicles['ID'] == vehicle_id]
        if vehicle.empty:
            return f"Vehicle ID {vehicle_id} not found."

        year = vehicle['Year'].values[0]
        size = vehicle['Size'].values[0]
        distance = vehicle['Distance'].values[0]
        yearly_range = vehicle['Yearly range (km)'].values[0]

        demand = self.yearly_demand[year][size][distance]

        if yearly_range >= demand:
            return f"Vehicle ID {vehicle_id} can meet the yearly demand of {demand} km."
        else:
            return f"Vehicle ID {vehicle_id} cannot meet the yearly demand of {demand} km."
