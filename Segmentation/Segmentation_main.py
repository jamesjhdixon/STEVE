# import dependencies
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random  # get x random LSOAs
import time

import seaborn as sns

sns.set_style('whitegrid')

from Segmentation.utils.Segmentation_useful_functions import *

from Segmentation.utils.Calibration_functions import *

# data path for bulky data not in online repo
DataPath = "C:/Users/cenv0795/Data/STEVE_DATA/Scen_CarSegments/"

# load NewCars_per_LSOA
f = open("./data/Cars_per_LSOA.pckl", "rb")
Cars_per_LSOA = pickle.load(f)
f.close()

LSOAs = Cars_per_LSOA.GEO_CODE.unique().tolist()
years = range(2012, 2036)

#everything is driven by NewCars_per_LSOA. Select only a subset and everything produced will be a subset
NewCars_per_LSOA = Cars_per_LSOA[['GEO_CODE'] + ['NewCars'+str(y) for y in years]]
TotalCars_per_LSOA = Cars_per_LSOA[['GEO_CODE'] + ['TotalCars'+str(y) for y in years]]

# ---- AGE DATA FOR SCRAPPAGE MODULE ---- #
# load age data
f = open("./data/AgeProfile_by_LSOA_normalised.pckl", 'rb')
AgeData = pickle.load(f)
f.close()

# load delta lookup
f = open("./data/delta_AvgAge_lookup.pckl", 'rb')
AvgAge_d_lookup = pickle.load(f)
f.close()

# ---- AGE DATA FOR SCRAPPAGE MODULE ---- #

# Load relevant tables - Cost_Data, Scen_CarSegments, CT_Fuel, Technology

LED_scenarios = ['LED2']

#LED_scenario = 'LED2'

for LED_scenario in LED_scenarios:

    # Cost_data
    Cost_Data = pd.read_csv(f"./tables/Cost_Data_{LED_scenario}.csv")

    # Scen_CarSegments - by LSOA - for Scotland
    f = open(f"{DataPath}Scen_CarSegments_byLSOA_SCOTLAND_{LED_scenario}.pckl", "rb")
    Scen_CarSegments = pickle.load(f)  # LSOA-specific
    f.close()

    # Fuel
    CT_Fuel = pd.read_csv("./tables/CT_Fuel.csv")  # fuel lookup

    # Technology
    Technology = pd.read_csv(f"./tables/Technology_{LED_scenario}.csv")

    # exclude other vehicle types (cars only)
    Technology = Technology[Technology.VehTypeID == 3]

    # replace na with 2050 (for final year)
    Technology.Final_Year.fillna(int(2050), inplace=True)

    # only used variables (see Segmentation_useful_functions.py)
    Technology = Technology[['TechID', 'Availability', 'Final_Year', 'MassCatID', 'HybridFlag', 'FuelID']]

    # Cost_Data contains all necessary info on technologies. Isolate so it's just cars up to the final year
    Cost_Data = Cost_Data[(Cost_Data.VehTypeID == 3) & (Cost_Data.Year <= years[-1])]  # VehTypeID = 3 for cars

    # only used variables (see Segmentation_useful_functions.py)
    Cost_Data = Cost_Data[['TechID', 'Year', 'Y1Costs', 'AnnCostsPriv', 'ChargingTime', 'SupplyPenalty', 'Range',
                           'NoChargingAccessPenalty']]

    #######
    #Calibration
    #######

    increase_awareness = True
    reduce_supplypenaltyBEV = True
    reduce_supplypenaltyPHEV = True
    reduce_supplypenaltyHEV = True
    reduce_supplypenaltyBEV = True
    increase_supplypenaltyPetrol = True
    increase_supplypenaltyDiesel = True
    increase_accesstoOP = False
    increase_certainty_access = False
    increase_charging_power = False

    if increase_awareness:
        print('Adjusting EV awareness')
        Scen_CarSegments = change_awareness(Scen_CarSegments, shift_yrs=5, multiplier=1.2)

    if reduce_supplypenaltyBEV:
        print('Adjusting BEV supply penalty')
        Scen_CarSegments, Cost_Data = change_supply_penalty_BEV(Scen_CarSegments, Cost_Data, Technology, years, shift_yrs=0, multiplier1=1.8, multiplier2=1.6, multiplier3=0.6, multiplier4=-4, y1=8, y2=14, y3=16)

    if reduce_supplypenaltyPHEV:
        print('Adjusting PHEV supply penalty')
        Scen_CarSegments, Cost_Data = change_supply_penalty_PHEV(Scen_CarSegments, Cost_Data, Technology, years, shift_yrs=0, multiplier1=1, multiplier2=0.3, multiplier3=0.2, y1=5, y2=12, phase_out_date=2035)

    if reduce_supplypenaltyHEV:
        print('Adjusting HEV supply penalty')
        Scen_CarSegments, Cost_Data = change_supply_penalty_HEV(Scen_CarSegments, Cost_Data, Technology, years, shift_yrs=0, multiplier1=2, multiplier2=1.8, multiplier3=2, y1=6, y2=11, phase_out_date=2030)

    if increase_supplypenaltyPetrol:
        print('Adjusting Petrol supply penalty')
        Scen_CarSegments, Cost_Data = change_supply_penalty_Petrol(Scen_CarSegments, Cost_Data, Technology, years, shift_yrs=0, multiplier1=0.4, multiplier2=1.2, multiplier3=2.5, y1=10, y2=13, phase_out_date=2030)

    if increase_supplypenaltyDiesel:
        print('Adjusting Diesel supply penalty')
        Scen_CarSegments, Cost_Data = change_supply_penalty_Diesel(Scen_CarSegments, Cost_Data, Technology, years, shift_yrs=0, multiplier1=0.5, multiplier2=1.2, multiplier3=2.5, y1=9, y2=14, phase_out_date=2030)

    if increase_accesstoOP:
        print('Adjusting access to overnight parking (private vehicles)')
        Scen_CarSegments = change_access_to_OP(Scen_CarSegments, limit=1)

    if increase_certainty_access:
        print('Adjusting certainty of access to overnight parking (fleet vehicles)')
        Scen_CarSegments = change_certainty_of_access(Scen_CarSegments, shift_yrs=5, multiplier=1.2)

    if increase_charging_power:
        print('Adjusting BEV charging power')
        Scen_CarSegments, Cost_Data = change_BEVChargingPower(Scen_CarSegments, Cost_Data, shift_yrs=5, multiplier=2)

    Options = {'increase_awareness':increase_awareness, 'reduce_supplypenaltyBEV':reduce_supplypenaltyBEV,
               'reduce_supplypenaltyPHEV':reduce_supplypenaltyPHEV, 'reduce_supplypenaltyHEV':reduce_supplypenaltyHEV,
               'increase_supplypenaltyPetrol':increase_supplypenaltyPetrol, 'increase_supplypenaltyDiesel':increase_supplypenaltyDiesel,
               'increase_certainty_access':increase_certainty_access, 'increase_charging_power':increase_charging_power}

    #plot calibration?
    plot_calibration = False
    if plot_calibration:
        plot_calibration_variables(Scen_CarSegments, random.sample(LSOAs, 1)[0], Options)

    # Add columns for indiviuals who are not aware of EV incentives, without charging access
    Scen_CarSegments['shNotAwareEV'] = 1 - Scen_CarSegments['shAwareEV']
    Scen_CarSegments['shPNoAccessToOC'] = 1 - Scen_CarSegments['shPAccessToOC']
    Scen_CarSegments['shFNoCertaintyOfAccess'] = 1 - Scen_CarSegments['shFCertaintyOfAccess']

    # Define new dataframes for Utility/MarketSh, SumNewCars/MarketShTotal, NewCars
    SumNewCars = pd.DataFrame(columns=['Year', 'Private_Fleet', 'Size', 'Consumer', 'Charging_Access', 'SumNewCars'])
    MarketShare = pd.DataFrame(columns=['TechID', 'Year', 'Size', 'Private_Fleet', 'Consumer', 'Utility', 'MarketShare'])
    NewCars = pd.DataFrame(
        columns=['LSOA', 'Year', 'TechID', 'Private_Fleet', 'Size', 'Consumer', 'Charging_Access', 'NewCars'])

    #TODO: Instantiate a NEW dataframe, TotalCars, that takes the results of NewCars and adds them to *separate* age bands to allow calculation of scrappage per yr
    TotalCars = pd.DataFrame(
        columns=['LSOA', 'Year', 'TechID', 'Private_Fleet', 'Size', 'Consumer', 'Charging_Access'] + [
            'TotalCars_AGE' + str(a) for a in range(22)])

    #TODO: TotalCars gets passed to the return_NewCars function.

    # Set possible configurations -- Private/Fleet, Size, Consumer, Charging_Access
    Private_Fleet_Options = ['Private', 'Fleet']
    Consumer_Segments = [['Enthusiast', 'Aspirer', 'Mass', 'Resistor'], ['UserChooser', 'FleetCar']]
    Sizes = [1, 2, 3]
    Charging_Access_Levels = [0, 1,
                              2]  # not aware of EV incentives, aware and access to charging, aware but no access to charging

    trial_cnt = 0
    while trial_cnt < 1:

        # Start timer
        segstart = time.time()

        Segmentation_df = pd.DataFrame(
            columns=['LSOA', 'Year', 'TechID', 'Private_Fleet', 'Size', 'Consumer', 'Charging_Access', 'NewCars'])

        LSOA_cnt = 0
        #sample_LSOAs = random.sample(LSOAs, 1)
        sample_LSOAs = ['S01006998'] #this one is Aberdeen A52 6HJ (Connor's network)
        #sample_LSOAs = ['S01006861'] #this one has shFleet = 0, shPrivate != 0
        #sample_LSOAs = ['S01007460'] #this one has shFleet != 0, shPrivate != 0

        for LSOA in sample_LSOAs:
            SumNew = return_SumNew(NewCars_per_LSOA, LSOA)

            SumNewCars = return_SumNewCars(SumNewCars, LSOA, SumNew, Scen_CarSegments, Private_Fleet_Options,
                                           Consumer_Segments, Sizes, Charging_Access_Levels)

            MarketShare = return_MarketShare(MarketShare, SumNew, Technology, Cost_Data, Private_Fleet_Options,
                                             Consumer_Segments, NewCars,
                                             Scen_CarSegments)

            MarketShare_Total = return_MarketShare_Totals(LSOA, MarketShare, SumNew, Technology)

            SumNewCars = return_MarketShTot(SumNewCars, MarketShare, Technology)

            NewCars = return_NewCars(LSOA, NewCars, SumNew, SumNewCars, MarketShare, Technology, Consumer_Segments,
                                     Private_Fleet_Options, Charging_Access_Levels)

            Segmentation_df = Segmentation_df.append(NewCars[NewCars.NewCars > 0])

            LSOA_cnt += 1

            if LSOA_cnt % 10 == 0:
                print(LSOA_cnt)

        print('overall time', time.time()-segstart)

        # Save Segmentation_df here
        save = False
        if save:

            savedir = "C:/Users/cenv0795/Data/CREDS 222/Vehicle fleet model/Segmentation data/"

            f = open(f"{savedir}Segmentation_df_Scotland_{LED_scenario}{str(len(sample_LSOAs))}LSOAs.pckl", "wb")
            pickle.dump(Segmentation_df, f)
            f.close()

        plot = False
        if plot:
            plot_results(Segmentation_df, Technology, LED_scenario, Options)

        plot_MarketShare_Total = False
        if plot_MarketShare_Total:
            plot_MS_Total(MarketShare_Total, Options)

        plot_MarketShare_Total_Aggregated = True
        if plot_MarketShare_Total_Aggregated:
            plot_MS_Total_Aggregated(LSOA, SumNew, MarketShare_Total, years, LED_scenario, proportional=False)


        trial_cnt += 1
