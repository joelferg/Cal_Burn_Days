import re
import ast
import time
import os
import datetime as dt
import requests

import pandas as pd
import geopandas as gpd
from dotenv import load_dotenv

load_dotenv()
email = os.getenv("aqi_email")
key = os.getenv("aqi_key")

def processAQI(url):
    req = requests.get(url)
    text = req.text
    text = re.sub("/s","",text)
    text = re.sub("null","None",text)
    text = ast.literal_eval(text)
    if len(text['Data'])>0:
        df = pd.DataFrame(text['Data'])
        return(df)
    else:
        print(f"No data: {url}")
        pass

def addZeros(x,n):
    x = str(x)
    while len(x)<n:
        x = "0"+x
    return(x)

counties = gpd.read_file("../raw_data/maps/CA_Counties/CA_Counties_TIGER2016.shp")
counties = counties.to_crs("EPSG:4326")

basins = gpd.read_file("../raw_data/maps/california-air-resources-board-air-basin-boundaries/CaAirBasin.shp")
basins = basins.to_crs("EPSG:4326")
sac_valley = basins.loc[basins['NAME']=="Sacramento Valley"]

sac_counties = gpd.sjoin(counties,sac_valley,
                        how="inner",predicate="intersects")
sac_counties = sac_counties['COUNTYFP'].to_list()


already_pulled = os.listdir("../raw_data/pm25/")
for year in range(2005,2023):
    #end_date = datetime.date(year+(month//12),(month%12)+1,1)-datetime.timedelta(days=1)
    for county in sac_counties:
        if f"pm25_06{county}_{year}.pkl" not in already_pulled:
            url = f"https://aqs.epa.gov/data/api/sampleData/byCounty?email={email}&key={key}&param=88101&bdate={year}0101&edate={year}{12}{31}&state=06&county={county}"
            df = processAQI(url)
            if type(df)!=type(None):
                df.to_pickle(f"../raw_data/pm25/pm25_06{county}_{year}.pkl")
            time.sleep(6)
