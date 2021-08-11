import pandas as pd
import datetime
import shapely.geometry as shg
import geopandas as gpd
import os

pm_dfs = os.listdir("../raw_data/pm25/")
pm_dfs.remove(".DS_Store")
pm = pd.concat([pd.read_pickle(f"../raw_data/pm25/{file}") for file in pm_dfs])
pm = pm[['latitude','longitude','date_local','time_local','sample_measurement','datum']]

fire_dfs = os.listdir("../processed_data/cropland_fires/")
fire_dfs.remove(".DS_Store")
fires_2020 = pd.concat([pd.read_csv(f"../processed_data/cropland_fires/{df}") for df in fire_dfs])

sac_fire_dfs = os.listdir("../processed_data/sac_fires_2012-2019/")
sac_cropland = pd.concat([pd.read_csv(f"../processed_data/sac_fires_2012-2019/{df}") for df in sac_fire_dfs])

basin_fires = pd.read_pickle("../processed_data/basin_fires_2012-2020.pkl")
sac_fires = basin_fires.loc[basin_fires['NAME']=="Sacramento Valley"]
cropland_fires = pd.concat([sac_cropland,fires_2020])
cropland_fires = cropland_fires.loc[cropland_fires['max']==2]
sac_cropland_fires = pd.merge(sac_fires,cropland_fires['index'],
                             on='index')

basin_met = pd.read_pickle("../processed_data/basin_met_clean.pkl")
basin_met = basin_met[['date','burn_dec_3000','aq_fact','alloc_eq','arb_rev_basin_alloc']]

sac_cfires_daily = sac_cropland_fires.groupby('acq_date')['fires'].sum()
basin_met_fires = pd.merge(basin_met,sac_cfires_daily,
                           left_on="date",right_on="acq_date",how="left")
basin_met_fires['fires'] = basin_met_fires['fires'].fillna(0)
basin_met_fires['year'] = basin_met_fires['date'].apply(lambda x: x.year)
basin_met_fires['month'] = basin_met_fires['date'].apply(lambda x: x.month)
basin_met_fires.to_csv("../processed_data/sac_alloc_fires.csv")

pm_points = pm[['longitude','latitude','datum']].drop_duplicates()
pm_wgs84 = pm_points.loc[pm_points['datum']=='WGS84']
pm_wgs84['point'] = pm_wgs84.apply(lambda x: shg.Point(x['longitude'],x['latitude']),axis=1)
pm_wgs84 = gpd.GeoDataFrame(pm_wgs84,geometry="point").set_crs("EPSG:4326")
pm_nad83 = pm_points.loc[pm_points['datum']=='NAD83']
pm_nad83['point'] = pm_nad83.apply(lambda x: shg.Point(x['longitude'],x['latitude']),axis=1)
pm_nad83 = gpd.GeoDataFrame(pm_nad83,geometry="point").set_crs("EPSG:4269")
pm_nad83 = pm_nad83.to_crs("EPSG:4326")
pm_points = pm_wgs84.append(pm_nad83)
pm_points = pm_points.to_crs("EPSG:3310")
pm_points['buff'] = pm_points['point'].apply(lambda x: x.buffer(50*1000))
pm_points = pm_points.set_geometry('buff')

sac_cropland_fires['point'] = sac_cropland_fires.apply(lambda x: shg.Point(x['longitude'],x['latitude']),axis=1)
sac_cropland_fires = gpd.GeoDataFrame(sac_cropland_fires,geometry='point').set_crs("EPSG:4326").to_crs("EPSG:3310")

pm_fires = gpd.sjoin(pm_points,sac_cropland_fires[['acq_date','fires','point']],
                    how="inner",op="contains")
pm_fires = pm_fires.groupby(['longitude','latitude','datum','acq_date'])['fires'].sum().reset_index()
pm_fires['acq_date'] = pm_fires['acq_date'].apply(str)
pm['date_local'] = pm['date_local'].apply(str)
pm_fires = pd.merge(pm,pm_fires,
                   left_on = ['longitude','latitude','datum','date_local'],
                   right_on = ['longitude','latitude','datum','acq_date'],
                   how='left')

pm_fires = pm_fires.groupby(['longitude','latitude','datum','date_local']).agg({'fires':'first','sample_measurement':'max'})
pm_fires['fires'] = pm_fires['fires'].fillna(0)
basin_met['date'] = basin_met['date'].apply(str)
pm_fires = pd.merge(pm_fires,basin_met,
                   left_on = "date_local",
                   right_on = "date")
pm_fires.to_csv("../processed_data/pm_station_fires.csv")
