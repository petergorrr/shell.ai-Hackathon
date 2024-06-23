import pandas as pd

# Load the data files
demand_df = pd.read_csv('dataset/demand.csv')
vehicles_df = pd.read_csv('dataset/vehicles.csv')

# Merge the dataframes on Year, Size, and Distance
merged_df = pd.merge(vehicles_df, demand_df, how='left', left_on=['Year', 'Size', 'Distance'], right_on=['Year', 'Size', 'Distance'])

# Save the merged dataframe to a new CSV file
merged_df.to_csv('dataset/vehicles_with_demand.csv', index=False)

print("Merged data has been saved to 'vehicles_with_demand.csv'")
