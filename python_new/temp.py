import csv
import pandas as pd
import numpy as np

file1 = '../results/TradeMatrixFeed_import_dry_matter_2013_Area.csv'
file2 = '../results/TradeMatrixFeed_import_dry_matter_2013R_Area.csv'

def read_csv(filepath):
    with open(filepath, newline='', encoding='utf-8') as f:
        return list(csv.reader(f))

df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)
df1 = df1.drop(columns=['Year'])
df2 = df2.drop(columns=['Year'])

df1.dropna(subset=['Area'], inplace=True)
df2.dropna(subset=['Area'], inplace=True)

df1_sorted = df1.sort_values(by=[df1.columns[0], df1.columns[1], 'Item_Code'])
df2_sorted = df2.sort_values(by=[df2.columns[0], df2.columns[1], 'Item_Code'])

# df1_sorted = df1_sorted[[df1.columns[0], df1.columns[1], 'Item_Code']]
# df2_sorted = df2_sorted[[df1.columns[0], df1.columns[1], 'Item_Code']]
merged_df = pd.merge(df1_sorted, df2_sorted, how='outer', on=['Consumer_Country_Code', 'Producer_Country_Code', 'Item_Code'], indicator=True)
final_df = merged_df[merged_df['_merge'] != 'both']
print(final_df)


