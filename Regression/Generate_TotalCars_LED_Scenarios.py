import pickle
import pandas as pd
import numpy as np

# years
years = range(2012, 2051)

# total cars (regression output)
f = open("regression/Cars_per_LSOA.pckl", "rb")
TotalCars = pickle.load(f)
f.close()

# load scenarios
TotalCars_by_scenario = pd.read_csv('tables/TotalCarOwnership_by_scenario.csv')

LED_scenarios = ['LED0', 'LED1', 'LED2']

for LED_scenario in LED_scenarios:
    print(f'doing {LED_scenario}')

    # TotalCars_by_scenario[LED_scenario]
    d = TotalCars_by_scenario[LED_scenario]
    d_ser = pd.Series(d.tolist())

    for i in list(TotalCars.index.values):

        t = TotalCars.loc[i, ['TotalCars' + str(y) for y in years]]
        t_ser = pd.Series(t.tolist())

        a = d_ser * t_ser

        TotalCars.loc[i, ['TotalCars' + str(y) for y in years]] = [int(np.round(a_val, 0)) for a_val in a.tolist()]


    # re-adjust new cars
    for year in years:
        TotalCars['NewCars'+str(year)] = TotalCars['TotalCars'+str(year)] - TotalCars['TotalCars'+str(year-1)]

    f = open(f"regression/Cars_per_LSOA_{LED_scenario}.pckl", "wb")
    pickle.dump(TotalCars, f)
    f.close()

