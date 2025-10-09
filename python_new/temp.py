import csv
import pandas as pd

file1 = '../results/TradeMatrix_import_dry_matter_2013.csv'
file2 = '../results/TradeMatrix_import_dry_matter_2013R.csv'

def read_csv(filepath):
    with open(filepath, newline='', encoding='utf-8') as f:
        return list(csv.reader(f))

df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

df1_sorted = df1.sort_values(by=[df1.columns[0], df1.columns[1], 'Item_Code'])
df2_sorted = df2.sort_values(by=[df2.columns[0], df2.columns[1], 'Item_Code'])

df1_sorted['Value'] = df1_sorted['Value'].round(5)
df2_sorted['Value'] = df2_sorted['Value'].round(5)

v1 = df1_sorted['Value'].values
v2 = df2_sorted['Value'].values

diff_indices = [i for i, (a, b) in enumerate(zip(v1, v2)) if a != b]
for i in diff_indices:
    print(f"Row {i}: Value1 = {v1[i]}, Value2 = {v2[i]}")

print(df1_sorted.iloc[diff_indices]['Value'])
print(df2_sorted.iloc[diff_indices]['Value'])