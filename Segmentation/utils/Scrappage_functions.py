## Scrappage functions to be integrated with segmentation model

import pandas as pd
import numpy as np
import time
import pickle

# scrappage function
def return_scrappage(NewCars_by_LSOA, AgeData):

    st = time.time()

    # load delta/gamma lookup based on avg. age
    f = open(r'C:\Users\cenv0795\OneDrive - Nexus365\Code\STEVE\Segmentation\data' + '\\' + 'delta_AvgAge_lookup.pckl',
             'rb')
    AvgAge_d_lookup = pickle.load(f)
    f.close()

    LSOAs = NewCars_by_LSOA.GEO_CODE.unique().tolist()
    years = range(2012, 2051)

    for y in years:
        print(y, time.time() - st)
        for l in LSOAs:

            # return index of this LSOA
            ind = NewCars_by_LSOA[NewCars_by_LSOA['GEO_CODE'] == l].index.values[0]

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
            NewCars_by_LSOA.at[ind, 'TotalCars' + str(y - 1)] -= scrapped_cars
            NewCars_by_LSOA.at[ind, 'NewCars' + str(y)] += scrapped_cars

            # advance the age profile along by one year
            NewAgeData = pd.DataFrame(columns=AgeData.columns)

            # set LSOA
            NewAgeData.at[AgeProfile_ind, 'GEO_CODE'] = l

            for age in range(1, 22):
                NewAgeData.at[AgeProfile_ind, 'AGE_' + str(age)] = int(
                    np.round(AgeProfile_LSOA['AGE_' + str(age - 1)].item(), 0))

            # and add NewCars of this year y (the cars demanded PLUS those to replace the scrapped ones) to the age data at age=0
            NewAgeData.at[AgeProfile_ind, 'AGE_' + str(0)] = int(NewCars_by_LSOA.at[ind, 'NewCars' + str(y)])

            # recalculate average age
            NewAgeData.at[AgeProfile_ind, 'AveAGE'] = sum(
                [NewAgeData.iloc[0]['AGE_' + str(age)] * age for age in range(22)]) / sum(
                [NewAgeData.iloc[0]['AGE_' + str(age)] for age in range(22)])

            # recalculate totalcars - they were DELETED from each age group, and now they are ADDED as new cars
            NewAgeData.at[AgeProfile_ind, 'TotalCars'] = NewCars_by_LSOA.at[ind, 'TotalCars' + str(y)]

            # re-normliase the car counts by age
            for i in range(22):
                NewAgeData.at[AgeProfile_ind, 'AGE_' + str(i)] = int(np.round(
                    NewAgeData.at[AgeProfile_ind, 'AGE_' + str(i)] / sum(
                        [NewAgeData.at[AgeProfile_ind, 'AGE_' + str(j)] for j in range(22)]) * NewAgeData.at[
                        AgeProfile_ind, 'TotalCars'], 0))

            AgeData.loc[AgeProfile_ind, :] = NewAgeData.loc[AgeProfile_ind, :]

    return NewCars_by_LSOA, AgeData