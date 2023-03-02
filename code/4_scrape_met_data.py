import requests
from bs4 import BeautifulSoup
import psycopg2
import datetime as dt
import time
import re

headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
    }

conn=psycopg2.connect(database="sac_met")

def scrapePage(date):
    year = date.year
    month = date.month
    day = date.day
    url = f"https://www.arb.ca.gov/aqmis2/met/see_burn_info.php?date={year}-{month}-{day}"
    req = requests.get(url, headers)

    soup = BeautifulSoup(req.content, 'html.parser')

    normbs = soup.find_all(class_="normb")
    norms = {}
    for i in normbs[:15]:
        norms[i.get_text()] = ';'.join([x.get_text() for x in i.find_next_siblings(class_="norm")])



    if 'ARB REVISED Basinwide Allocation' in norms.keys():

        sql = ''' INSERT INTO basin_met (date,form_date,time,meteorologist,burn_dec_3000,am_stab,wind_spd,millibar500_ht,rain,met_fact,aq_fact,alloc_eq,arb_rev_basin_alloc,rev_basin_alloc)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'''

        cur.execute(sql,(f"{year}-{month}-{day}",norms['Date:'],norms['Local Time:'],norms['Meteorologist:'],norms['Ag Burn Decision Above 3000 ft:'][0:40],norms['A.M. Stability (°F)'],norms['Wind Speed (mph)\xa0'],norms['500 millibar height (decameters)'],norms['Average Rainfall (in)'],norms['Meteorological (MET) Factor'],norms['Air Quality (AQ) Factor (Basinwide 00-06 PST Average PM2.5)'], norms['Allocation Equation:'],norms['ARB REVISED Basinwide Allocation'],norms['Revised Allocation']))
    else:

        sql = ''' INSERT INTO basin_met (date,form_date,time,meteorologist,burn_dec_3000,am_stab,wind_spd,millibar500_ht,rain,met_fact,aq_fact,alloc_eq,arb_rev_basin_alloc,rev_basin_alloc)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'''

        cur.execute(sql,(f"{year}-{month}-{day}",norms['Date:'],norms['Local Time:'],norms['Meteorologist:'],norms['Ag Burn Decision Above 3000 ft:'],norms['A.M. Stability (°F)'],norms['Wind Speed (mph)\xa0'],norms['500 millibar height (decameters)'],norms['Average Rainfall (in)'],norms['Meteorological (MET) Factor'],norms['Air Quality (AQ) Factor (Basinwide 00-06 PST Average PM2.5)'], norms['Allocation Equation:'],norms['ARB/SMPC REVISED Basinwide Allocation'],norms['ARB/SMPC REVISED Basinwide Allocation']))

    conn.commit()


start_date = dt.date(2005,9,7) # First day of recorded data as far as I can tell
end_date = dt.date(2022,12,31)
days_tot = (end_date-start_date).days

last_yr = 0

for day in range(0,days_tot):
    date = start_date+dt.timedelta(days=day)
    yr = date.year
    if yr!=last_yr:
        print(yr)
    last_yr = yr
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM basin_met WHERE date = '{yr}-{date.month}-{date.day}';")
    res = cur.fetchone()[0]
    cur.close()
    if res == 0:
        try:
            cur = conn.cursor()
            scrapePage(date)
            time.sleep(1)
        except:
            print(f"Broke on day {day}")
            cur.close()
            time.sleep(1)

conn.close()
