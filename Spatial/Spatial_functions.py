import pandas as pd
import numpy as np
import geopandas as gpd

# function to return datazone intersected by node
def return_datazone(node):
    datapath = r"C:\Users\cenv0795\Data\STEVE_DATA\Spatial_Network_data"
    data_zones = gpd.read_file(f"{datapath}/SG_DataZone_Bdry_2011.shp")

    DataZone = ""
    for i in list(data_zones.index.values):
        if node.geometry.intersects(data_zones.geometry[i]):
            DataZone = data_zones.DataZone[i]
            break

    return DataZone