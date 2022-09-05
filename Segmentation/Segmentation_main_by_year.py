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

from Segmentation.utils.Segmentation_useful_functions_by_year import *
# from Segmentation.utils.Segmentation_useful_functions import *

from Segmentation.utils.Calibration_functions import *

# load NewCars_per_LSOA - NOT INCLUDING SCRAPPAGE
f = open("./data/Cars_per_LSOA.pckl", "rb")
Cars_per_LSOA = pickle.load(f)
f.close()

LSOAs = Cars_per_LSOA.GEO_CODE.unique().tolist()
years = range(2012, 2050)

#everything is driven by NewCars_per_LSOA. Select only a subset and everything produced will be a subset
NewCars_per_LSOA = Cars_per_LSOA[['GEO_CODE'] + ['NewCars'+str(y) for y in years]]
TotalCars_per_LSOA = Cars_per_LSOA[['GEO_CODE'] + ['TotalCars'+str(y) for y in years]]

# Load age data for scrappage module
AgeData, AvgAge_d_lookup = return_agedata()

# Load relevant tables - Cost_Data, Scen_CarSegments, CT_Fuel, Technology
LED_scenarios = ['LED0', 'LED1', 'LED2']

for LED_scenario in LED_scenarios:
    #LED_scenario = 'LED2'
    Cost_Data, Scen_CarSegments, CT_Fuel, Technology = return_tables(LED_scenario, years)

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

    #Instantiate a NEW dataframe, TotalCars, that *TRACKS* the evolution of the vehicle fleet
    TotalCars = pd.DataFrame(
        columns=['LSOA', 'Year', 'TechID', 'Private_Fleet', 'Size', 'Consumer', 'Charging_Access'] + [
            'TotalCars_AGE' + str(a) for a in range(22)] + ['ScrappedCars_AGE' + str(a) for a in range(22)])

    MarketShare_Totals = pd.DataFrame(columns=['LSOA', 'Year', 'FuelID', 'Fuel', 'HybridFlag', 'Hybrid', 'MarketShare'])

    # Set possible configurations -- Private/Fleet, Size, Consumer, Charging_Access
    Private_Fleet_Options = ['Private', 'Fleet']
    Consumer_Segments = [['Enthusiast', 'Aspirer', 'Mass', 'Resistor'], ['UserChooser', 'FleetCar']]
    Sizes = [1, 2, 3]
    Charging_Access_Levels = [0, 1,
                              2]  # not aware of EV incentives, aware and access to charging, aware but no access to charging

    # Start timer
    segstart = time.time()

    LSOA = 'S01006998' #this one is Aberdeen A52 6HJ (Connor's network)

    #SumNew is calculated ONCE for all years.
    SumNew = return_SumNew(NewCars_per_LSOA, LSOA)

    count = 0

    for year in years:
        st_year = time.time()
        #if year is first year, then calculate data for base year (default = 2011)
        if years.index(year) == 0:
            SumNewCars_year = return_SumNewCars(year, LSOA, SumNewCars, SumNew[SumNew.Year == year].TotalCars.item(),
                                           Scen_CarSegments, Private_Fleet_Options, Consumer_Segments, Sizes,
                                           Charging_Access_Levels)

            MarketShare_year = return_MarketShare(year, years, MarketShare, Technology, Cost_Data, Private_Fleet_Options,
                                             Consumer_Segments, NewCars, Scen_CarSegments)

            SumNewCars_year = return_MarketShTot(SumNewCars_year, MarketShare_year, Technology)

            NewCars_year = return_NewCars(year, LSOA, NewCars, SumNewCars_year, MarketShare_year, Technology, Consumer_Segments,
                                     Private_Fleet_Options, Charging_Access_Levels)

            TotalCars = return_TotalCars_base_year(years, LSOA, AgeData, NewCars_year, TotalCars)

            # clear data to avoid duplicates
            # SumNewCars = SumNewCars.iloc[0:0]
            # MarketShare = MarketShare.iloc[0:0]
            # NewCars = NewCars.iloc[0:0]

        TotalCars_year, NewCars_year = return_TotalCars(year, years, LSOA, TotalCars, NewCars, SumNewCars,
                                                        AgeData, MarketShare, AvgAge_d_lookup, Cars_per_LSOA,
                                                        Technology, Cost_Data, Scen_CarSegments, Consumer_Segments,
                                                        Sizes, Private_Fleet_Options, Charging_Access_Levels)

        TotalCars = TotalCars.append(TotalCars_year)
        NewCars = NewCars.append(NewCars_year)

        print(f"YEAR TIME, {year}: {time.time()-st_year} sec")

    print(f"Overall time: {time.time()-segstart} sec")

    #plot here.
    plot_Fleet_Evolution = True
    if plot_Fleet_Evolution:
        BEV_Share, HEV_Share, PHEV_Share, ICE_Share = return_BEV_share(years, TotalCars, Technology)
        plot_BEV_share(years, LED_scenario, BEV_Share, HEV_Share, PHEV_Share, ICE_Share)




