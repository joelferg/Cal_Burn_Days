import datetime as dt

import pandas as pd
import geopandas as gpd
import rasterio as rio
import shapely.geometry as shg

air_basins = gpd.read_file("../raw_data/maps/california-air-resources-board-air-basin-boundaries/CaAirBasin.shp")
basin_crs = air_basins.crs
air_basins['sjv_sv'] = air_basins['NAME'].isin(['Sacramento Valley','San Joaquin Valley'])
sample = air_basins.loc[air_basins['sjv_sv']]
sample['buff'] = sample['geometry'].apply(lambda x: x.buffer(50_000))
sample = sample[['NAME','geometry','buff']]


modis = gpd.read_file("../raw_data/fires/DL_FIRE_M-C61_332621/fire_archive_M-C61_332621.shp")
modis = modis.to_crs(basin_crs)
modis_sample = gpd.sjoin(modis,gpd.GeoDataFrame(sample[['buff']],geometry='buff',crs=basin_crs),predicate="within")
modis_sample = modis_sample.drop(['index_right'],axis=1)
#modis_sample = gpd.sjoin(modis_sample,gpd.GeoDataFrame(sample[['NAME','geometry']],geometry='geometry',crs=basin_crs),predicate="within",how="left")

modis_nrt = gpd.read_file("../raw_data/fires/DL_FIRE_M-C61_332621/fire_nrt_M-C61_332621.shp")
modis_nrt = modis_nrt.to_crs(basin_crs)
modis_nrt_sample = gpd.sjoin(modis_nrt,gpd.GeoDataFrame(sample[['buff']],geometry='buff',crs=basin_crs),predicate="within")
modis_nrt_sample = modis_nrt_sample.drop(['index_right'],axis=1)
#modis_nrt_sample = gpd.sjoin(modis_nrt_sample, gpd.GeoDataFrame(sample[['NAME','geometry']],geometry='geometry',crs=basin_crs),predicate="within",how="left")

viirs = gpd.read_file("../raw_data/fires/DL_FIRE_SV-C2_332623/fire_archive_SV-C2_332623.shp")
viirs = viirs.to_crs(basin_crs)
viirs_sample = gpd.sjoin(viirs,gpd.GeoDataFrame(sample[['buff']],geometry='buff',crs=basin_crs),predicate="within")
#viirs_sample = gpd.sjoin(viirs_sample, gpd.GeoDataFrame(sample[['NAME','geometry']],geometry='geometry',crs=basin_crs),predicate="within",how="left")

all_fires = pd.concat([
    modis_sample[['geometry','ACQ_DATE','ACQ_TIME','SATELLITE','CONFIDENCE','FRP','DAYNIGHT']],
    viirs_sample[['geometry','ACQ_DATE','ACQ_TIME','SATELLITE','CONFIDENCE','FRP','DAYNIGHT']],
    modis_nrt_sample[['geometry','ACQ_DATE','ACQ_TIME','SATELLITE','CONFIDENCE','FRP','DAYNIGHT']]
])

all_fires['ACQ_DATE'] = all_fires['ACQ_DATE'].apply(dt.date.fromisoformat)
all_fires['year'] = all_fires['ACQ_DATE'].apply(lambda x: x.year)
all_fires['month'] = all_fires['ACQ_DATE'].apply(lambda x: x.month)
all_fires['day'] = all_fires['ACQ_DATE'].apply(lambda x: x.day)


crop_fire_dfs = []
for year in range(2005,2023):
    print(year)
    if year < 2008:
        img_year = 2008
    else:
        img_year = year
    img = rio.open(f"../raw_data/sv_sjv_cdl/cdl_{img_year}.tif")
    cdl_crs = img.crs

    year_fires = all_fires.loc[all_fires['year']==year]
    year_fires= year_fires.to_crs(cdl_crs)
    year_fires['coords'] = year_fires['geometry'].apply(lambda x: (x.x,x.y))

    cultivated = [val[0] for val in img.sample(year_fires['coords'].tolist(),2,True)]
    year_fires['cultivated'] = cultivated
    crop = [val[0] for val in img.sample(year_fires['coords'].tolist(),1,True)]
    year_fires['crop'] = crop

    crop_fires = year_fires.loc[year_fires['cultivated']==1]
    crop_fires['fires'] = 1
    crop_fire_dfs.append(crop_fires)

crop_fires = pd.concat(crop_fire_dfs)
crop_fires.to_pickle("../processed_data/cropland_fires.pkl")

crop_fires_basins = gpd.sjoin(crop_fires,gpd.GeoDataFrame(sample[['NAME','geometry']],geometry='geometry',crs=basin_crs),predicate="within")
crop_fires_basins.to_pickle("../processed_data/cropland_fires_basins.pkl")

month_series = crop_fires_basins.groupby(['NAME','year','month','SATELLITE'])['fires'].sum().reset_index()
month_series.to_csv("../processed_data/basin_fire_month_series.csv",index=False)
