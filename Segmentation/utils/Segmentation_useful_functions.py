import pandas as pd
import numpy as np
import time
import pickle

def return_agedata():
    f = open("./data/AgeProfile_by_LSOA_normalised.pckl", 'rb')
    AgeData = pickle.load(f)
    f.close()

    # load delta lookup
    f = open("./data/delta_AvgAge_lookup.pckl", 'rb')
    AvgAge_d_lookup = pickle.load(f)
    f.close()

    return AgeData, AvgAge_d_lookup

def return_tables(LED_scenario, years, DataPath = "C:/Users/cenv0795/Data/STEVE_DATA/Scen_CarSegments/"):
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

    return Cost_Data, Scen_CarSegments, CT_Fuel, Technology

# SumNew
def return_SumNew(NewCars_by_LSOA, LSOA):
    time_sumnew = time.time()
    """
    -SumNew is a dataframe containing the SUM of new cars needed in each year
    """

    SumNew = pd.DataFrame(columns=['Year', 'TotalCars'])

    SumNew['Year'] = range(
        [int(r[7:]) for r in NewCars_by_LSOA.columns[NewCars_by_LSOA.columns.str.startswith('NewCars')]][0],
        [int(r[7:]) for r in NewCars_by_LSOA.columns[NewCars_by_LSOA.columns.str.startswith('NewCars')]][-1] + 1)
    SumNew['TotalCars'] = NewCars_by_LSOA[(NewCars_by_LSOA.GEO_CODE == LSOA)][
        [N for N in NewCars_by_LSOA.columns if N.startswith('NewCars')]].iloc[0].tolist()

    print('Sumnew took', time.time()-time_sumnew)
    return SumNew

# Size multiplier
def return_Size_Multiplier(Size, PF_Prefix):
    if Size == 1:
        SizeStr = 'Small'
    elif Size == 2:
        SizeStr = 'Medium'
    else:
        SizeStr = 'Large'

    return 'sh' + PF_Prefix + SizeStr

# charging multiplier
def return_Charging_Multipliers(ConsumerSeg, Charging_Access):
    # Charging access is a bit more complicated - they are compound, and they depend on fleet/private
    if ConsumerSeg == 'FleetCar':
        if Charging_Access == 0:  # not aware of EV incentives
            Charging_Multipliers = ['shNotAwareEV']
        elif Charging_Access == 1:  # aware AND access
            Charging_Multipliers = ['shAwareEV', 'shFCertaintyOfAccess']
        else:  # aware but NO access
            Charging_Multipliers = ['shAwareEV', 'shFNoCertaintyOfAccess']
    else:
        if Charging_Access == 0:  # not aware of EV incentives
            Charging_Multipliers = ['shNotAwareEV']
        elif Charging_Access == 1:  # aware AND access
            Charging_Multipliers = ['shAwareEV', 'shPAccessToOC']
        else:  # aware but NO access
            Charging_Multipliers = ['shAwareEV', 'shPNoAccessToOC']

    return Charging_Multipliers

# SumNewCars - BY YEAR
def return_SumNewCars(year, LSOA, SumNewCars, Cars_for_segmentation, Scen_CarSegments, Private_Fleet_Options, Consumer_Segments,
                      Sizes, Charging_Access_Levels):

    time_sumnewcars = time.time()
    """
    SumNewCars
    -SumNewCars is the total number of cars for each segment of the market - private/fleet, size, consumer, charging access
    """
    # append to the last active row on the last year-by-year run
    if SumNewCars.index.empty:
        cnt = 0
    else:
        cnt = SumNewCars.index.tolist()[-1] + 1

    #create new dataframe just for this year
    SumNewCars_year = pd.DataFrame(columns=SumNewCars.columns)

    # Segment data for this year
    Segment_data = Scen_CarSegments[(Scen_CarSegments.Year == year) & (Scen_CarSegments.LSOA == LSOA)]

    for P_F in Private_Fleet_Options:

        ConsumerSegs = Consumer_Segments[Private_Fleet_Options.index(P_F)]

        # for ConsumerSeg, Size, Charging_Access in zip(Consumersegs, Sizes, Charging_Access_levels):
        for ConsumerSeg in ConsumerSegs:

            for Size in Sizes:

                for Charging_Access in Charging_Access_Levels:

                    # return 'Multipliers' (column headings for shares of market)
                    PF_Multiplier = 'sh' + P_F
                    PF_Prefix = P_F[0]  # prefixed by P or F
                    Consumer_Multiplier = 'sh' + PF_Prefix + ConsumerSeg
                    Size_Multiplier = return_Size_Multiplier(Size, PF_Prefix)
                    Charging_Multipliers = return_Charging_Multipliers(ConsumerSeg, Charging_Access)

                    # retrieve numerical values from multipliers
                    PF_Share = Segment_data[PF_Multiplier].tolist()[0]
                    Size_Share = Segment_data[Size_Multiplier].tolist()[0]
                    Consumer_Share = Segment_data[Consumer_Multiplier].tolist()[0]

                    Charging_Share = 1
                    for Charging_Multiplier in Charging_Multipliers:  # compound
                        Charging_Share = Charging_Share * Segment_data[Charging_Multiplier].tolist()[0]

                    # Cars in this segment
                    SegmentCars = Cars_for_segmentation * PF_Share * Consumer_Share * Size_Share * Charging_Share

                    # Write to df
                    SumNewCars_year.at[cnt, 'Year'] = year
                    SumNewCars_year.at[cnt, 'Private_Fleet'] = P_F
                    SumNewCars_year.at[cnt, 'Size'] = Size
                    SumNewCars_year.at[cnt, 'Consumer'] = ConsumerSeg
                    SumNewCars_year.at[cnt, 'Charging_Access'] = Charging_Access
                    SumNewCars_year.at[
                        cnt, 'SumNewCars'] = SegmentCars  # taken out rounding 5/1/22 (compliance with TEAM)

                    cnt += 1

    print('SumNewCars took', time.time() - time_sumnewcars)
    return SumNewCars_year

# ASC based on vehicle type
def return_ASC_VehType(FuelID, HybridFlag):
    # lookup Vehicle type based on FuelID for ASC lookup (below)
    if FuelID == 12:
        ASC_VehType = 'BEV'
    elif (FuelID == 1 and HybridFlag == 1) or (FuelID == 2 and HybridFlag == 1) or (
            FuelID == 1 and HybridFlag == 2) or (FuelID == 2 and HybridFlag == 2):
        ASC_VehType = 'PHEV'
    elif FuelID == 5 or FuelID == 10:
        ASC_VehType = 'GV'
    elif FuelID == 7 or FuelID == 8:
        ASC_VehType = 'BioV'
    elif FuelID == 13 or FuelID == 14:
        ASC_VehType = 'HFCV'
    else:
        ASC_VehType = ''

    return ASC_VehType

# ASC
def return_ASC(year, years, ASC_VehType, Scen_CarSegments, NewCars, Technology, ConsumerSeg, FuelID, HybridFlag):
    ASC_Modifier = 1  # default value. Re-evaluated in loop if conditions are met.

    if ASC_VehType and ConsumerSeg != 'FleetCar':
        ASC = \
            Scen_CarSegments[Scen_CarSegments.Year == year]['ASC_' + ASC_VehType + '_' + ConsumerSeg].tolist()[
                0]

        # calculate ASC_Modifier for various segments and tech
        # all alternative fuel techs. We only get to this loop if ASC_VehType.
        # ASC modifier is calculated on the basis of the year beforehand, so this does not run in the first year
        if years.index(year) > 0:
            # ASC modifier is a linear relationship of -4x + 1. The ASC_Modifier is 1 by default. The less it is (closer to zero) the lower the costs will be
            ASC_Modifier = max(0, -4 * NewCars[(NewCars['TechID'].isin(
                                                   Technology[Technology['FuelID'] == FuelID]['TechID']))
                                               & (NewCars['TechID'].isin(
                Technology[Technology['HybridFlag'] == HybridFlag]['TechID']))
                                               ]['NewCars'].sum() / NewCars['NewCars'].sum() + 1)

            ASC *= ASC_Modifier

    else:
        ASC = 0

    return ASC

# MarketShare - BY YEAR
def return_MarketShare(year, years, MarketShare, Technology, Cost_Data, Private_Fleet_Options, Consumer_Segments, NewCars,
                       Scen_CarSegments):
    time_marketsh = time.time()
    """
    Utility/MarketShare
    -For each year, go through each available technology and calculate the utility and market share of that utility
    """
    # set indexing to be concurrent with overall dataframe
    if MarketShare.index.empty:
        cnt = 0
    else:
        cnt = MarketShare.index.tolist()[-1] + 1

    # make a new dataframe for this year
    MarketShare_year = pd.DataFrame(columns=MarketShare.columns)

    # return available tech in this year
    AvailableTech = Technology[(Technology.Availability <= year) & (Technology.Final_Year >= year)]

    # loop through each available tech and calculate utility, market share
    for i in list(AvailableTech.index.values):

        TechID = Technology.TechID[i]
        Size = Technology.MassCatID[i]
        HybridFlag = Technology.HybridFlag[i]
        FuelID = Technology.FuelID[i]

        # return row of Cost_Data for this TechID in this year
        Cost_Row = Cost_Data[(Cost_Data.TechID == TechID) & (Cost_Data.Year == year)]

        # return ASC_VehType
        ASC_VehType = return_ASC_VehType(FuelID, HybridFlag)

        for P_F in Private_Fleet_Options:

            Private_Fleet = P_F
            ConsumerSegs = Consumer_Segments[Private_Fleet_Options.index(P_F)]

            for ConsumerSeg in ConsumerSegs:
                # retrieve ASC - includes ASC_Modifier (as of 26 May 2022)
                ASC = return_ASC(year, years, ASC_VehType, Scen_CarSegments, NewCars[NewCars.Year == year - 1], Technology, ConsumerSeg,
                                 FuelID, HybridFlag)

                # Calculate Utility (U)
                Utility = Cost_Row['Y1Costs'].tolist()[0] * -0.0003521 + Cost_Row['AnnCostsPriv'].tolist()[
                    0] * -0.0024647 + Cost_Row['ChargingTime'].tolist()[0] * -0.088025 + \
                          Cost_Row['SupplyPenalty'].tolist()[0] * -0.0003521 + ASC + Cost_Row['Range'].tolist()[
                              0] * -0.0003521 + Cost_Row['NoChargingAccessPenalty'].tolist()[0] * -0.0003521

                # Market share = exp(U)
                MarketSh = np.exp(Utility)  # this will always be positive

                MarketShare_year.at[cnt, 'TechID'] = TechID
                MarketShare_year.at[cnt, 'Year'] = year
                MarketShare_year.at[cnt, 'Size'] = Size
                MarketShare_year.at[cnt, 'Private_Fleet'] = Private_Fleet
                MarketShare_year.at[cnt, 'Consumer'] = ConsumerSeg
                MarketShare_year.at[cnt, 'Utility'] = Utility
                MarketShare_year.at[cnt, 'MarketShare'] = MarketSh

                cnt += 1

    print('MarketShare took', time.time()-time_marketsh)
    return MarketShare_year

# Available Tech
def return_AvailableTech(Charging_Access, Technology):
    if Charging_Access == 0:  # not aware of EVs
        AvailableTechIDs = Technology[(Technology.FuelID < 5) & (Technology.HybridFlag < 2)].TechID.tolist()
    elif Charging_Access == 1:  # aware of EVs; has charging access
        AvailableTechIDs = Technology.TechID.tolist()
    else:  # aware of EVs; no charging access
        AvailableTechIDs = Technology[Technology.FuelID != 12].TechID.tolist()

    return AvailableTechIDs


def return_MarketShTot(SumNewCars_year, MarketShare_year, Technology):
    time_marketshtot = time.time()
    """
    MarketShTot
    -MarketShTot(P/F,Size,Consumer,ChargingAccess) is the SUM of all the MarketSh's of all the TechIDs that correspond to that ChargingAccess
    """

    for i in list(SumNewCars_year.index.values):
        # return config for this row
        year, P_F, Size, Consumer, Charging_Access = SumNewCars_year.Year[i], SumNewCars_year.Private_Fleet[i], SumNewCars_year.Size[i], \
                                                     SumNewCars_year.Consumer[i], SumNewCars_year.Charging_Access[i]

        # return MarketShare_year data corresponding to this config
        MS = MarketShare_year[
            (MarketShare_year.Year == year) & (MarketShare_year.Private_Fleet == P_F) & (MarketShare_year.Size == Size) & (
                    MarketShare_year.Consumer == Consumer)]

        AvailableTechIDs = return_AvailableTech(Charging_Access, Technology)

        MarketShTot = MS[MS.TechID.isin(AvailableTechIDs)].MarketShare.sum()

        SumNewCars_year.at[i, 'MarketShTotal'] = MarketShTot

    print('marketshtot took', time.time() - time_marketshtot)
    return SumNewCars_year

# NewCars
def return_NewCars(year, LSOA, NewCars, SumNewCars_year, MarketShare_year, Technology, Consumer_Segments, Private_Fleet_Options, Charging_Access_Levels):
    time_newcars = time.time()
    """
    NewCars
    -NewCars is the output
    -New cars by TechID, Private/Fleet, Size, Consumer, Charging Access
    """
    if NewCars.index.empty:
        cnt = 0
    else:
        cnt = NewCars.index.tolist()[-1] + 1

    NewCars_year = pd.DataFrame(columns=NewCars.columns)

    # retrieve the Technologies available for this year
    AvailableTech = Technology[(Technology.Availability <= year) & (Technology.Final_Year >= year)]

    TechIDs = AvailableTech.TechID.tolist()

    for P_F in Private_Fleet_Options:
        ConsumerSegs = Consumer_Segments[Private_Fleet_Options.index(P_F)]

        for Consumer in ConsumerSegs:

            for Charging_Access in Charging_Access_Levels:

                for TechID in TechIDs:

                    FuelID = AvailableTech[AvailableTech.TechID == TechID].FuelID.tolist()[0]
                    HybridFlag = AvailableTech[AvailableTech.TechID == TechID].HybridFlag.tolist()[0]
                    Size = AvailableTech[AvailableTech.TechID == TechID].MassCatID.tolist()[0]

                    # if statement here - can the Charging_Access have access to this Tech?
                    if Charging_Access == 0:

                        if FuelID < 5 and HybridFlag < 2:

                            MarketSh = \
                            MarketShare_year[(MarketShare_year.Year == year) & (MarketShare_year.Private_Fleet == P_F) & (
                                    MarketShare_year.Size == Size) & (MarketShare_year.Consumer == Consumer) & (
                                                MarketShare_year.TechID == TechID)].MarketShare.tolist()[0]
                            MarketShTot = \
                            SumNewCars_year[(SumNewCars_year.Year == year) & (SumNewCars_year.Private_Fleet == P_F) & (
                                    SumNewCars_year.Size == Size) & (SumNewCars_year.Consumer == Consumer) & (
                                               SumNewCars_year.Charging_Access == Charging_Access)].MarketShTotal.tolist()[
                                0]
                            SumNewC = SumNewCars_year[(SumNewCars_year.Year == year) & (SumNewCars_year.Private_Fleet == P_F) & (
                                    SumNewCars_year.Size == Size) & (SumNewCars_year.Consumer == Consumer) & (
                                                         SumNewCars_year.Charging_Access == Charging_Access)].SumNewCars.tolist()[
                                0]

                            if MarketShTot > 0:
                                NewC = SumNewC * MarketSh / MarketShTot
                            else:
                                NewC = 0

                        else:
                            NewC = 0

                    elif Charging_Access == 1:

                        MarketSh = MarketShare_year[(MarketShare_year.Year == year) & (MarketShare_year.Private_Fleet == P_F) & (
                                MarketShare_year.Size == Size) & (MarketShare_year.Consumer == Consumer) & (
                                                       MarketShare_year.TechID == TechID)].MarketShare.tolist()[0]
                        MarketShTot = SumNewCars_year[(SumNewCars_year.Year == year) & (SumNewCars_year.Private_Fleet == P_F) & (
                                SumNewCars_year.Size == Size) & (SumNewCars_year.Consumer == Consumer) & (
                                                         SumNewCars_year.Charging_Access == Charging_Access)].MarketShTotal.tolist()[
                            0]
                        SumNewC = SumNewCars_year[(SumNewCars_year.Year == year) & (SumNewCars_year.Private_Fleet == P_F) & (
                                SumNewCars_year.Size == Size) & (SumNewCars_year.Consumer == Consumer) & (
                                                     SumNewCars_year.Charging_Access == Charging_Access)].SumNewCars.tolist()[
                            0]

                        if MarketShTot > 0:
                            NewC = SumNewC * MarketSh / MarketShTot
                        else:
                            NewC = 0

                    else:

                        if FuelID != 12:

                            MarketSh = \
                            MarketShare_year[(MarketShare_year.Year == year) & (MarketShare_year.Private_Fleet == P_F) & (
                                    MarketShare_year.Size == Size) & (MarketShare_year.Consumer == Consumer) & (
                                                MarketShare_year.TechID == TechID)].MarketShare.tolist()[0]
                            MarketShTot = \
                            SumNewCars_year[(SumNewCars_year.Year == year) & (SumNewCars_year.Private_Fleet == P_F) & (
                                    SumNewCars_year.Size == Size) & (SumNewCars_year.Consumer == Consumer) & (
                                               SumNewCars_year.Charging_Access == Charging_Access)].MarketShTotal.tolist()[
                                0]
                            SumNewC = SumNewCars_year[(SumNewCars_year.Year == year) & (SumNewCars_year.Private_Fleet == P_F) & (
                                    SumNewCars_year.Size == Size) & (SumNewCars_year.Consumer == Consumer) & (
                                                         SumNewCars_year.Charging_Access == Charging_Access)].SumNewCars.tolist()[
                                0]

                            if MarketShTot > 0:
                                NewC = SumNewC * MarketSh / MarketShTot
                            else:
                                NewC = 0

                        else:
                            NewC = 0

                    # write to DF
                    NewCars_year.at[cnt, 'LSOA'] = LSOA
                    NewCars_year.at[cnt, 'Year'] = year
                    NewCars_year.at[cnt, 'TechID'] = TechID
                    NewCars_year.at[cnt, 'Private_Fleet'] = P_F
                    NewCars_year.at[cnt, 'Size'] = Size
                    NewCars_year.at[cnt, 'Consumer'] = Consumer
                    NewCars_year.at[cnt, 'Charging_Access'] = Charging_Access
                    NewCars_year.at[cnt, 'NewCars'] = NewC  # got rid of rounding, 5/1 (compliance with TEAM)

                    cnt += 1

    print('newcars took', time.time() - time_newcars)
    return NewCars_year

# function to return TotalCars for base year.

def return_TotalCars_base_year(years, LSOA, AgeData, NewCars, TotalCars):

    # this function sets the values of the TotalCars DF for the TotalCars_AGEXX for the base year (2011 is default).

    # return Age Data for this LSOA
    LSOA_AgeData = AgeData[AgeData.GEO_CODE == LSOA]

    NewCars_BaseYear = NewCars[NewCars.Year == years[0]]

    # now, go through each row of that dataframe.
    for i in list(NewCars_BaseYear.index.values):
        TotalCars.loc[i, ['TechID', 'Private_Fleet', 'Size', 'Consumer', 'Charging_Access']] = NewCars_BaseYear.loc[
            i, ['TechID', 'Private_Fleet',
                'Size', 'Consumer',
                'Charging_Access']]


        # set the TotalCars in that age bracket as a proportion of the total
        TotalCars.loc[i, ['TotalCars_AGE' + str(a) for a in range(22)]] = (
                    NewCars_BaseYear.at[i, 'NewCars'] / NewCars_BaseYear['NewCars'].sum() *
                    LSOA_AgeData[['AGE_' + str(a) for a in range(22)]].iloc[0]).tolist()

        # set the TotalCars age zero to the new cars in the base year
        TotalCars.at[i, 'TotalCars_AGE0'] = NewCars_BaseYear.at[i, 'NewCars']

    #set year and LSOA
    TotalCars['Year'] = years[0] - 1
    TotalCars['LSOA'] = LSOA

    return TotalCars

# TotalCars for all other years
def return_TotalCars(year, years, LSOA, TotalCars, NewCars, SumNewCars, AgeData, MarketShare, AvgAge_d_lookup,
                     Cars_per_LSOA, Technology, Cost_Data, Scen_CarSegments, Consumer_Segments, Sizes,
                     Private_Fleet_Options, Charging_Access_Levels):

    # return TotalCars from last year
    TotalCars_lastyear = TotalCars[TotalCars.Year == (year - 1)]

    # return scrappage parameters gamma (service life) + delta (failure rate)
    gamma, delta = return_gamma_delta(AvgAge_d_lookup, AgeData, LSOA)

    # initiate count
    cnt = TotalCars.index.tolist()[-1] + 1

    TotalCars_year = pd.DataFrame(columns=TotalCars.columns)

    for i in list(TotalCars_lastyear.index.values):

        LSOA, TechID, P_F, Size, Consumer, Charging_Access = TotalCars_lastyear.loc[
            i, ['LSOA', 'TechID', 'Private_Fleet', 'Size', 'Consumer', 'Charging_Access']].tolist()

        TotalCars_year.loc[
            cnt, ['LSOA', 'TechID', 'Private_Fleet', 'Size', 'Consumer', 'Charging_Access']] = TotalCars_lastyear.loc[
            i, ['LSOA', 'TechID', 'Private_Fleet', 'Size', 'Consumer', 'Charging_Access']].tolist()

        TotalCars_year.at[cnt, 'Year'] = year

        for age in range(22):

            # return scrappage probability of vehicles this age
            Pscrap = return_Pscrap(age, gamma, delta)

            # return cars from last year
            cars_from_last_year = TotalCars_lastyear.at[i, 'TotalCars_AGE'+str(age)]

            # calculate scrapped cars
            scrapped_cars = Pscrap * TotalCars_lastyear.at[i, 'TotalCars_AGE'+str(age)]

            # calculate total cars (in this age band) this year
            cars_this_year = cars_from_last_year - scrapped_cars

            # Set scrapped cars of this age, TechID, segment
            TotalCars_year.at[cnt, 'ScrappedCars_AGE'+str(age)] = scrapped_cars

            # calculate total cars of this age, TechID, segment
            TotalCars_year.at[cnt, 'TotalCars_AGE'+str(age)] = cars_this_year

        TotalCars_year.loc[cnt, ['TotalCars_AGE' + str(age) for age in range(22)]] = TotalCars_year.loc[
            cnt, ['TotalCars_AGE' + str(age) for age in range(22)]].shift(periods=1)
        cnt += 1

    desired_cars = Cars_per_LSOA[Cars_per_LSOA.GEO_CODE == LSOA]['TotalCars'+str(year)].item()
    cars_we_have = TotalCars_year[['TotalCars_AGE'+str(a) for a in range(22)]].sum().sum()

    Cars_for_segmentation = desired_cars - cars_we_have

    SumNewCars_year = return_SumNewCars(year, LSOA, SumNewCars, Cars_for_segmentation, Scen_CarSegments,
                                   Private_Fleet_Options, Consumer_Segments, Sizes, Charging_Access_Levels)

    MarketShare_year = return_MarketShare(year, years, MarketShare, Technology, Cost_Data, Private_Fleet_Options,
                                     Consumer_Segments, NewCars, Scen_CarSegments)

    SumNewCars_year = return_MarketShTot(SumNewCars_year, MarketShare_year, Technology)

    NewCars_year = return_NewCars(year, LSOA, NewCars, SumNewCars_year, MarketShare_year, Technology, Consumer_Segments,
                             Private_Fleet_Options, Charging_Access_Levels)

    #add new cars to age=0
    for j in list(NewCars_year.index.values):
        LSOA, TechID, P_F, Size, Consumer, Charging_Access = NewCars_year.loc[j, ['LSOA', 'TechID', 'Private_Fleet', 'Size', 'Consumer', 'Charging_Access']]

        if not TotalCars_year[(TotalCars_year.LSOA == LSOA) & (TotalCars_year.TechID == TechID) &
                            (TotalCars_year.Private_Fleet == P_F) & (TotalCars_year.Size == Size) &
                            (TotalCars_year.Consumer == Consumer) & (TotalCars_year.Charging_Access == Charging_Access)].empty:
            set_ind = TotalCars_year[(TotalCars_year.LSOA == LSOA) & (TotalCars_year.TechID == TechID) &
                                (TotalCars_year.Private_Fleet == P_F) & (TotalCars_year.Size == Size) &
                                (TotalCars_year.Consumer == Consumer) & (TotalCars_year.Charging_Access == Charging_Access)].index.item()
        else: #if this TechID isn't already kept track of in TotalCars
            set_ind = TotalCars_year.index.tolist()[-1] + 1

        TotalCars_year.at[set_ind, ['LSOA', 'TechID', 'Private_Fleet', 'Size', 'Consumer', 'Charging_Access']] = [LSOA, TechID, P_F, Size, Consumer, Charging_Access]
        TotalCars_year.at[set_ind, 'Year'] = year
        TotalCars_year.at[set_ind, 'TotalCars_AGE0'] = NewCars_year[(NewCars_year.LSOA == LSOA) & (NewCars_year.TechID == TechID) & (NewCars_year.Private_Fleet == P_F)
                                                  & (NewCars_year.Size == Size) & (NewCars_year.Consumer == Consumer) & (NewCars_year.Charging_Access == Charging_Access)]['NewCars'].item()

    return TotalCars_year, NewCars_year

# a quick function (not originally in TEAM) to return the market share of technologies (BEVs, PHEVs)
def return_MarketShare_Totals(year, LSOA, MarketShare_year, MarketShare_Totals, Technology):
# instantiate new dataframe

    FuelID_dict = {1: 'Gasoline',
                   2: 'Diesel',
                   3: 'Improved Gasoline',
                   4: 'Improved Diesel',
                   5: 'Liquified Petroleum',
                   6: 'Biomethanol',
                   7: 'E85',
                   8: 'Biodiesel',
                   10: 'CNG',
                   11: 'CBG',
                   12: 'Electricity',
                   13: 'Gaseous H',
                   14: 'Liquefied H',
                   15: 'Aviation fuel',
                   16: 'Bio jet fuel'}

    Hybrid_dict = {0: '',
                   1: 'Hybrid',
                   2: 'Plug-in hybrid'}

    if MarketShare_Totals.index.empty:
        count = 0
    else:
        count = MarketShare_Totals.index.tolist()[-1] + 1

    MarketShare_Totals_year = pd.DataFrame(columns=MarketShare_Totals.columns)

    for fuel_key in FuelID_dict:
        for hybrid_key in Hybrid_dict:

            MarketShare_Totals_year.at[count, 'LSOA'] = LSOA
            MarketShare_Totals_year.at[count, 'Year'] = year
            MarketShare_Totals_year.at[count, 'FuelID'] = fuel_key
            MarketShare_Totals_year.at[count, 'Fuel'] = FuelID_dict[fuel_key]
            MarketShare_Totals_year.at[count, 'HybridFlag'] = hybrid_key
            MarketShare_Totals_year.at[count, 'Hybrid'] = Hybrid_dict[hybrid_key]
            MarketShare_Totals_year.at[count, 'MarketShare'] = MarketShare_year[(MarketShare_year.TechID.isin(Technology[Technology.FuelID == fuel_key].TechID)) & (MarketShare_year.TechID.isin(Technology[Technology.HybridFlag == hybrid_key].TechID))].MarketShare.sum() / MarketShare_year.MarketShare.sum()

            count += 1

    return MarketShare_Totals_year

# return delta and gamma scrappage parameters
def return_gamma_delta(AvgAge_d_lookup, AgeData, LSOA, gamma=21):

    # return age profile for this lsoa
    AvgAge_LSOA = AgeData[AgeData.GEO_CODE == LSOA].AveAGE.item()

    delta = AvgAge_d_lookup.iloc[(AvgAge_d_lookup['AvgAge'] - AvgAge_LSOA).abs().argsort()[0]].delta

    return gamma, delta

# return probability of scrappage given age; (gamma, delta)
def return_Pscrap(age, gamma, delta):
    Pscrap = 1 - np.exp(-1 * ((age + delta) / gamma) ** delta) / np.exp(
        -1 * (((age - 1) + delta) / gamma) ** delta)

    return Pscrap