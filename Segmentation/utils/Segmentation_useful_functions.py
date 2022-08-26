import pandas as pd
import numpy as np
import time
import pickle

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

# SumNewCars
def return_SumNewCars(SumNewCars, LSOA, SumNew, Scen_CarSegments, Private_Fleet_Options, Consumer_Segments,
                      Sizes, Charging_Access_Levels):

    time_sumnewcars = time.time()
    """
    SumNewCars
    -SumNewCars is the total number of cars for each segment of the market - private/fleet, size, consumer, charging access
    """
    cnt = 0

    for year in SumNew.Year.tolist():

        # number of cars in LSOA this year
        TotalCars = SumNew[SumNew.Year == year].TotalCars.tolist()[0]

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
                        SegmentCars = TotalCars * PF_Share * Consumer_Share * Size_Share * Charging_Share

                        # Write to df
                        SumNewCars.at[cnt, 'Year'] = year
                        SumNewCars.at[cnt, 'Private_Fleet'] = P_F
                        SumNewCars.at[cnt, 'Size'] = Size
                        SumNewCars.at[cnt, 'Consumer'] = ConsumerSeg
                        SumNewCars.at[cnt, 'Charging_Access'] = Charging_Access
                        SumNewCars.at[
                            cnt, 'SumNewCars'] = SegmentCars  # taken out rounding 5/1/22 (compliance with TEAM)

                        cnt += 1

    print('SumNewCars took', time.time() - time_sumnewcars)
    return SumNewCars

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
def return_ASC(year, ASC_VehType, Scen_CarSegments, SumNew, NewCars, Technology, ConsumerSeg, FuelID, HybridFlag):
    ASC_Modifier = 1  # default value. Re-evaluated in loop if conditions are met.

    if ASC_VehType and ConsumerSeg != 'FleetCar':
        ASC = \
            Scen_CarSegments[Scen_CarSegments.Year == year]['ASC_' + ASC_VehType + '_' + ConsumerSeg].tolist()[
                0]

        # calculate ASC_Modifier for various segments and tech
        # all alternative fuel techs. We only get to this loop if ASC_VehType.
        # ASC modifier is calculated on the basis of the year beforehand, so this does not run in the first year
        if year != SumNew.Year.iloc[0]:
            # ASC modifier is a linear relationship of -4x + 1. The ASC_Modifier is 1 by default. The less it is (closer to zero) the lower the costs will be
            ASC_Modifier = max(0, -4 * NewCars[(NewCars['Year'] == year - 1) &
                                               (NewCars['TechID'].isin(
                                                   Technology[Technology['FuelID'] == FuelID]['TechID']))
                                               & (NewCars['TechID'].isin(
                Technology[Technology['HybridFlag'] == HybridFlag]['TechID']))
                                               ]['NewCars'].sum() / SumNew[SumNew['Year'] == year - 1][
                                   'TotalCars'].sum() + 1)

            ASC *= ASC_Modifier

    else:
        ASC = 0

    return ASC

# MarketShare
def return_MarketShare(MarketShare, SumNew, Technology, Cost_Data, Private_Fleet_Options, Consumer_Segments, NewCars,
                       Scen_CarSegments):
    time_marketsh = time.time()
    """
    Utility/MarketShare
    -For each year, go through each available technology and calculate the utility and market share of that utility
    """

    cnt = 0

    for year in SumNew.Year.tolist():

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
                    ASC = return_ASC(year, ASC_VehType, Scen_CarSegments, SumNew, NewCars, Technology, ConsumerSeg,
                                     FuelID, HybridFlag)

                    # Calculate Utility (U)
                    Utility = Cost_Row['Y1Costs'].tolist()[0] * -0.0003521 + Cost_Row['AnnCostsPriv'].tolist()[
                        0] * -0.0024647 + Cost_Row['ChargingTime'].tolist()[0] * -0.088025 + \
                              Cost_Row['SupplyPenalty'].tolist()[0] * -0.0003521 + ASC + Cost_Row['Range'].tolist()[
                                  0] * -0.0003521 + Cost_Row['NoChargingAccessPenalty'].tolist()[0] * -0.0003521

                    # Market share = exp(U)
                    MarketSh = np.exp(Utility)  # this will always be positive

                    MarketShare.at[cnt, 'TechID'] = TechID
                    MarketShare.at[cnt, 'Year'] = year
                    MarketShare.at[cnt, 'Size'] = Size
                    MarketShare.at[cnt, 'Private_Fleet'] = Private_Fleet
                    MarketShare.at[cnt, 'Consumer'] = ConsumerSeg
                    MarketShare.at[cnt, 'Utility'] = Utility
                    MarketShare.at[cnt, 'MarketShare'] = MarketSh

                    cnt += 1

    print('MarketShare took', time.time()-time_marketsh)
    return MarketShare

# Available Tech
def return_AvailableTech(Charging_Access, Technology):
    if Charging_Access == 0:  # not aware of EVs
        AvailableTechIDs = Technology[(Technology.FuelID < 5) & (Technology.HybridFlag < 2)].TechID.tolist()
    elif Charging_Access == 1:  # aware of EVs; has charging access
        AvailableTechIDs = Technology.TechID.tolist()
    else:  # aware of EVs; no charging access
        AvailableTechIDs = Technology[Technology.FuelID != 12].TechID.tolist()

    return AvailableTechIDs

# MarketShTot
def return_MarketShTot(SumNewCars, MarketShare, Technology):
    time_marketshtot = time.time()
    """
    MarketShTot
    -MarketShTot(P/F,Size,Consumer,ChargingAccess) is the SUM of all the MarketSh's of all the TechIDs that correspond to that ChargingAccess
    """

    for i in list(SumNewCars.index.values):
        # return config for this row
        year, P_F, Size, Consumer, Charging_Access = SumNewCars.Year[i], SumNewCars.Private_Fleet[i], SumNewCars.Size[i], \
                                                     SumNewCars.Consumer[i], SumNewCars.Charging_Access[i]

        # return MarketShare data corresponding to this config
        MS = MarketShare[
            (MarketShare.Year == year) & (MarketShare.Private_Fleet == P_F) & (MarketShare.Size == Size) & (
                    MarketShare.Consumer == Consumer)]

        AvailableTechIDs = return_AvailableTech(Charging_Access, Technology)

        MarketShTot = MS[MS.TechID.isin(AvailableTechIDs)].MarketShare.sum()

        SumNewCars.at[i, 'MarketShTotal'] = MarketShTot

    print('marketshtot took', time.time() - time_marketshtot)
    return SumNewCars

# NewCars
def return_NewCars(LSOA, NewCars, SumNew, SumNewCars, MarketShare, Technology, Consumer_Segments, Private_Fleet_Options, Charging_Access_Levels):
    time_newcars = time.time()
    """
    NewCars
    -NewCars is the output
    -New cars by TechID, Private/Fleet, Size, Consumer, Charging Access
    """

    cnt = 0
    for year in SumNew.Year.tolist():

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
                                MarketShare[(MarketShare.Year == year) & (MarketShare.Private_Fleet == P_F) & (
                                        MarketShare.Size == Size) & (MarketShare.Consumer == Consumer) & (
                                                    MarketShare.TechID == TechID)].MarketShare.tolist()[0]
                                MarketShTot = \
                                SumNewCars[(SumNewCars.Year == year) & (SumNewCars.Private_Fleet == P_F) & (
                                        SumNewCars.Size == Size) & (SumNewCars.Consumer == Consumer) & (
                                                   SumNewCars.Charging_Access == Charging_Access)].MarketShTotal.tolist()[
                                    0]
                                SumNewC = SumNewCars[(SumNewCars.Year == year) & (SumNewCars.Private_Fleet == P_F) & (
                                        SumNewCars.Size == Size) & (SumNewCars.Consumer == Consumer) & (
                                                             SumNewCars.Charging_Access == Charging_Access)].SumNewCars.tolist()[
                                    0]

                                if MarketShTot > 0:
                                    NewC = SumNewC * MarketSh / MarketShTot
                                else:
                                    NewC = 0

                            else:
                                NewC = 0

                        elif Charging_Access == 1:

                            MarketSh = MarketShare[(MarketShare.Year == year) & (MarketShare.Private_Fleet == P_F) & (
                                    MarketShare.Size == Size) & (MarketShare.Consumer == Consumer) & (
                                                           MarketShare.TechID == TechID)].MarketShare.tolist()[0]
                            MarketShTot = SumNewCars[(SumNewCars.Year == year) & (SumNewCars.Private_Fleet == P_F) & (
                                    SumNewCars.Size == Size) & (SumNewCars.Consumer == Consumer) & (
                                                             SumNewCars.Charging_Access == Charging_Access)].MarketShTotal.tolist()[
                                0]
                            SumNewC = SumNewCars[(SumNewCars.Year == year) & (SumNewCars.Private_Fleet == P_F) & (
                                    SumNewCars.Size == Size) & (SumNewCars.Consumer == Consumer) & (
                                                         SumNewCars.Charging_Access == Charging_Access)].SumNewCars.tolist()[
                                0]

                            if MarketShTot > 0:
                                NewC = SumNewC * MarketSh / MarketShTot
                            else:
                                NewC = 0

                        else:

                            if FuelID != 12:

                                MarketSh = \
                                MarketShare[(MarketShare.Year == year) & (MarketShare.Private_Fleet == P_F) & (
                                        MarketShare.Size == Size) & (MarketShare.Consumer == Consumer) & (
                                                    MarketShare.TechID == TechID)].MarketShare.tolist()[0]
                                MarketShTot = \
                                SumNewCars[(SumNewCars.Year == year) & (SumNewCars.Private_Fleet == P_F) & (
                                        SumNewCars.Size == Size) & (SumNewCars.Consumer == Consumer) & (
                                                   SumNewCars.Charging_Access == Charging_Access)].MarketShTotal.tolist()[
                                    0]
                                SumNewC = SumNewCars[(SumNewCars.Year == year) & (SumNewCars.Private_Fleet == P_F) & (
                                        SumNewCars.Size == Size) & (SumNewCars.Consumer == Consumer) & (
                                                             SumNewCars.Charging_Access == Charging_Access)].SumNewCars.tolist()[
                                    0]

                                if MarketShTot > 0:
                                    NewC = SumNewC * MarketSh / MarketShTot
                                else:
                                    NewC = 0

                            else:
                                NewC = 0

                        # write to DF
                        NewCars.at[cnt, 'LSOA'] = LSOA
                        NewCars.at[cnt, 'Year'] = year
                        NewCars.at[cnt, 'TechID'] = TechID
                        NewCars.at[cnt, 'Private_Fleet'] = P_F
                        NewCars.at[cnt, 'Size'] = Size
                        NewCars.at[cnt, 'Consumer'] = Consumer
                        NewCars.at[cnt, 'Charging_Access'] = Charging_Access
                        NewCars.at[cnt, 'NewCars'] = NewC  # got rid of rounding, 5/1 (compliance with TEAM)

                        cnt += 1

    print('newcars took', time.time() - time_newcars)
    return NewCars

# a quick function (not originally in TEAM) to return the market share of technologies (BEVs, PHEVs)
def return_MarketShare_Totals(LSOA, MarketShare, SumNew, Technology):

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

    #instantiate new dataframe
    MarketShare_Totals = pd.DataFrame(columns=['LSOA', 'Year', 'FuelID', 'Fuel', 'HybridFlag', 'Hybrid', 'MarketShare'])

    count = 0
    for year in SumNew.Year.tolist():
        for fuel_key in FuelID_dict:
            for hybrid_key in Hybrid_dict:

                MarketShare_Totals.at[count, 'LSOA'] = LSOA
                MarketShare_Totals.at[count, 'Year'] = year
                MarketShare_Totals.at[count, 'FuelID'] = fuel_key
                MarketShare_Totals.at[count, 'Fuel'] = FuelID_dict[fuel_key]
                MarketShare_Totals.at[count, 'HybridFlag'] = hybrid_key
                MarketShare_Totals.at[count, 'Hybrid'] = Hybrid_dict[hybrid_key]
                MarketShare_Totals.at[count, 'MarketShare'] = MarketShare[(MarketShare.TechID.isin(Technology[Technology.FuelID == fuel_key].TechID)) & (MarketShare.TechID.isin(Technology[Technology.HybridFlag == hybrid_key].TechID)) & (MarketShare.Year == year)].MarketShare.sum() / MarketShare[MarketShare.Year == year].MarketShare.sum()

                count += 1

    return MarketShare_Totals

# update Cost_Data after Scen_CarSegments has been changed
def update_Cost_Data(Cost_Data, Scen_CarSegments):
    #we need to update SUPPLY PENALTY and CHARGING TIME

    #retrieve vectors from Scen_CarSegments (these are LSOA-insensitive so just pick the first one
    new_BEVChargingPower = Scen_CarSegments[Scen_CarSegments['LSOA'] == Scen_CarSegments.LSOA.unique()[0]].BEVChargingPower.tolist()
    old_BEVChargingPower = Cost_Data

    #assign to relevant

    return Cost_Data

# scrappage function
def return_scrappage(AgeData, years, Cars_per_LSOA):


    LSOAs = Cars_per_LSOA.GEO_CODE.unique().tolist()

    for y in years:
        for l in LSOAs:
            # return index of this LSOA
            ind = Cars_per_LSOA[Cars_per_LSOA['GEO_CODE'] == l].index.values[0]

            # return age profile for this lsoa
            AgeProfile_LSOA = AgeData[AgeData.GEO_CODE == l]
            AgeProfile_ind = AgeProfile_LSOA.index.values[0]

            # look up average age for the LSOA for scrappage probability calc in loop
            AvgAge_LSOA = AgeProfile_LSOA.AveAGE.item()

            # use that average age value to lookup a delta value
            # lookup delta from table by sorting -- https://stackoverflow.com/questions/30112202/how-do-i-find-the-closest-values-in-a-pandas-series-to-an-input-number
            if years.index(y) == 0:  # only do it for the first year
                delta = AvgAge_d_lookup.iloc[(AvgAge_d_lookup['AvgAge'] - AvgAge_LSOA).abs().argsort()[0]].delta

            # gamma = characteristic service life for vehicle type = car
            gamma = 21

            # go through each year in turn and evaluate the proportion of scrapped vehicles
            scrapped_cars = 0
            for age in range(22):
                # calculate probability of scrappage
                Pscrap = 1 - np.exp(-1 * ((age + delta) / gamma) ** delta) / np.exp(
                    -1 * (((age - 1) + delta) / gamma) ** delta)

                # scrapped vehicles for each age is the number of vehicles that age * the probability that one is scrapped
                scrapped = int(np.round(AgeData.loc[AgeProfile_ind, 'AGE_' + str(age)] * Pscrap, 0))

                scrapped_cars += scrapped

                # minus the scrapped vehicles from the Age Profile data of this cell
                AgeData.at[AgeProfile_ind, 'AGE_' + str(age)] -= scrapped

            # MINUS the scrapped cars away from the total cars in year y-1 and ADD them to the new cars
            Cars_per_LSOA.at[ind, 'TotalCars' + str(y - 1)] -= scrapped_cars
            Cars_per_LSOA.at[ind, 'NewCars' + str(y)] += scrapped_cars

            # advance the age profile along by one year
            NewAgeData = pd.DataFrame(columns=AgeData.columns)

            # set LSOA
            NewAgeData.at[AgeProfile_ind, 'GEO_CODE'] = l

            for age in range(1, 22):
                NewAgeData.at[AgeProfile_ind, 'AGE_' + str(age)] = int(
                    np.round(AgeProfile_LSOA['AGE_' + str(age - 1)].item(), 0))

            # and add NewCars of this year y (the cars demanded PLUS those to replace the scrapped ones) to the age data at age=0
            NewAgeData.at[AgeProfile_ind, 'AGE_' + str(0)] = int(Cars_per_LSOA.at[ind, 'NewCars' + str(y)])

            # recalculate average age
            NewAgeData.at[AgeProfile_ind, 'AveAGE'] = sum(
                [NewAgeData.iloc[0]['AGE_' + str(age)] * age for age in range(22)]) / sum(
                [NewAgeData.iloc[0]['AGE_' + str(age)] for age in range(22)])

            # recalculate totalcars - they were DELETED from each age group, and now they are ADDED as new cars
            NewAgeData.at[AgeProfile_ind, 'TotalCars'] = Cars_per_LSOA.at[ind, 'TotalCars' + str(y)]

            # re-normliase the car counts by age 
            for i in range(22):
                NewAgeData.at[AgeProfile_ind, 'AGE_' + str(i)] = int(np.round(
                    NewAgeData.at[AgeProfile_ind, 'AGE_' + str(i)] / sum(
                        [NewAgeData.at[AgeProfile_ind, 'AGE_' + str(j)] for j in range(22)]) * NewAgeData.at[
                        AgeProfile_ind, 'TotalCars'], 0))

            AgeData.loc[AgeProfile_ind, :] = NewAgeData.loc[AgeProfile_ind, :]

    return Cars_per_LSOA, AgeData