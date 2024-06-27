from fleet_decarbonization_model_final import FleetOptimization

chromosome = [
    # Year 1 (2023)
    {
        'buy': [
            {
                'ID': 'BEV_S1_2023',
                'Num_Vehicles': 5,
                'Distance_per_vehicle(km)': 102000,
                'Distance_bucket': 'D1',
                'Fuel': 'Electricity'
            },
            {
                'ID': 'Diesel_S2_2023',
                'Num_Vehicles': 3,
                'Distance_per_vehicle(km)': 106000,
                'Distance_bucket': 'D2',
                'Fuel': 'B20'
            }
        ],
        'sell': [],
        'use': [
            {
                'ID': 'BEV_S1_2023',
                'Num_Vehicles': 5,
                'Distance_per_vehicle(km)': 102000,
                'Distance_bucket': 'D1',
                'Fuel': 'Electricity'
            },
            {
                'ID': 'Diesel_S2_2023',
                'Num_Vehicles': 3,
                'Distance_per_vehicle(km)': 106000,
                'Distance_bucket': 'D2',
                'Fuel': 'B20'
            }
        ]
    },
    # Year 2 (2024)
    {
        'buy': [
            {
                'ID': 'BEV_S2_2024',
                'Num_Vehicles': 4,
                'Distance_per_vehicle(km)': 104000,
                'Distance_bucket': 'D2',
                'Fuel': 'Electricity'
            }
        ],
        'sell': [
            {
                'ID': 'Diesel_S2_2023',
                'Num_Vehicles': 1,
                'Distance_per_vehicle(km)': 106000,
                'Distance_bucket': 'D2',
                'Fuel': 'B20'
            }
        ],
        'use': [
            {
                'ID': 'BEV_S1_2023',
                'Num_Vehicles': 5,
                'Distance_per_vehicle(km)': 102000,
                'Distance_bucket': 'D1',
                'Fuel': 'Electricity'
            },
            {
                'ID': 'BEV_S2_2024',
                'Num_Vehicles': 4,
                'Distance_per_vehicle(km)': 104000,
                'Distance_bucket': 'D2',
                'Fuel': 'Electricity'
            }
        ]
    },
    # Year 3 (2025)
    {
        'buy': [
            {
                'ID': 'HVO_S3_2025',
                'Num_Vehicles': 6,
                'Distance_per_vehicle(km)': 107000,
                'Distance_bucket': 'D3',
                'Fuel': 'HVO'
            }
        ],
        'sell': [
            {
                'ID': 'BEV_S1_2023',
                'Num_Vehicles': 2,
                'Distance_per_vehicle(km)': 102000,
                'Distance_bucket': 'D1',
                'Fuel': 'Electricity'
            }
        ],
        'use': [
            {
                'ID': 'BEV_S1_2023',
                'Num_Vehicles': 3,
                'Distance_per_vehicle(km)': 102000,
                'Distance_bucket': 'D1',
                'Fuel': 'Electricity'
            },
            {
                'ID': 'BEV_S2_2024',
                'Num_Vehicles': 4,
                'Distance_per_vehicle(km)': 104000,
                'Distance_bucket': 'D2',
                'Fuel': 'Electricity'
            },
            {
                'ID': 'HVO_S3_2025',
                'Num_Vehicles': 6,
                'Distance_per_vehicle(km)': 107000,
                'Distance_bucket': 'D3',
                'Fuel': 'HVO'
            }
        ]
    },
    # Year 4 (2026)
    {
        'buy': [
            {
                'ID': 'LNG_S4_2026',
                'Num_Vehicles': 2,
                'Distance_per_vehicle(km)': 108000,
                'Distance_bucket': 'D4',
                'Fuel': 'LNG'
            }
        ],
        'sell': [
            {
                'ID': 'Diesel_S2_2023',
                'Num_Vehicles': 2,
                'Distance_per_vehicle(km)': 106000,
                'Distance_bucket': 'D2',
                'Fuel': 'B20'
            }
        ],
        'use': [
            {
                'ID': 'BEV_S1_2023',
                'Num_Vehicles': 3,
                'Distance_per_vehicle(km)': 102000,
                'Distance_bucket': 'D1',
                'Fuel': 'Electricity'
            },
            {
                'ID': 'BEV_S2_2024',
                'Num_Vehicles': 4,
                'Distance_per_vehicle(km)': 104000,
                'Distance_bucket': 'D2',
                'Fuel': 'Electricity'
            },
            {
                'ID': 'HVO_S3_2025',
                'Num_Vehicles': 6,
                'Distance_per_vehicle(km)': 107000,
                'Distance_bucket': 'D3',
                'Fuel': 'HVO'
            },
            {
                'ID': 'LNG_S4_2026',
                'Num_Vehicles': 2,
                'Distance_per_vehicle(km)': 108000,
                'Distance_bucket': 'D4',
                'Fuel': 'LNG'
            }
        ]
    },
    # More years can be added similarly...
]


# Example usage
json_file_path = 'dataset/mapping_and_cost_data.json'
fleet_optimization = FleetOptimization(json_file_path)
