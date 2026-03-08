#After doing some investigation, I found that the url provided in the task is not longer vald.
#I have found another url that provides the same data and I have used that url in the code below.
#Data source needed: Firearm Mortality rates (from the CDC) and Firearm Law Strictness 
#Firearm mortality data was obtained from the CDC Open Data API using the “Mapping Injury, Overdose, and Violence – State” dataset. 
#The dataset was filtered to include only deaths where the injury mechanism was classified as firearm.
#Column	Meaning
#FA_Deaths	Total firearm deaths
#FA_Homicide	Firearm homicides
#FA_Suicide	Firearm suicides

import pandas as pd

csv_url = "https://data.cdc.gov/api/views/fpsi-y8tj/rows.csv?accessType=DOWNLOAD"
df = pd.read_csv(csv_url)

print(df.head())
print(df.columns.tolist())

df.to_csv("data/cdc_firearm_state_data_raw.csv", index=False)
print("Saved to data/cdc_firearm_state_data_raw.csv")

print(df.columns)
print(df['Intent'].unique())

df_filtered = df[(df['Intent'] == 'FA_Deaths') | (df['Intent'] == 'FA_Homicide') | (df['Intent'] == 'FA_Suicide')]

df_filtered.rename(columns={"FA_Deaths": "firearm_deaths"}, inplace=True)
df_filtered.rename(columns={"FA_Homicide": "firearm_homicides"}, inplace=True)
df_filtered.rename(columns={"FA_Suicide": "firearm_suicides"}, inplace=True)

print(df_filtered.head())
print(df_filtered.columns.tolist())


df_filtered.to_csv("data/cdc_firearm_state_data_filtered.csv", index=False)
print("Saved to data/cdc_firearm_state_data_filtered.csv")