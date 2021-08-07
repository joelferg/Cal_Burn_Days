import pandas as pd
import psycopg2
import datetime
import re
import numpy as np

conn=psycopg2.connect(database="sac_met")

df = pd.read_sql_query("SELECT * FROM basin_met;",conn)
conn.close()

df['date'] = df['date'].apply(lambda x: datetime.date(int(re.split('-',x)[0]),
                                                     int(re.split('-',x)[1]),
                                                     int(re.split('-',x)[2])))
months = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
df['form_date'] = df['form_date'].apply(lambda x: datetime.date(int(f"20{re.split('-',x)[2]}"),
                                             months[re.split('-',x)[1]],
                                             int(re.split('-',x)[0])))

df=df.loc[df['date']==df['form_date'],]

for column in ['am_stab','wind_spd','millibar500_ht','rain','met_fact','aq_fact','alloc_eq','arb_rev_basin_alloc','rev_basin_alloc']:
    df[column]=df[column].apply(lambda x: re.sub("[=;]","",x))
    df.loc[df[column]=='',column]=np.nan
    df[column] = df[column].apply(float)

df.to_pickle("../processed_data/basin_met_clean.pkl")
