import pandas as pd
import numpy as np
from pathlib import Path
conversion_opt="dry_matter"
year=2013
prefer_import="import"


print("Loading files for animal products to feed conversion...")

cb_map_filename = "../CB_to_primary_items_map.csv"
cb_split_filename = "../CB_items_split.csv" 
content_factors_filename = "../content_factors_per_100g.xlsx"
cb_conversion_filename = "../CB_code_FAO_code_for_conversion_factors.csv"
cb_crops_filename = "../CommodityBalances_Crops_E_All_Data_(Normalized).csv"
animals_filename = "../Production_LivestockPrimary_E_All_Data_(Normalized).csv"
trade_matrix_filename = f"../results/TradeMatrix_{prefer_import}_{conversion_opt}_{year}.csv"
weighing_filename = "../weighing_factors.csv"


if not Path(trade_matrix_filename).exists():
    raise FileNotFoundError(f"Trade matrix file not found: {trade_matrix_filename}")
transformed_data = pd.read_csv(trade_matrix_filename, encoding='Latin-1')
cb_map = pd.read_csv(cb_map_filename, encoding='Latin-1')
cb_split = pd.read_csv(cb_split_filename, encoding='Latin-1')
content_factors = pd.read_excel(content_factors_filename, skiprows=1)
cb_conversion_map = pd.read_csv(cb_conversion_filename, encoding='Latin-1')
cb_crops_data = pd.read_csv(cb_crops_filename, encoding='Latin-1')
production_animals = pd.read_csv(animals_filename, encoding='Latin-1')
weighing_factors = pd.read_csv(weighing_filename, encoding='Latin-1')
units = pd.read_excel(content_factors_filename, header=None, nrows=1)
units.columns = content_factors.columns


content_factors.rename(columns=lambda x: x.replace(' ', '_'), inplace=True)
cb_crops_data.rename(columns=lambda x: x.replace(' ', '_'), inplace=True)
production_animals.rename(columns=lambda x: x.replace(' ', '_'), inplace=True)


cb_crops_data = cb_crops_data[(cb_crops_data["Year"] == year) &
    (cb_crops_data["Element_Code"] == 5520)]    
production_animals = production_animals[(production_animals["Year"] == year) &
    (production_animals["Element_Code"] == 5510)]

print("Calculating conversion factors...")

content_factors_cb = cb_conversion_map.merge(content_factors, 
    left_on='FAO_code',
    right_on='Item_Code',
    how='left'
    ).drop(columns=['Item', 'FAO_code', 'FAO_name', 'Item_Code']
    ).rename(columns={'CB_code': 'Item_Code', 'CB_name': 'Item'})
content_factors_cb = content_factors_cb[["Item_Code", conversion_opt]]

joined = cb_map.merge(
    content_factors_cb,
    on="Item_Code",
    how="left")
joined = joined.merge(
    content_factors_cb,
    left_on="Primary_Item_Code",
    right_on="Item_Code",
    how="left",
    suffixes=("_x", "_y")).drop(columns=["Item_Code_y"]).rename(columns={"Item_Code_x": "Item_Code"})

joined["Conversion_factor"] = joined[f"{conversion_opt}_x"] / joined[f"{conversion_opt}_y"]
joined = joined.sort_values(by="Primary_Item_Code")

conversion_factors = joined[joined["Conversion_factor"].notna()][["Item_Code", "Primary_Item_Code", "Conversion_factor"]]

print("Preparing data...")
cb_data = cb_crops_data.merge(
    conversion_factors,
    on="Item_Code",
    how="left")

cb_data["Value_new"] = cb_data["Value"] * cb_data["Conversion_factor"]

feed_data = cb_data[(cb_data["Area_Code"]<300) & (cb_data["Primary_Item_Code"].notna())]
feed_data = (feed_data
    .groupby(["Area_Code", "Year", "Primary_Item_Code"])
    .agg({'Value_new': 'sum'})
    .reset_index())