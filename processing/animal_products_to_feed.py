"""
This code is a translation/re-written python script of the original R code of the following publication:
Schwarzmueller, F. & Kastner, T (2022), Agricultural trade and its impact on cropland use
and the global loss of species' habitats. Sustainability Science, doi: 10.1007/s11625-022-01138-7

Please cite ;-)
(c) Florian Schwarzmueller, December 2021
Re-written in Python, October 2025 by Louis De Neve
"""

import pandas as pd
import numpy as np
from pathlib import Path

def ml_animal_prod(year, country, production_animals,feed_data, weighing_factors,):
    production_animal_data_1 = production_animals[
        (production_animals["Area_Code"] == country) &
        (production_animals["Year"] == year) &
        (production_animals["Value"] > 0)]
    data_feed = feed_data[
        (feed_data["Area_Code"] == country) &
        (feed_data["Year"] == year) &
        (feed_data["Value"] > 0)]
    # if len(production_animal_data_1) == 0 or len(data_feed) == 0:
    #     return None
    data_2 = weighing_factors.merge(production_animal_data_1, on="Item_Code", how="inner")
    data_2 = data_2[data_2["Weighing_factors"] > 0]
    data_2["relative_weighing"] = data_2["Weighing_factors"] / data_2["Weighing_factors"].mean()
    data_2["weighted_production"] = data_2["relative_weighing"] * data_2["Value"]
    data_2["relative_production"] = data_2["weighted_production"] / data_2["weighted_production"].sum()
    data_2["rel_prod_weighted"] = data_2["relative_production"] / data_2["Value"]
    
    mpt = np.outer(data_2["rel_prod_weighted"], data_feed["Value"])

    row_indices = data_2["Item_Code"].tolist()
    col_indices = data_feed["Primary_Item_Code"].tolist()
    
    results = []
    for j in range(mpt.shape[0]):
        for k in range(mpt.shape[1]):
            if (mpt[j, k] > 0) & (not np.isnan(row_indices[j])):
                results.append({
                    "Producer_Country_Code": country,
                    "Year": year,
                    "Animal_Product_Code": row_indices[j],
                    "Item_Code": col_indices[k],
                    "Value": mpt[j, k]
                })
    return results

def animal_products_to_feed(prefer_import="import", conversion_opt="dry_matter", year=2013):
    print("    Loading files for animal products to feed conversion...")

    cb_map_filename = "./input_data/CB_to_primary_items_map.csv"
    cb_split_filename = "./input_data/CB_items_split.csv" 
    content_factors_filename = "./input_data/content_factors_per_100g.xlsx"
    cb_conversion_filename = "./input_data/CB_code_FAO_code_for_conversion_factors.csv"
    cb_crops_filename = "./input_data/CommodityBalances_Crops_E_All_Data_(Normalized).csv"
    animals_filename = "./input_data/Production_LivestockPrimary_E_All_Data_(Normalized).csv"
    weighing_filename = "./input_data/weighing_factors.csv"


    trade_matrix_filename = f"./results/intermediate/{year}_TradeMatrix_{prefer_import}_{conversion_opt}.csv"
    output_filename = f"./results/intermediate/{year}_TradeMatrixFeed_{prefer_import}_{conversion_opt}.csv"


    if not Path(trade_matrix_filename).exists():
        raise FileNotFoundError(f"Trade matrix file not found: {trade_matrix_filename}")
    transformed_data = pd.read_csv(trade_matrix_filename, encoding="Latin-1")
    cb_map = pd.read_csv(cb_map_filename, encoding="Latin-1")
    cb_split = pd.read_csv(cb_split_filename, encoding="Latin-1")
    content_factors = pd.read_excel(content_factors_filename, skiprows=1)
    cb_conversion_map = pd.read_csv(cb_conversion_filename, encoding="Latin-1")
    cb_crops_data = pd.read_csv(cb_crops_filename, encoding="Latin-1")
    production_animals = pd.read_csv(animals_filename, encoding="Latin-1")
    weighing_factors = pd.read_csv(weighing_filename, encoding="Latin-1")
    units = pd.read_excel(content_factors_filename, header=None, nrows=1)
    units.columns = content_factors.columns


    content_factors.rename(columns=lambda x: x.replace(" ", "_"), inplace=True)
    cb_crops_data.rename(columns=lambda x: x.replace(" ", "_"), inplace=True)
    production_animals.rename(columns=lambda x: x.replace(" ", "_"), inplace=True)
    weighing_factors.rename(columns=lambda x: x.replace(" ", "_"), inplace=True)


    cb_crops_data = cb_crops_data[(cb_crops_data["Year"] == year) &
        (cb_crops_data["Element_Code"] == 5520)]    
    production_animals = production_animals[(production_animals["Year"] == year) &
        (production_animals["Element_Code"] == 5510)]


    content_factors_cb = cb_conversion_map.merge(content_factors, 
        left_on="FAO_code",
        right_on="Item_Code",
        how="left"
        ).drop(columns=["Item", "FAO_code", "FAO_name", "Item_Code"]
        ).rename(columns={"CB_code": "Item_Code", "CB_name": "Item"})
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

    cb_data = cb_crops_data.merge(
        conversion_factors,
        on="Item_Code",
        how="left")

    cb_data["Value_new"] = cb_data["Value"] * cb_data["Conversion_factor"]

    feed_data = cb_data[(cb_data["Area_Code"]<300) & (cb_data["Primary_Item_Code"].notna())]
    feed_data = (feed_data
        .groupby(["Area_Code", "Year", "Primary_Item_Code"])
        .agg({"Value_new": "sum"})
        .reset_index()
        .rename(columns={"Value_new": "Value"})
        )

    unique_combinations = transformed_data[["Producer_Country_Code", "Year"]].drop_duplicates()
    unique_combinations = unique_combinations.sort_values(by=["Year", "Producer_Country_Code"])

    feed_eq_data = []
    for country, yr in unique_combinations.itertuples(index=False):
        feed_eq_data += ml_animal_prod(yr, country, production_animals, feed_data, weighing_factors)

    feed_eq_data = pd.DataFrame(feed_eq_data, columns=["Producer_Country_Code", "Year", "Animal_Product_Code", "Item_Code", "Value"])
    feed_eq_data.rename(columns={"Producer_Country_Code": "AP_Producer_Country_Code", "Value": "Feed_per_AP"}, inplace=True)


    crop_shares = (transformed_data
        .merge(cb_split, left_on="Item_Code", right_on="Primary_Item_Code", how="left"))
    crop_shares = crop_shares[crop_shares["Item_Code"] < 867]
    crop_shares["vsum"] = crop_shares.groupby(["Consumer_Country_Code", "CB_Item_Code", "Year"])["Value"].transform("sum")
    crop_shares["share"] = crop_shares["Value"]/crop_shares["vsum"]
    crop_shares = (crop_shares
        .rename(columns={
            "Producer_Country_Code": "Feed_Producer_Country_Code",
            "Item_Code": "Feed_Item_Code"})
        .drop(columns=["Primary_Item_Code", "vsum"]))    

    crop_shares.loc[crop_shares["Value"]==0, "share"]=0

    share_per_country = feed_eq_data.merge(crop_shares, left_on=["AP_Producer_Country_Code", "Year", "Item_Code"], right_on=["Consumer_Country_Code", "Year", "CB_Item_Code"], how="left")
    share_per_country["feed_share"] = share_per_country["Feed_per_AP"] * share_per_country["share"]

    share_per_country = share_per_country[["AP_Producer_Country_Code", "Year", "Animal_Product_Code", "Feed_Producer_Country_Code", "Feed_Item_Code", "feed_share"]]

    animal_trade_data = transformed_data[transformed_data["Item_Code"] > 850]


    print("    Computing animal feed...")

    # Process merge in chunks by item
    results = []    
    for prod in animal_trade_data['Item_Code'].unique():
        animal_chunk = animal_trade_data[animal_trade_data['Item_Code'] == prod]
        share_chunk = share_per_country[share_per_country['Animal_Product_Code'] == prod]
        
        merged_chunk = animal_chunk.merge(
            share_chunk,
            left_on=["Year", "Item_Code", "Producer_Country_Code"],
            right_on=["Year", "Animal_Product_Code", "AP_Producer_Country_Code"],
            how="inner"
        ).drop(columns=["AP_Producer_Country_Code", "Animal_Product_Code"])
        
        results.append(merged_chunk)
    
    animal_product_data_full = pd.concat(results, ignore_index=True)
    animal_product_data_full["tons_feed_use"] = animal_product_data_full["feed_share"] * animal_product_data_full["Value"]
    
    feed_in_animal_products = (animal_product_data_full
        .groupby(["Year", "Feed_Producer_Country_Code", "Consumer_Country_Code", "Feed_Item_Code", "Item_Code"])
        .agg({"tons_feed_use": "sum"})
        .reset_index()
        .rename(columns={
            "Feed_Producer_Country_Code": "Producer_Country_Code",
            "tons_feed_use": "Value",
            "Feed_Item_Code": "Item_Code",
            "Item_Code": "Animal_Product_Code"
        })
        .reindex(columns=["Year", "Producer_Country_Code", "Consumer_Country_Code", "Item_Code", "Value", "Animal_Product_Code"])
    )

    feed_use_origin_per_country = (animal_product_data_full
        .groupby(["Year", "Feed_Producer_Country_Code", "Producer_Country_Code", "Feed_Item_Code", "Item_Code"])
        .agg({"tons_feed_use": "sum"})
        .reset_index()
    )
    feed_use_origin_per_country.drop(columns=["Item_Code"], inplace=True)
    feed_use_origin_per_country["tons_feed_use"] = feed_use_origin_per_country["tons_feed_use"] * -1

    feed_use_origin_per_country.rename(columns={
        "tons_feed_use": "Value",
        "Feed_Item_Code": "Item_Code",
        "Producer_Country_Code": "Consumer_Country_Code",
        "Feed_Producer_Country_Code": "Producer_Country_Code"}, inplace=True)

    crop_trade_data = transformed_data[transformed_data["Item_Code"] < 850]
    crop_trade_data = pd.concat([crop_trade_data, feed_use_origin_per_country], ignore_index=True, sort=False)

    crop_trade_data = crop_trade_data.groupby(["Year", "Producer_Country_Code", "Consumer_Country_Code", "Item_Code"], as_index=False)["Value"].sum()
    crop_trade_data["Animal_Product_Code"] = np.nan

    output_data = pd.concat([crop_trade_data, feed_in_animal_products])
    print("    Saving feed results...")
    output_data.to_csv(output_filename, index=False)


if __name__ == "__main__":
    import os
    os.chdir('/home/louis/Documents/zoology/pipeline/mrio')
    animal_products_to_feed(prefer_import="import", conversion_opt="dry_matter", year=2013)