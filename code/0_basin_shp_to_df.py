import pandas as pd
import geopandas as gpd

def to_coords(geom):
    if geom.type=="MultiPolygon":
        coords = [list(x.exterior.coords) for x in geom.geoms]
    else:
        coords = list(geom.exterior.coords)
    return(coords)

air_basins = gpd.read_file("../raw_data/maps/california-air-resources-board-air-basin-boundaries/CaAirBasin.shp")
air_basins = air_basins.to_crs("WGS84")
air_basins['sample'] = air_basins['NAME'].isin(['Sacramento Valley','San Joaquin Valley'])
sample = air_basins.loc[air_basins['sample']]
sample['coords'] = sample['geometry'].apply(to_coords)
sample[['coords','NAME']].to_pickle("../processed_data/sample_region.pkl")
