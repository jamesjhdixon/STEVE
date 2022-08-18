# Script to change all big input tables (DFs) to dictionaries by variable. Hope to speed up searches
import pickle
import pandas as pd

#Cost_Data
LED_scenario = 'LED1'

# Cost_data
Cost_Data = pd.read_csv(f"./tables/Cost_Data_{LED_scenario}.csv")

# Cost_Data contains all necessary info on technologies. Isolate so it's just cars up to 2050
Cost_Data = Cost_Data[(Cost_Data.VehTypeID == 3) & (Cost_Data.Year <= 2050)]  # VehTypeID = 3 for cars

Cost_Data_dict = dict()

Cost_Data_variables = ['Y1Costs', 'AnnCostsPriv', 'ChargingTime', 'SupplyPenalty', 'Range',
                       'NoChargingAccessPenalty']

# Technology
Technology = pd.read_csv(f"./tables/Technology_{LED_scenario}.csv")

# exclude other vehicle types (cars only)
Technology = Technology[Technology.VehTypeID == 3]

# replace na with 2050 (for final year)
Technology.Final_Year.fillna(int(2050), inplace=True)

# TODO: TECHNOLOGY DICTIONARY
Technology_dict = dict()

Technology_variables = ['MassCatID', 'HybridFlag', 'FuelID']

# take year from Cost_Data
for year in Cost_Data['Year'].tolist():




for TechID in Cost_Data['TechID'].tolist():
    # dictionary for this techid for each YEAR
    year_dict = dict()
    print(f"{Cost_Data['TechID'].tolist().index(TechID)} out of {len(Cost_Data['TechID'].tolist())}")

    for year in Cost_Data['Year'].tolist():

        # dictionary to contain all variables for this year&techId
        sub_dict = dict()
        for variable in Cost_Data_variables:
            sub_dict[variable] = Cost_Data[(Cost_Data['Year'] == year) & (Cost_Data['TechID'] == TechID)][
                variable].item()

        year_dict[year] = sub_dict

    Cost_Data_dict[TechID] = year_dict

