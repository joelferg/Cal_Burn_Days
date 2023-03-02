import pandas as pd
import geopandas as gpd
import shapely.geometry as shg
import datetime
from math import floor
import ee

# Read in air basins and re-project
air_basins = gpd.read_file("../raw_data/maps/california-air-resources-board-air-basin-boundaries/CaAirBasin.shp")
air_basins = air_basins.to_crs("EPSG:4326")
#air_basins.plot()

# Read in fires and make into gdf
fires = pd.read_csv("../raw_data/fires/DL_FIRE_SV-C2_212843/fire_archive_SV-C2_212843.csv")
fires['geometry'] = fires.apply(lambda x: shg.Point((x['longitude'],x['latitude'])), axis=1)
fires = gpd.GeoDataFrame(fires,geometry="geometry").set_crs("EPSG:4326")

# Clean dfs and merge basin name onto fires
air_basins = air_basins[['NAME','geometry']]
fires = fires[['acq_date','acq_time','frp','confidence','longitude','latitude','geometry']]
fires['fires'] = 1
basin_fires = gpd.sjoin(fires,air_basins,how="inner",op="within")
basin_fires = basin_fires.reset_index()
basin_fires['acq_date'] = basin_fires['acq_date'].apply(datetime.date.fromisoformat)
basin_fires['year'] = basin_fires['acq_date'].apply(lambda x: x.year)

# Save it
basin_fires.to_pickle("../processed_data/basin_fires_2012-2020.pkl")

basin_fires = pd.read_pickle("../processed_data/basin_fires_2012-2020.pkl")
sac_fires = basin_fires.loc[basin_fires['NAME']=="Sacramento Valley"]
#basin_fires_2020 = basin_fires.loc[basin_fires['year']==2020]

ee.Initialize()
for year in range(2012,2021):
    if year != 2012:
        cropland = ee.ImageCollection("USDA/NASS/CDL").filterDate(f"{year}-01-01",f"{year+1}-01-01").first()
    else:
        cropland = ee.ImageCollection("USDA/NASS/CDL").filterDate("2013-01-01","2014-01-01").first()
    cropland = cropland.select("cultivated")
    sac_fires_year = sac_fires.loc[sac_fires['year']==year]
    for i in range(1,5):
        print(i)
        start = (i-1)*floor(len(sac_fires_year['index'])/4)
        if i != 4:
            end = (i)*floor(len(sac_fires_year['index'])/4)-1
        else:
            end = len(sac_fires_year['index'])-1

        sac_fires_i = sac_fires_year.iloc[start:end,:]
        sac_fires_i['ee_point'] = sac_fires_i.apply(lambda x: ee.Geometry.Point(x['longitude'],x['latitude']),axis=1)
        sac_fires_i['ee_feature'] = sac_fires_i.apply(lambda x: ee.Feature(x['ee_point'],{'index':x['index'],'year':x['year']}), axis=1)
        ee_sac_fires_i = ee.FeatureCollection(sac_fires_i['ee_feature'].tolist())

        ee_sac_fires_i = ee_sac_fires_i.map(lambda x: x.buffer(30))

        out = cropland.reduceRegions(ee_sac_fires_i,
                                     ee.Reducer.max(),
                                     1)
        task = ee.batch.Export.table.toDrive(collection=out,
                                             folder='cal_fires',
                                                 description=f"sac_fires_cropland_{year}_{i}")
        task.start()
