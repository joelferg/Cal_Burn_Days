import pandas as pd

dfs = pd.read_excel("/Users/joelferguson/Documents/Cal_Burn_Days/raw_data/burn_decisions/md2020.xlsx",
                    sheet_name=None,
                    skiprows=4,
                    nrows=30)


for m in dfs.keys():
    df = dfs[m]
    df = df.dropna(1,"all").drop("Burn %",axis=1)
    df = df.melt(id_vars=["AIR BASIN"],
                 var_name="day",
                 value_name="burn_dec")
    df['month'] = m
    dfs[m] = df

dfs = pd.concat(dfs)

dfs['burn_day'] = (dfs['burn_dec']!="NB")&(dfs['burn_dec']!=0)

dfs.to_csv("/Users/joelferguson/Documents/Cal_Burn_Days/processed_data/burn_decisions.csv")
