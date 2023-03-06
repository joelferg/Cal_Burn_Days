import os
import datetime as dt

import pandas as pd
import numpy as np
import geopandas as gpd
import shapely.geometry as shg

basin_met = pd.read_pickle("../processed_data/basin_met_clean.pkl")
basin_met['year'] = basin_met['date'].apply(lambda x: x.year)
basin_met['month'] = basin_met['date'].apply(lambda x: x.month)
basin_met['day'] = basin_met['date'].apply(lambda x: x.day)

basin_met['alloc_eq_manual'] = (-1/0.006)* (-170 + (1 * basin_met['am_stab']) + (0.2049159 * basin_met['millibar500_ht'])- (0.3579679 * basin_met['wind_spd']) + (1 * basin_met['aq_fact']))
basin_met['meteorologist']=basin_met['meteorologist'].apply(lambda x: x.lower())

fire_df = pd.read_pickle("../processed_data/cropland_fires_basins.pkl")
fire_df = fire_df.loc[fire_df['NAME']=='Sacramento Valley']
fire_df.loc[fire_df['SATELLITE'].isin(['Aqua','Terra']),'SATELLITE'] = 'Modis'
fire_df = fire_df.groupby(['year','month','day','SATELLITE'])['fires'].sum().reset_index()
fire_df = fire_df[['year','month','day','SATELLITE','fires']].set_index(['year','month','day','SATELLITE']).unstack().reset_index()
fire_df.columns = [col[0]+col[1] for col in fire_df.columns]

basin_met_fires = pd.merge(basin_met,fire_df,
                           on = ['year','month','day'],how="outer")
basin_met_fires['firesModis'] = basin_met_fires['firesModis'].fillna(0)
basin_met_fires.to_csv("../processed_data/sac_alloc_fires.csv", index=False)

pm_dfs = os.listdir("../raw_data/pm25/")
pm_dfs.remove(".DS_Store")
pm = pd.concat([pd.read_pickle(f"../raw_data/pm25/{file}") for file in pm_dfs])
pm = pm[['latitude','longitude','site_number','date_local','time_local','sample_measurement','datum']]
pm['hour'] = pm['time_local'].apply(lambda x: int(x[0:2]))
pm['date_local'] = pm['date_local'].apply(dt.date.fromisoformat)
pm['year'] = pm['date_local'].apply(lambda x: x.year)
pm['month'] = pm['date_local'].apply(lambda x: x.month)
pm['day'] = pm['date_local'].apply(lambda x: x.day)
pm = pm.loc[pm['hour'].isin(range(10,17))]

air_basins = gpd.read_file("../raw_data/maps/california-air-resources-board-air-basin-boundaries/CaAirBasin.shp")
basin_crs = air_basins.crs
sample = air_basins.loc[air_basins['NAME']=='Sacramento Valley']

pm_points = pm[['longitude','latitude','datum']].drop_duplicates()
pm_wgs84 = pm_points.loc[pm_points['datum']=='WGS84']
pm_wgs84['point'] = pm_wgs84.apply(lambda x: shg.Point(x['longitude'],x['latitude']),axis=1)
pm_wgs84 = gpd.GeoDataFrame(pm_wgs84,geometry="point").set_crs("EPSG:4326")
pm_nad83 = pm_points.loc[pm_points['datum']=='NAD83']
pm_nad83['point'] = pm_nad83.apply(lambda x: shg.Point(x['longitude'],x['latitude']),axis=1)
pm_nad83 = gpd.GeoDataFrame(pm_nad83,geometry="point").set_crs("EPSG:4269")
pm_nad83 = pm_nad83.to_crs("EPSG:4326")
pm_points = pm_wgs84.append(pm_nad83)
pm_points = pm_points.to_crs(air_basins.crs)

pm_points = gpd.sjoin(pm_points,
                     gpd.GeoDataFrame(sample[['geometry']],geometry='geometry',crs=basin_crs),
                     predicate = "within")
pm_points = pm_points.drop('index_right',axis=1)

pm_points['buff'] = pm_points['point'].apply(lambda x: x.buffer(50_000))
pm_points = pm_points.set_geometry('buff')

fires = pd.read_pickle("../processed_data/cropland_fires.pkl")
fires.loc[fires['SATELLITE'].isin(['Aqua','Terra']),'SATELLITE'] = 'Modis'
gpd.GeoDataFrame(fires[['year','month','day','fires','geometry','SATELLITE']],geometry='geometry',crs=basin_crs)

pm_fires = gpd.sjoin(pm_points,fires,
                    how="inner",predicate="contains")
pm_fires = pm_fires.groupby(['longitude','latitude','datum','year','month','day','SATELLITE'])['fires'].sum().unstack()
pm_fires.columns = [f"fires{col}" for col in pm_fires.columns]
print(pm_fires.columns)
pm_fires = pm_fires.reset_index()
pm_fires = pd.merge(pm,pm_fires,
                   left_on = ['longitude','latitude','datum','year','month','day'],
                   right_on = ['longitude','latitude','datum','year','month','day'],
                   how='outer')

pm_fires = pm_fires.groupby(['site_number','longitude','latitude','datum','year','month','day','hour']).agg({'date_local':'first','firesModis':'sum','sample_measurement':'mean'}).reset_index()
pm_fires['firesModis'] = pm_fires['firesModis'].fillna(0)
pm_fires = pd.merge(pm_fires,basin_met,
                   on = ['year','month','day'],
                   how="outer")
pm_fires.to_csv("../processed_data/pm_station_fires.csv",index=False)
