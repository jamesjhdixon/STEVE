import pickle
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import colorcet as cc

sns.set_style('whitegrid')

LED_scenarios = ['LED0', 'LED1', 'LED2']

def plot_total_registrations(LED_scenario):

    f = open(f'TotalRegistrations_{LED_scenario}.pckl', 'rb')
    TotalRegistrations = pickle.load(f)
    f.close()

    Technology = pd.read_csv(f'tables/Technology_{LED_scenario}.csv')

    FuelIDs = {'Gasoline': 1, 'Diesel': 2, 'Improved Gasoline': 3, 'Improved Diesel': 4, 'LPG': 5, 'Biomethanol': 6,
               'Bioethanol': 7, 'Biodiesel': 8, 'CNG': 10, 'CBG': 11, 'Electricity': 12, 'Gaseous H2': 13,
               'Liquefied H2': 14}

    Grouped_FuelIDs = {'Fossil fuel ICE': [1, 2, 3, 4, 5, 10, 11], 'Biofuels ICE': [6, 7, 8], 'Electric': [12],
                       'HFC': [13, 14]}

    years = range(2012, 2051)

    plot_dict = {}
    for FuelID in FuelIDs:
        plot_dict[FuelID] = []
        for year in years:
            plot_dict[FuelID].append(TotalRegistrations[(TotalRegistrations.Year == year) & (
                TotalRegistrations.TechID.isin(Technology[Technology.FuelID == FuelIDs[FuelID]].TechID))][
                                         ['TotalCars_AGE' + str(k) for k in range(22)]].sum().sum())

    clrs = sns.color_palette(cc.glasbey, n_colors=len(FuelIDs))

    fig, ax = plt.subplots()

    clr_cnt = 0
    for FuelID in FuelIDs:

        ax.plot(years, plot_dict[FuelID], label=FuelID, color=clrs[clr_cnt])
        clr_cnt+=1

    for t in ax.xaxis.get_majorticklabels(): t.set_fontsize(14)
    for t in ax.yaxis.get_majorticklabels(): t.set_fontsize(14)
    ax.legend(fontsize=10, loc='upper left')
    ax.set_ylabel('Total registered vehicles by fuel type', fontsize=18)

    ax.set_title(LED_scenario, fontsize=16)
    fig.tight_layout()

def plot_EV_total_numbers():
    LSOA = 'S01006998'
    LED_scenarios = ['LED0', 'LED1', 'LED2']
    LED_labels = {'LED0':'BaU', 'LED1': 'Shift', 'LED2': 'Transform'}

    years = range(2012, 2051)

    EV_dict = {}
    allcars_dict = {}

    for LED_scenario in LED_scenarios:

        EV_dict[LED_scenario] = []
        allcars_dict[LED_scenario] = []

        f = open(f'TotalRegistrations_{LED_scenario}.pckl', 'rb')
        TotalRegistrations = pickle.load(f)
        f.close()

        Technology = pd.read_csv(f'tables/Technology_{LED_scenario}.csv')

        for year in years:
            EV_dict[LED_scenario].append(TotalRegistrations[(TotalRegistrations.Year == year) & (
                TotalRegistrations.TechID.isin(Technology[Technology.FuelID == 12].TechID))][
                                         ['TotalCars_AGE' + str(k) for k in range(22)]].sum().sum())

            allcars_dict[LED_scenario].append(TotalRegistrations[(TotalRegistrations.Year == year)][
                                         ['TotalCars_AGE' + str(k) for k in range(22)]].sum().sum())

    clrs = sns.color_palette(cc.glasbey, n_colors=len(LED_scenarios))

    fig, ax = plt.subplots(figsize=(10, 6))

    clr_cnt = 0
    for LED_scenario in LED_scenarios:
        ax.plot(years, EV_dict[LED_scenario], label='BEVs, '+LED_labels[LED_scenario], color=clrs[clr_cnt], linestyle='-')
        ax.plot(years, allcars_dict[LED_scenario], label='All cars, '+LED_labels[LED_scenario], color=clrs[clr_cnt], linestyle='--')
        clr_cnt += 1

    for t in ax.xaxis.get_majorticklabels(): t.set_fontsize(14)
    for t in ax.yaxis.get_majorticklabels(): t.set_fontsize(14)
    ax.legend(fontsize=10, loc='upper left')
    ax.set_ylabel('Total registered cars by LED scenario', fontsize=18)

    ax.set_title(LSOA, fontsize=16)
    fig.tight_layout()
    plt.savefig(f'Total_EV_numbers_by_LED_Scenario_{LSOA}.png')