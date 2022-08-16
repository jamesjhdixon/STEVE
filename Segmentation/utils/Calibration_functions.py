import pandas as pd


def retrieve_real_marketshare_data():
    # load in raw date - veh1153 (DFT licensing stats
    df = pd.read_excel(
        r'C:\Users\cenv0795\OneDrive - Nexus365\Code\Vehicle Ownership Modelling\Calibration\veh1153.xlsx',
        sheet_name='VEH1153a_RoadUsing', skiprows=range(4))
    MS_data = df[(df['Date'].isin([str(y) for y in range(2012, 2022)])) & (df['Geography'] == 'Great Britain') & (
            df['Date Interval'] == 'Annual') & (df['Units'] == 'Percentage of total') & (df['BodyType'] == 'Cars')]
    return MS_data


#plot calibration variables
def plot_calibration_variables(Scen_CarSegments, LSOA, Options, reduce_variables=True):
    import matplotlib.pyplot as plt
    import seaborn as sns
    import colorcet as cc
    sns.set_style('whitegrid')

    calibration_variables = ['shAwareEV',
                             'SPBEVsmall',
                             'SPBEVmedium',
                             'SPBEVlarge',
                             'SPPHEVsmall',
                             'SPPHEVmedium',
                             'SPPHEVlarge',
                             'SPHEVsmall',
                             'SPHEVmedium',
                             'SPHEVlarge',
                             'SPPetrolsmall',
                             'SPPetrolmedium',
                             'SPPetrollarge',
                             'SPDieselsmall',
                             'SPDieselmedium',
                             'SPDiesellarge',
                             'shPAccessToOC',
                             'shFCertaintyOfAccess',
                             'BEVChargingPower']

    if reduce_variables:
        calibration_variables = [c for c in calibration_variables if ('large' not in c) and ('small' not in c)]

    data = Scen_CarSegments[Scen_CarSegments.LSOA == LSOA]

    clrs = sns.color_palette(cc.glasbey, n_colors=len(calibration_variables))
    fig, ax = plt.subplots()
    ax2 = ax.twinx()

    for variable in calibration_variables:
        if variable.startswith('sh'):
            ax.plot(data['Year'], data[variable], label=variable, color=clrs[calibration_variables.index(variable)])
        else:
            ax2.plot(data['Year'], data[variable], label=variable, color=clrs[calibration_variables.index(variable)])

    ax.set_ylabel('Variable')
    ax.legend(loc='upper left')
    ax2.legend(loc='lower right')
    ax.set_title('Calibration variables' + '\n'.join([k for k in Options.keys() if Options[k]]))

    fig.tight_layout()


# plot results in comparison to uptake
def plot_results(Segmentation_df, Technology, LED_Scenario, Options):
    import matplotlib.pyplot as plt
    import seaborn as sns
    import colorcet as cc

    Real_MS_data = retrieve_real_marketshare_data()
    Real_MS_techtypes = ['Petrol',
                         'Diesel',
                         'Hybrid Electric',
                         'Plug-in Hybrid Electric',
                         'Battery Electric']

    sns.set_style('whitegrid')

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

    clrs = sns.color_palette(cc.glasbey_warm, n_colors=int(len(FuelID_dict) * len(Hybrid_dict)))

    fig, ax = plt.subplots(figsize=(10, 6))

    clr_count = 0
    for fuel_key in FuelID_dict:
        for hybrid_key in Hybrid_dict:
            if (fuel_key == 1 and hybrid_key == 0) or (fuel_key == 1 and hybrid_key == 1) or \
                (fuel_key == 1 and hybrid_key == 2) or (fuel_key == 2 and hybrid_key == 0) or \
                (fuel_key == 2 and hybrid_key == 1) or (fuel_key == 2 and hybrid_key == 2) or \
                (fuel_key == 12 and hybrid_key == 0):
                plot_data = []
                for year in Segmentation_df.Year.unique().tolist():
                    plot_data.append(Segmentation_df[(Segmentation_df.Year == year) & (Segmentation_df.TechID.isin(Technology[(Technology.FuelID == fuel_key) & (Technology.HybridFlag == hybrid_key)].TechID))].NewCars.sum() / Segmentation_df[(Segmentation_df.Year == year)].NewCars.sum())

                ax.plot(Segmentation_df.Year.unique().tolist(), plot_data, label=FuelID_dict[fuel_key] + Hybrid_dict[hybrid_key], color=clrs[clr_count])
                clr_count += 1

    realdata_clrs = sns.color_palette(cc.glasbey_cool, n_colors=len(Real_MS_techtypes))
    for tech in Real_MS_techtypes:
        ax.plot(pd.to_numeric(Real_MS_data.Date), Real_MS_data[tech] / 100, label=tech + ' (DVLA data)',
                color=realdata_clrs[Real_MS_techtypes.index(tech)], linestyle='--')

    for t in ax.xaxis.get_majorticklabels(): t.set_fontsize(14)
    for t in ax.yaxis.get_majorticklabels(): t.set_fontsize(14)
    ax.legend(fontsize=10, loc='upper left')
    ax.set_ylabel('Market share (proportion of new registrations)',fontsize=18)

    ax.set_title(LED_Scenario, fontsize=16)
    fig.tight_layout()


def plot_MS_Total(MarketShare_Total, Options):
    import matplotlib.pyplot as plt
    import seaborn as sns
    import colorcet as cc

    Real_MS_data = retrieve_real_marketshare_data()
    Real_MS_techtypes = ['Petrol',
                         'Diesel',
                         'Hybrid Electric',
                         'Plug-in Hybrid Electric',
                         'Battery Electric']

    sns.set_style('whitegrid')

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

    clrs = sns.color_palette(cc.glasbey_warm, n_colors=int(len(FuelID_dict) * len(Hybrid_dict)))

    fig, ax = plt.subplots()

    clr_count = 0
    for fuel_key in FuelID_dict:
        for hybrid_key in Hybrid_dict:
            if (fuel_key == 1 and hybrid_key == 0) or (fuel_key == 1 and hybrid_key == 1) or \
                    (fuel_key == 1 and hybrid_key == 2) or (fuel_key == 2 and hybrid_key == 0) or \
                    (fuel_key == 2 and hybrid_key == 1) or (fuel_key == 2 and hybrid_key == 2) or \
                    (fuel_key == 12 and hybrid_key == 0):
                ax.plot(MarketShare_Total[
                            (MarketShare_Total.FuelID == fuel_key) & (MarketShare_Total.HybridFlag == hybrid_key)].Year,
                        MarketShare_Total[(MarketShare_Total.FuelID == fuel_key) & (
                                    MarketShare_Total.HybridFlag == hybrid_key)].MarketShare,
                        label=FuelID_dict[fuel_key] + Hybrid_dict[hybrid_key], color=clrs[clr_count])
                clr_count += 1

    realdata_clrs = sns.color_palette(cc.glasbey_cool, n_colors=len(Real_MS_techtypes))
    for tech in Real_MS_techtypes:
        ax.plot(pd.to_numeric(Real_MS_data.Date), Real_MS_data[tech] / 100, label=tech + ' (DVLA data)',
                color=realdata_clrs[Real_MS_techtypes.index(tech)], linestyle='--')

    ax.legend()
    ax.set_ylabel('Market share (proportion of new registrations)')

    ax.set_title('; '.join([k for k in Options.keys() if Options[k]]))


# increase share aware of EVs
def change_awareness(Scen_CarSegments, shift_yrs, multiplier):
    # the awareness in each year applied to all LSOAs
    awareness_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].shAwareEV.tolist()

    # make new vector
    new_awareness_vector = len(awareness_vector) * [0]

    # shift it along by shift_yrs
    for i in range(len(awareness_vector) - shift_yrs):
        new_awareness_vector[i] = awareness_vector[i + shift_yrs]

    for i in range(len(new_awareness_vector)):
        if new_awareness_vector[i] == 0:
            new_awareness_vector[i] = 1.0

    # multiply by multiplier. if result is > 1 then set to 1.0
    for i in range(len(new_awareness_vector)):
        if new_awareness_vector[i] * multiplier > 1:
            new_awareness_vector[i] = 1.0
        else:
            new_awareness_vector[i] *= multiplier

    new_shAwareEV = pd.DataFrame({'Year': range(2012, 2051), 'shAwareEV': new_awareness_vector})

    Scen_CarSegments_CertaintyAccess = Scen_CarSegments.copy()

    for year in range(2012, 2051):
        inds = Scen_CarSegments_CertaintyAccess[Scen_CarSegments_CertaintyAccess.Year == year].index.tolist()
        Scen_CarSegments_CertaintyAccess.loc[inds, 'shAwareEV'] = new_shAwareEV[
            new_shAwareEV.Year == year].shAwareEV.item()

    return Scen_CarSegments_CertaintyAccess


# Change the supply penalty for all BEVs - a function that can be called
def change_supply_penalty_BEV(Scen_CarSegments, Cost_Data, Technology, years, shift_yrs, multiplier1, multiplier2, y1):
    # the supply penalties applied to all LSOAs
    SPBEVsmall_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].SPBEVsmall.tolist()
    SPBEVmedium_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].SPBEVmedium.tolist()
    SPBEVlarge_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].SPBEVlarge.tolist()

    # small

    # shift it along by shift_yrs
    new_SPBEVsmall_vector = len(SPBEVsmall_vector) * [0]
    for i in range(len(SPBEVsmall_vector) - shift_yrs):
        new_SPBEVsmall_vector[i] = SPBEVsmall_vector[i + shift_yrs]

    for i in range(len(SPBEVsmall_vector) - shift_yrs, len(SPBEVsmall_vector)):
        new_SPBEVsmall_vector[i] = SPBEVsmall_vector[i]

    # multiply by multipliers. y1 is the year, relative to the start year, where multiplier 2 kicks in
    for i in range(y1):
        new_SPBEVsmall_vector[i] *= multiplier1
    for i in range(y1, len(new_SPBEVsmall_vector)):
        new_SPBEVsmall_vector[i] *= multiplier2

    # medium

    # shift it along by shift_yrs
    new_SPBEVmedium_vector = len(SPBEVmedium_vector) * [0]
    for i in range(len(SPBEVmedium_vector) - shift_yrs):
        new_SPBEVmedium_vector[i] = SPBEVmedium_vector[i + shift_yrs]

    for i in range(len(SPBEVmedium_vector) - shift_yrs, len(SPBEVmedium_vector)):
        new_SPBEVmedium_vector[i] = SPBEVmedium_vector[i]

    # multiply by multipliers. y1 is the year, relative to the start year, where multiplier 2 kicks in
    for i in range(y1):
        new_SPBEVmedium_vector[i] *= multiplier1
    for i in range(y1, len(new_SPBEVmedium_vector)):
        new_SPBEVmedium_vector[i] *= multiplier2

    # large

    # shift by shift_yrs
    new_SPBEVlarge_vector = len(SPBEVlarge_vector) * [0]
    for i in range(len(SPBEVlarge_vector) - shift_yrs):
        new_SPBEVlarge_vector[i] = SPBEVlarge_vector[i + shift_yrs]

    for i in range(len(SPBEVlarge_vector) - shift_yrs, len(SPBEVlarge_vector)):
        new_SPBEVlarge_vector[i] = SPBEVlarge_vector[i]

    # multiply by multipliers. y1 is the year, relative to the start year, where multiplier 2 kicks in
    for i in range(y1):
        new_SPBEVlarge_vector[i] *= multiplier1
    for i in range(y1, len(new_SPBEVlarge_vector)):
        new_SPBEVlarge_vector[i] *= multiplier2

    new_SupplyPenalties = pd.DataFrame({'Year': range(2012, 2051), 'SPBEVsmall': new_SPBEVsmall_vector,
                                        'SPBEVmedium': new_SPBEVmedium_vector, 'SPBEVlarge': new_SPBEVlarge_vector})

    Scen_CarSegments_NewSP = Scen_CarSegments.copy()
    Cost_Data_NewSP = Cost_Data.copy()

    #update Scen_CarSegments and Cost_Data
    size_dict = {1: 'small', 2: 'medium', 3: 'large'}
    for year in years:
        Scen_CarSegments_inds = Scen_CarSegments_NewSP[Scen_CarSegments_NewSP.Year == year].index.tolist()
        for key in size_dict:
            Scen_CarSegments_NewSP.loc[Scen_CarSegments_inds, 'SPBEV'+size_dict[key]] = new_SupplyPenalties[
                new_SupplyPenalties.Year == year]['SPBEV'+size_dict[key]].item()

            Cost_Data_inds = Cost_Data[(Cost_Data.Year == year) & (Cost_Data.TechID.isin(Technology[(Technology.MassCatID == key) & (Technology.FuelID == 12) & (Technology.HybridFlag == 0)].TechID))].index.tolist()
            Cost_Data_NewSP.loc[Cost_Data_inds, 'SupplyPenalty'] = new_SupplyPenalties[new_SupplyPenalties.Year == year]['SPBEV'+size_dict[key]].item()

    return Scen_CarSegments_NewSP, Cost_Data_NewSP


# Change the supply penalty for all HEVs - a function that can be called
def change_supply_penalty_HEV(Scen_CarSegments, Cost_Data, Technology, years, shift_yrs, multiplier1, multiplier2, y1, phase_out_date):
    # the supply penalties applied to all LSOAs
    SPHEVsmall_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].SPHEVsmall.tolist()
    SPHEVmedium_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].SPHEVmedium.tolist()
    SPHEVlarge_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].SPHEVlarge.tolist()

    # small

    # shift it along by shift_yrs
    new_SPHEVsmall_vector = len(SPHEVsmall_vector) * [0]
    for i in range(len(SPHEVsmall_vector) - shift_yrs):
        new_SPHEVsmall_vector[i] = SPHEVsmall_vector[i + shift_yrs]

    for i in range(len(SPHEVsmall_vector) - shift_yrs, len(SPHEVsmall_vector)):
        new_SPHEVsmall_vector[i] = SPHEVsmall_vector[i]

    # multiply by multipliers. y1 is the year, relative to the start year, where multiplier 2 kicks in
    for i in range(y1):
        new_SPHEVsmall_vector[i] *= multiplier1
    for i in range(y1, len(new_SPHEVsmall_vector)):
        new_SPHEVsmall_vector[i] *= multiplier2

    # apply phase out - assign high supply penalty for all elements in vector after phase_out_date
    for i in range(range(2012, 2051).index(phase_out_date), len(new_SPHEVsmall_vector)):
        new_SPHEVsmall_vector[i] = 10e6

    # medium

    # shift it along by shift_yrs
    new_SPHEVmedium_vector = len(SPHEVmedium_vector) * [0]
    for i in range(len(SPHEVmedium_vector) - shift_yrs):
        new_SPHEVmedium_vector[i] = SPHEVmedium_vector[i + shift_yrs]

    for i in range(len(SPHEVmedium_vector) - shift_yrs, len(SPHEVmedium_vector)):
        new_SPHEVmedium_vector[i] = SPHEVmedium_vector[i]

    # multiply by multipliers. y1 is the year, relative to the start year, where multiplier 2 kicks in
    for i in range(y1):
        new_SPHEVmedium_vector[i] *= multiplier1
    for i in range(y1, len(new_SPHEVmedium_vector)):
        new_SPHEVmedium_vector[i] *= multiplier2

    # apply phase out - assign high supply penalty for all elements in vector after phase_out_date
    for i in range(range(2012, 2051).index(phase_out_date), len(new_SPHEVmedium_vector)):
        new_SPHEVmedium_vector[i] = 10e6

    # large

    # shift by shift_yrs
    new_SPHEVlarge_vector = len(SPHEVlarge_vector) * [0]
    for i in range(len(SPHEVlarge_vector) - shift_yrs):
        new_SPHEVlarge_vector[i] = SPHEVlarge_vector[i + shift_yrs]

    for i in range(len(SPHEVlarge_vector) - shift_yrs, len(SPHEVlarge_vector)):
        new_SPHEVlarge_vector[i] = SPHEVlarge_vector[i]

    # multiply by multipliers. y1 is the year, relative to the start year, where multiplier 2 kicks in
    for i in range(y1):
        new_SPHEVlarge_vector[i] *= multiplier1
    for i in range(y1, len(new_SPHEVlarge_vector)):
        new_SPHEVlarge_vector[i] *= multiplier2

    # apply phase out - assign high supply penalty for all elements in vector after phase_out_date
    for i in range(range(2012, 2051).index(phase_out_date), len(new_SPHEVlarge_vector)):
        new_SPHEVlarge_vector[i] = 10e6

    new_SupplyPenalties = pd.DataFrame({'Year': range(2012, 2051), 'SPHEVsmall': new_SPHEVsmall_vector,
                                        'SPHEVmedium': new_SPHEVmedium_vector, 'SPHEVlarge': new_SPHEVlarge_vector})

    Scen_CarSegments_NewSP = Scen_CarSegments.copy()
    Cost_Data_NewSP = Cost_Data.copy()

    #update Scen_CarSegments and Cost_Data
    size_dict = {1: 'small', 2: 'medium', 3: 'large'}
    for year in years:
        Scen_CarSegments_inds = Scen_CarSegments_NewSP[Scen_CarSegments_NewSP.Year == year].index.tolist()
        for key in size_dict:
            Scen_CarSegments_NewSP.loc[Scen_CarSegments_inds, 'SPHEV'+size_dict[key]] = new_SupplyPenalties[
                new_SupplyPenalties.Year == year]['SPHEV'+size_dict[key]].item()

            Cost_Data_inds = Cost_Data[(Cost_Data.Year == year) & (Cost_Data.TechID.isin(Technology[(Technology.MassCatID == key) & (Technology.FuelID.isin(range(1, 5))) & (Technology.HybridFlag == 1)].TechID))].index.tolist()
            Cost_Data_NewSP.loc[Cost_Data_inds, 'SupplyPenalty'] = new_SupplyPenalties[new_SupplyPenalties.Year == year]['SPHEV'+size_dict[key]].item()

    return Scen_CarSegments_NewSP, Cost_Data_NewSP


# Change the supply penalty for all PHEVs - a function that can be called
def change_supply_penalty_PHEV(Scen_CarSegments, Cost_Data, Technology, years, shift_yrs, multiplier1, multiplier2, y1, phase_out_date):
    # the supply penalties applied to all LSOAs
    SPPHEVsmall_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].SPPHEVsmall.tolist()
    SPPHEVmedium_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].SPPHEVmedium.tolist()
    SPPHEVlarge_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].SPPHEVlarge.tolist()

    # small

    # shift it along by shift_yrs
    new_SPPHEVsmall_vector = len(SPPHEVsmall_vector) * [0]
    for i in range(len(SPPHEVsmall_vector) - shift_yrs):
        new_SPPHEVsmall_vector[i] = SPPHEVsmall_vector[i + shift_yrs]

    for i in range(len(SPPHEVsmall_vector) - shift_yrs, len(SPPHEVsmall_vector)):
        new_SPPHEVsmall_vector[i] = SPPHEVsmall_vector[i]

    # multiply by multipliers. y1 is the year, relative to the start year, where multiplier 2 kicks in
    for i in range(y1):
        new_SPPHEVsmall_vector[i] *= multiplier1
    for i in range(y1, len(new_SPPHEVsmall_vector)):
        new_SPPHEVsmall_vector[i] *= multiplier2

    # apply phase out - assign high supply penalty for all elements in vector after phase_out_date
    for i in range(range(2012, 2051).index(phase_out_date), len(new_SPPHEVsmall_vector)):
        new_SPPHEVsmall_vector[i] = 10e6

    # medium

    # shift it along by shift_yrs
    new_SPPHEVmedium_vector = len(SPPHEVmedium_vector) * [0]
    for i in range(len(SPPHEVmedium_vector) - shift_yrs):
        new_SPPHEVmedium_vector[i] = SPPHEVmedium_vector[i + shift_yrs]

    for i in range(len(SPPHEVmedium_vector) - shift_yrs, len(SPPHEVmedium_vector)):
        new_SPPHEVmedium_vector[i] = SPPHEVmedium_vector[i]

    # multiply by multipliers. y1 is the year, relative to the start year, where multiplier 2 kicks in
    for i in range(y1):
        new_SPPHEVmedium_vector[i] *= multiplier1
    for i in range(y1, len(new_SPPHEVmedium_vector)):
        new_SPPHEVmedium_vector[i] *= multiplier2

    # apply phase out - assign high supply penalty for all elements in vector after phase_out_date
    for i in range(range(2012, 2051).index(phase_out_date), len(new_SPPHEVmedium_vector)):
        new_SPPHEVmedium_vector[i] = 10e6

    # large

    # shift by shift_yrs
    new_SPPHEVlarge_vector = len(SPPHEVlarge_vector) * [0]
    for i in range(len(SPPHEVlarge_vector) - shift_yrs):
        new_SPPHEVlarge_vector[i] = SPPHEVlarge_vector[i + shift_yrs]

    for i in range(len(SPPHEVlarge_vector) - shift_yrs, len(SPPHEVlarge_vector)):
        new_SPPHEVlarge_vector[i] = SPPHEVlarge_vector[i]

    # multiply by multipliers. y1 is the year, relative to the start year, where multiplier 2 kicks in
    for i in range(y1):
        new_SPPHEVlarge_vector[i] *= multiplier1
    for i in range(y1, len(new_SPPHEVlarge_vector)):
        new_SPPHEVlarge_vector[i] *= multiplier2

    # apply phase out - assign high supply penalty for all elements in vector after phase_out_date
    for i in range(range(2012, 2051).index(phase_out_date), len(new_SPPHEVlarge_vector)):
        new_SPPHEVlarge_vector[i] = 10e6

    new_SupplyPenalties = pd.DataFrame({'Year': range(2012, 2051), 'SPPHEVsmall': new_SPPHEVsmall_vector,
                                        'SPPHEVmedium': new_SPPHEVmedium_vector, 'SPPHEVlarge': new_SPPHEVlarge_vector})

    Scen_CarSegments_NewSP = Scen_CarSegments.copy()
    Cost_Data_NewSP = Cost_Data.copy()

    #update Scen_CarSegments and Cost_Data
    size_dict = {1: 'small', 2: 'medium', 3: 'large'}
    for year in years:
        Scen_CarSegments_inds = Scen_CarSegments_NewSP[Scen_CarSegments_NewSP.Year == year].index.tolist()
        for key in size_dict:
            Scen_CarSegments_NewSP.loc[Scen_CarSegments_inds, 'SPPHEV'+size_dict[key]] = new_SupplyPenalties[
                new_SupplyPenalties.Year == year]['SPPHEV'+size_dict[key]].item()

            Cost_Data_inds = Cost_Data[(Cost_Data.Year == year) & (Cost_Data.TechID.isin(Technology[(Technology.MassCatID == key) & (Technology.FuelID.isin(range(1, 5))) & (Technology.HybridFlag == 2)].TechID))].index.tolist()
            Cost_Data_NewSP.loc[Cost_Data_inds, 'SupplyPenalty'] = new_SupplyPenalties[new_SupplyPenalties.Year == year]['SPPHEV'+size_dict[key]].item()

    return Scen_CarSegments_NewSP, Cost_Data_NewSP


# Change the supply penalty for all PETROLs - a function that can be called
def change_supply_penalty_Petrol(Scen_CarSegments, Cost_Data, Technology, years, shift_yrs, multiplier1, multiplier2, y1, phase_out_date):
    # the supply penalties applied to all LSOAs
    SPPetrolsmall_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].SPPetrolsmall.tolist()
    SPPetrolmedium_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].SPPetrolmedium.tolist()
    SPPetrollarge_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].SPPetrollarge.tolist()

    # small

    # shift it along by shift_yrs
    new_SPPetrolsmall_vector = len(SPPetrolsmall_vector) * [0]
    for i in range(len(SPPetrolsmall_vector) - shift_yrs):
        new_SPPetrolsmall_vector[i] = SPPetrolsmall_vector[i + shift_yrs]

    for i in range(len(SPPetrolsmall_vector) - shift_yrs, len(SPPetrolsmall_vector)):
        new_SPPetrolsmall_vector[i] = SPPetrolsmall_vector[i]

    # multiply by multipliers. y1 is the year, relative to the start year, where multiplier 2 kicks in
    for i in range(y1):
        new_SPPetrolsmall_vector[i] *= multiplier1
    for i in range(y1, len(new_SPPetrolsmall_vector)):
        new_SPPetrolsmall_vector[i] *= multiplier2

    # apply phase out - assign high supply penalty for all elements in vector after phase_out_date
    for i in range(range(2012, 2051).index(phase_out_date), len(new_SPPetrolsmall_vector)):
        new_SPPetrolsmall_vector[i] = 10e6

    # medium

    # shift it along by shift_yrs
    new_SPPetrolmedium_vector = len(SPPetrolmedium_vector) * [0]
    for i in range(len(SPPetrolmedium_vector) - shift_yrs):
        new_SPPetrolmedium_vector[i] = SPPetrolmedium_vector[i + shift_yrs]

    for i in range(len(SPPetrolmedium_vector) - shift_yrs, len(SPPetrolmedium_vector)):
        new_SPPetrolmedium_vector[i] = SPPetrolmedium_vector[i]

    # multiply by multipliers. y1 is the year, relative to the start year, where multiplier 2 kicks in
    for i in range(y1):
        new_SPPetrolmedium_vector[i] *= multiplier1
    for i in range(y1, len(new_SPPetrolmedium_vector)):
        new_SPPetrolmedium_vector[i] *= multiplier2

    # apply phase out - assign high supply penalty for all elements in vector after phase_out_date
    for i in range(range(2012, 2051).index(phase_out_date), len(new_SPPetrolmedium_vector)):
        new_SPPetrolmedium_vector[i] = 10e6

    # large

    # shift by shift_yrs
    new_SPPetrollarge_vector = len(SPPetrollarge_vector) * [0]
    for i in range(len(SPPetrollarge_vector) - shift_yrs):
        new_SPPetrollarge_vector[i] = SPPetrollarge_vector[i + shift_yrs]

    for i in range(len(SPPetrollarge_vector) - shift_yrs, len(SPPetrollarge_vector)):
        new_SPPetrollarge_vector[i] = SPPetrollarge_vector[i]

    # multiply by multipliers. y1 is the year, relative to the start year, where multiplier 2 kicks in
    for i in range(y1):
        new_SPPetrollarge_vector[i] *= multiplier1
    for i in range(y1, len(new_SPPetrollarge_vector)):
        new_SPPetrollarge_vector[i] *= multiplier2

    # apply phase out - assign high supply penalty for all elements in vector after phase_out_date
    for i in range(range(2012, 2051).index(phase_out_date), len(new_SPPetrollarge_vector)):
        new_SPPetrollarge_vector[i] = 10e6

    new_SupplyPenalties = pd.DataFrame({'Year': range(2012, 2051), 'SPPetrolsmall': new_SPPetrolsmall_vector,
                                        'SPPetrolmedium': new_SPPetrolmedium_vector,
                                        'SPPetrollarge': new_SPPetrollarge_vector})

    Scen_CarSegments_NewSP = Scen_CarSegments.copy()
    Cost_Data_NewSP = Cost_Data.copy()

    #update Scen_CarSegments and Cost_Data
    size_dict = {1: 'small', 2: 'medium', 3: 'large'}
    for year in years:
        Scen_CarSegments_inds = Scen_CarSegments_NewSP[Scen_CarSegments_NewSP.Year == year].index.tolist()
        for key in size_dict:
            Scen_CarSegments_NewSP.loc[Scen_CarSegments_inds, 'SPPetrol'+size_dict[key]] = new_SupplyPenalties[
                new_SupplyPenalties.Year == year]['SPPetrol'+size_dict[key]].item()

            Cost_Data_inds = Cost_Data[(Cost_Data.Year == year) & (Cost_Data.TechID.isin(Technology[(Technology.MassCatID == key) & (Technology.FuelID.isin([1, 3])) & (Technology.HybridFlag == 0)].TechID))].index.tolist()
            Cost_Data_NewSP.loc[Cost_Data_inds, 'SupplyPenalty'] = new_SupplyPenalties[new_SupplyPenalties.Year == year]['SPPetrol'+size_dict[key]].item()

    return Scen_CarSegments_NewSP, Cost_Data_NewSP


# Change the supply penalty for all DIESELs - a function that can be called
def change_supply_penalty_Diesel(Scen_CarSegments, Cost_Data, Technology, years, shift_yrs, multiplier1, multiplier2, y1, phase_out_date):
    # the supply penalties applied to all LSOAs
    SPDieselsmall_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].SPDieselsmall.tolist()
    SPDieselmedium_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].SPDieselmedium.tolist()
    SPDiesellarge_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].SPDiesellarge.tolist()

    # small

    # shift it along by shift_yrs
    new_SPDieselsmall_vector = len(SPDieselsmall_vector) * [0]
    for i in range(len(SPDieselsmall_vector) - shift_yrs):
        new_SPDieselsmall_vector[i] = SPDieselsmall_vector[i + shift_yrs]

    for i in range(len(SPDieselsmall_vector) - shift_yrs, len(SPDieselsmall_vector)):
        new_SPDieselsmall_vector[i] = SPDieselsmall_vector[i]

    # multiply by multipliers. y1 is the year, relative to the start year, where multiplier 2 kicks in
    for i in range(y1):
        new_SPDieselsmall_vector[i] *= multiplier1
    for i in range(y1, len(new_SPDieselsmall_vector)):
        new_SPDieselsmall_vector[i] *= multiplier2

    # apply phase out - assign high supply penalty for all elements in vector after phase_out_date
    for i in range(range(2012, 2051).index(phase_out_date), len(new_SPDieselsmall_vector)):
        new_SPDieselsmall_vector[i] = 10e6

    # medium

    # shift it along by shift_yrs
    new_SPDieselmedium_vector = len(SPDieselmedium_vector) * [0]
    for i in range(len(SPDieselmedium_vector) - shift_yrs):
        new_SPDieselmedium_vector[i] = SPDieselmedium_vector[i + shift_yrs]

    for i in range(len(SPDieselmedium_vector) - shift_yrs, len(SPDieselmedium_vector)):
        new_SPDieselmedium_vector[i] = SPDieselmedium_vector[i]

    # multiply by multipliers. y1 is the year, relative to the start year, where multiplier 2 kicks in
    for i in range(y1):
        new_SPDieselmedium_vector[i] *= multiplier1
    for i in range(y1, len(new_SPDieselmedium_vector)):
        new_SPDieselmedium_vector[i] *= multiplier2

    # apply phase out - assign high supply penalty for all elements in vector after phase_out_date
    for i in range(range(2012, 2051).index(phase_out_date), len(new_SPDieselmedium_vector)):
        new_SPDieselmedium_vector[i] = 10e6

    # large

    # shift by shift_yrs
    new_SPDiesellarge_vector = len(SPDiesellarge_vector) * [0]
    for i in range(len(SPDiesellarge_vector) - shift_yrs):
        new_SPDiesellarge_vector[i] = SPDiesellarge_vector[i + shift_yrs]

    for i in range(len(SPDiesellarge_vector) - shift_yrs, len(SPDiesellarge_vector)):
        new_SPDiesellarge_vector[i] = SPDiesellarge_vector[i]

    # multiply by multipliers. y1 is the year, relative to the start year, where multiplier 2 kicks in
    for i in range(y1):
        new_SPDiesellarge_vector[i] *= multiplier1
    for i in range(y1, len(new_SPDiesellarge_vector)):
        new_SPDiesellarge_vector[i] *= multiplier2

    # apply phase out - assign high supply penalty for all elements in vector after phase_out_date
    for i in range(range(2012, 2051).index(phase_out_date), len(new_SPDiesellarge_vector)):
        new_SPDiesellarge_vector[i] = 10e6

    new_SupplyPenalties = pd.DataFrame({'Year': range(2012, 2051), 'SPDieselsmall': new_SPDieselsmall_vector,
                                        'SPDieselmedium': new_SPDieselmedium_vector,
                                        'SPDiesellarge': new_SPDiesellarge_vector})

    Scen_CarSegments_NewSP = Scen_CarSegments.copy()
    Cost_Data_NewSP = Cost_Data.copy()

    #update Scen_CarSegments and Cost_Data
    size_dict = {1: 'small', 2: 'medium', 3: 'large'}
    for year in years:
        Scen_CarSegments_inds = Scen_CarSegments_NewSP[Scen_CarSegments_NewSP.Year == year].index.tolist()
        for key in size_dict:
            Scen_CarSegments_NewSP.loc[Scen_CarSegments_inds, 'SPDiesel'+size_dict[key]] = new_SupplyPenalties[
                new_SupplyPenalties.Year == year]['SPDiesel'+size_dict[key]].item()

            Cost_Data_inds = Cost_Data[(Cost_Data.Year == year) & (Cost_Data.TechID.isin(Technology[(Technology.MassCatID == key) & (Technology.FuelID.isin([2, 4])) & (Technology.HybridFlag == 0)].TechID))].index.tolist()
            Cost_Data_NewSP.loc[Cost_Data_inds, 'SupplyPenalty'] = new_SupplyPenalties[new_SupplyPenalties.Year == year]['SPDiesel'+size_dict[key]].item()

    return Scen_CarSegments_NewSP, Cost_Data_NewSP


# Change the share with access to overnight charging
def change_access_to_OP(Scen_CarSegments, limit):
    # this variable does vary by LSOA, so this calibration method gets rid of that variety. therefore, recommend that
    # it is only used to set a new limit

    Scen_CarSegments_AccessOP = Scen_CarSegments.copy()

    Scen_CarSegments_AccessOP.shPAccessToOC = float(limit)

    return Scen_CarSegments_AccessOP


# Change the certainty of access (fleet)
def change_certainty_of_access(Scen_CarSegments, shift_yrs, multiplier):
    # the awareness in each year applied to all LSOAs
    certainty_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].shFCertaintyOfAccess.tolist()

    # shift it along by shift_yrs
    new_certainty_vector = len(certainty_vector) * [0]
    for i in range(len(certainty_vector) - shift_yrs):
        new_certainty_vector[i] = certainty_vector[i + shift_yrs]

    for i in range(len(new_certainty_vector)):
        if new_certainty_vector[i] == 0:
            new_certainty_vector[i] = 1.0

    # multiply by multiplier. if result is > 1 then set to 1.0
    for i in range(len(new_certainty_vector)):
        if new_certainty_vector[i] * multiplier > 1:
            new_certainty_vector[i] = 1.0
        else:
            new_certainty_vector[i] *= multiplier

    new_shFCertaintyOfAccess = pd.DataFrame({'Year': range(2012, 2051), 'shFCertaintyOfAccess': new_certainty_vector})

    Scen_CarSegments_CertaintyAccess = Scen_CarSegments.copy()

    for year in range(2012, 2051):
        inds = Scen_CarSegments_CertaintyAccess[Scen_CarSegments_CertaintyAccess.Year == year].index.tolist()
        Scen_CarSegments_CertaintyAccess.loc[inds, 'shFCertaintyOfAccess'] = new_shFCertaintyOfAccess[
            new_shFCertaintyOfAccess.Year == year].shFCertaintyOfAccess.item()

    return Scen_CarSegments_CertaintyAccess


# Change the BEV Charging Power (also updates Cost_Data)
def change_BEVChargingPower(Scen_CarSegments, Cost_Data, shift_yrs, multiplier):
    # the BEV charging power in each year applied to all LSOAs
    BEVChargingPower_vector = Scen_CarSegments[
        Scen_CarSegments.LSOA == Scen_CarSegments.LSOA.unique().tolist()[0]].BEVChargingPower.tolist()

    # shift it along by shift_yrs
    new_BEVChargingPower_vector = len(BEVChargingPower_vector) * [0]
    for i in range(len(BEVChargingPower_vector) - shift_yrs):
        new_BEVChargingPower_vector[i] = BEVChargingPower_vector[i + shift_yrs]

    for i in range(len(BEVChargingPower_vector) - shift_yrs, len(new_BEVChargingPower_vector)):
        new_BEVChargingPower_vector[i] = BEVChargingPower_vector[i]

    # multiply by multiplier
    for i in range(len(new_BEVChargingPower_vector)):
        new_BEVChargingPower_vector[i] *= multiplier

    new_BEVChargingPower = pd.DataFrame({'Year': range(2012, 2051), 'BEVChargingPower': new_BEVChargingPower_vector,
                                         'old_BEVChargingPower': BEVChargingPower_vector})

    Scen_CarSegments_BEVChargingPower = Scen_CarSegments.copy()
    Cost_Data_BEVChargingPower = Cost_Data.copy()

    for year in range(2012, 2051):
        Scen_CarSegments_inds = Scen_CarSegments_BEVChargingPower[Scen_CarSegments_BEVChargingPower.Year == year].index.tolist()
        Scen_CarSegments_BEVChargingPower.loc[Scen_CarSegments_inds, 'BEVChargingPower'] = new_BEVChargingPower[
            new_BEVChargingPower.Year == year].BEVChargingPower.item()

        Cost_Data_inds = Cost_Data_BEVChargingPower[Cost_Data_BEVChargingPower.Year == year].index.tolist()
        Cost_Data_BEVChargingPower.loc[Cost_Data_inds, 'ChargingTime'] *= new_BEVChargingPower[new_BEVChargingPower.Year == year].old_BEVChargingPower.item() / new_BEVChargingPower[new_BEVChargingPower.Year == year].BEVChargingPower.item()

    return Scen_CarSegments_BEVChargingPower, Cost_Data_BEVChargingPower
