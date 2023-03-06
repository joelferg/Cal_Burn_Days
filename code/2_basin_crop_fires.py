import os
import datetime as dt

import pandas as pd



months = {"Jan":1,"Feb":2,"March":3,"April":4,"May":5,"Jun":6,
          "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

cropfire_files = os.listdir("../processed_data/cropland_fires/")

cropfires = [pd.read_csv("../processed_data/cropland_fires/"+f) for f in cropfire_files]
cropfires = pd.concat(cropfires)
cropfires['cropland'] = cropfires['max']==2
cropfires = cropfires[['index','cropland']]

basin_fires = pd.read_pickle("../processed_data/basin_fires_2012-2020.pkl")
burn_decisions = pd.read_csv("../processed_data/burn_decisions.csv")
#basin_name_xwalk = pd.read_csv("../raw_data/burn_decisions/basin_name_xwalk.csv")

basin_fires_wcrop = pd.merge(basin_fires,cropfires,
                             on='index')

basin_counts = basin_fires_wcrop.groupby(['NAME','acq_date'])[['fires','cropland']].sum().reset_index()
basin_counts['year'] = basin_counts['acq_date'].apply(lambda x: x.year)
basin_counts['month'] = basin_counts['acq_date'].apply(lambda x: x.month)
basin_counts.to_csv("../processed_data/daily_fires_basin.csv")

'''
burn_decisions = pd.merge(burn_decisions,basin_name_xwalk,
                          on="AIR BASIN")

decisions_w_fires = burn_decisions.groupby(['NAME','month','day'])['burn_day'].min().reset_index()
decisions_w_fires['month'] = decisions_w_fires['month'].apply(lambda x: months[x])
decisions_w_fires['acq_date'] = decisions_w_fires.apply(lambda x:datetime.date(2020,x['month'],x['day']),axis=1)
decisions_w_fires = pd.merge(decisions_w_fires,basin_counts,
                             on=["NAME","acq_date"],how="left")
decisions_w_fires[['fires','cropland']] = decisions_w_fires[['fires','cropland']].fillna(0)
decisions_w_fires.to_csv("../processed_data/burn_decisions_w_fires.csv")
'''
