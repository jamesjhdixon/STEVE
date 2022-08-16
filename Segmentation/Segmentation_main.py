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

from Scotland.Segmentation_useful_functions import *

from Calibration.Calibration_functions import *

# load NewCars_by_LSOA
f = open(
    r'C:\Users\cenv0795\OneDrive - Nexus365\Code\Vehicle Ownership Modelling\Scotland' + '\\' + 'Cars_by_LSOA_incScrappage.pckl',
    'rb')
NewCars_by_LSOA = pickle.load(f)
f.close()

LSOAs = NewCars_by_LSOA.GEO_CODE.unique().tolist()
years = range(2012, 2036)

#everything is driven by NewCars_by_LSOA. Select only a subset and everything produced will be a subset
NewCars_by_LSOA = NewCars_by_LSOA[['GEO_CODE'] + ['NewCars'+str(y) for y in years]]

# Load relevant tables - Cost_Data, Scen_CarSegments, CT_Fuel, Technology

TablesDir = r'C:\Users\cenv0795\OneDrive - Nexus365\Code\Vehicle Ownership Modelling\Tables' + '\\'

LED_scenario = 'LED1'

# Cost_data
Cost_Data = pd.read_csv(TablesDir + '\\Cost_Data_' + LED_scenario + '.csv')

# Scen_CarSegments - by LSOA - for Scotland
f = open(TablesDir + '\\Scen_CarSegments_byLSOA_SCOTLAND_' + LED_scenario + '.pckl', 'rb')
Scen_CarSegments = pickle.load(f)  # LSOA-specific
f.close()

# Fuel
CT_Fuel = pd.read_csv(TablesDir + '\\CT_Fuel.csv')  # fuel lookup

# Technology
Technology = pd.read_csv(TablesDir + '\\Technology_' + LED_scenario + '.csv')

# exclude other vehicle types (cars only)
Technology = Technology[Technology.VehTypeID == 3]

# replace na with 2050 (for final year)
Technology.Final_Year.fillna(int(2050), inplace=True)

# Cost_Data contains all necessary info on technologies. Isolate so it's just cars up to 2050
Cost_Data = Cost_Data[(Cost_Data.VehTypeID == 3) & (Cost_Data.Year <= 2050)]  # VehTypeID = 3 for cars

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
increase_accesstoOP = True
increase_certainty_access = True
increase_charging_power = True

if increase_awareness:
    print('Adjusting EV awareness')
    Scen_CarSegments = change_awareness(Scen_CarSegments, shift_yrs=3, multiplier=1.2)

if reduce_supplypenaltyBEV:
    print('Adjusting BEV supply penalty')
    Scen_CarSegments, Cost_Data = change_supply_penalty_BEV(Scen_CarSegments, Cost_Data, Technology, years, shift_yrs=3, multiplier1=0.8, multiplier2=0.05, y1=8)

if reduce_supplypenaltyPHEV:
    print('Adjusting PHEV supply penalty')
    Scen_CarSegments, Cost_Data = change_supply_penalty_PHEV(Scen_CarSegments, Cost_Data, Technology, years, shift_yrs=5, multiplier1=0.2, multiplier2=0.1, y1=9, phase_out_date=2035)

if reduce_supplypenaltyHEV:
    print('Adjusting HEV supply penalty')
    Scen_CarSegments, Cost_Data = change_supply_penalty_HEV(Scen_CarSegments, Cost_Data, Technology, years, shift_yrs=1, multiplier1=2.2, multiplier2=8, y1=13, phase_out_date=2030)

if increase_supplypenaltyPetrol:
    print('Adjusting Petrol supply penalty')
    Scen_CarSegments, Cost_Data = change_supply_penalty_Petrol(Scen_CarSegments, Cost_Data, Technology, years, shift_yrs=5, multiplier1=5, multiplier2=15, y1=8, phase_out_date=2030)

if increase_supplypenaltyDiesel:
    print('Adjusting Diesel supply penalty')
    Scen_CarSegments, Cost_Data = change_supply_penalty_Diesel(Scen_CarSegments, Cost_Data, Technology, years, shift_yrs=2, multiplier1=2, multiplier2=15, y1=9, phase_out_date=2030)

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
    sample_LSOAs = ['S01010818']
    #sample_LSOAs = ['S01006861'] #this one has shFleet = 0, shPrivate != 0
    #sample_LSOAs = ['S01007460'] #this one has shFleet != 0, shPrivate != 0

    for LSOA in sample_LSOAs:
        SumNew = return_SumNew(NewCars_by_LSOA, LSOA)

        SumNewCars = return_SumNewCars(SumNewCars, LSOA, SumNew, Scen_CarSegments, Private_Fleet_Options,
                                       Consumer_Segments, Sizes, Charging_Access_Levels)

        MarketShare = return_MarketShare(MarketShare, SumNew, Technology, Cost_Data, Private_Fleet_Options,
                                         Consumer_Segments, NewCars,
                                         Scen_CarSegments)

        MarketShare_Total = return_MarketShare_Totals(LSOA, MarketShare, SumNew, Technology)

        #COMMENT OUT BELOW IF DON'T NEED DETAILED MARKET BREAKDOWNS!
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

        savedir = r'C:\Users\cenv0795\Data\CREDS 222\Vehicle fleet model\Segmentation data' + '\\'

        f = open(savedir + 'Segmentation_df_Scotland_' + LED_scenario + str(len(sample_LSOAs)) + 'LSOAs.pckl', 'wb')
        pickle.dump(Segmentation_df, f)
        f.close()

    plot = True
    if plot:
        plot_results(Segmentation_df, Technology, LED_scenario, Options)

    plot_MarketShare_Total = False
    if plot_MarketShare_Total:
        plot_MS_Total(MarketShare_Total, Options)

    trial_cnt += 1