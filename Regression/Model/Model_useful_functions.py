## Set of useful functions for REGRESSION MODEL:
# - generate Neural Network (NN) model based on data
# - produce total cars per LSOA using saved NN model


import pandas as pd
import pickle
import numpy as np
import tensorflow as tf

# function to generate artificial NN model based on base year (2011) and historical (2001) data
def generate_NN_model():

    return

# function to return number of cars per LSOA using saved NN model
def return_cars_per_LSOA(years, country='Scotland'):

    # load model
    model = tf.keras.models.load_model(f"./Model/{country}model_trained2001_2011")

    # instantiate dataframe for cars by LSOA
    Cars_per_LSOA = pd.DataFrame(columns=['GEO_CODE'] + ['NewCars' + str(y) for y in years])

    # load change DFs
    for year in years:

        f = open(f"./Data/{country}/Change_DataFrames/{country}_ChangeDF_{str(year-1)}_{str(year)}.pckl",
                 "rb")
        df = pickle.load(f)
        f.close()

        # exclude unnecessary columns
        df = df[df.columns.tolist()[df.columns.tolist().index('GEO_CODE'):]]

        # return independent variables
        cols = df.columns.tolist()
        x = [vj for vj in [vi for vi in [v for v in cols if v != 'TotalCars'] if vi != 'GEO_CODE'] if
             vj != 'geometry']  # everything except geo_code, geometry and totalcars

        # convert df to numeric data only
        for xval in x:
            df[xval] = pd.to_numeric(df[xval])

        # input data to model
        X = df[x]

        pred_TotalCars = model.predict(X)

        # add predictions to dataframes
        df.loc[:, 'TotalCars'] = [np.round(y[0]) for y in pred_TotalCars]

        Cars_per_LSOA.loc[:, 'NewCars' + str(year)] = [np.round(y[0]) for y in pred_TotalCars]

    Cars_per_LSOA.loc[:, 'GEO_CODE'] = df.loc[:, 'GEO_CODE']
    #Cars_per_LSOA.loc[:, 'geometry'] = df.loc[:, 'geometry']

    # add totalcars (from base year) to newcars
    f = open(f"./Data/{country}/Base_year/{country}_df2011.pckl", "rb")
    df2011 = pickle.load(f)
    f.close()

    Cars_per_LSOA.loc[:, 'TotalCars' + str(2011)] = df2011.loc[:, 'TotalCars']

    for year in years:
        Cars_per_LSOA.loc[:, 'TotalCars' + str(year)] = Cars_per_LSOA.loc[:,
                                                       'TotalCars' + str(year - 1)] + Cars_per_LSOA.loc[:,
                                                                                   'NewCars' + str(year)]

    f = open(f"./../Segmentation/data/{country}Cars_by_LSOA.pckl", "wb")
    pickle.dump(Cars_per_LSOA, f)
    f.close()

    return Cars_per_LSOA