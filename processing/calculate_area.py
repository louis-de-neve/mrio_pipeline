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

def calculate_area(prefer_import="import", conversion_opt="dry_matter", year=2013):
    
    print("    Loading area data...")
        # File paths
    yield_data_file = "input_data/Production_Crops_Livestock_E_All_Data_(Normalized).csv"
    trade_matrix_file = f"results/intermediate/{year}_TradeMatrixFeed_{prefer_import}_{conversion_opt}.csv"
    
    # Check if trade matrix file exists
    if not Path(trade_matrix_file).exists():
        raise FileNotFoundError(f"Trade matrix file not found: {trade_matrix_file}")
    
    # Load data
    trade_data = pd.read_csv(trade_matrix_file, encoding="Latin-1")
    yield_data = pd.read_csv(yield_data_file, encoding="Latin-1", low_memory=False)
    
    # Clean column names
    yield_data.rename(columns=lambda x: x.replace(" ", "_"), inplace=True)
    
    # Filter yield data
    yield_data = yield_data[(yield_data["Element"] == "Yield")&(yield_data["Unit"]=="kg/ha")]


    # Rename columns to match trade data
    yield_data = yield_data.rename(columns={
        "Area_Code": "Producer_Country_Code",
        "Value": "Yield"})
    
    print("    Calculating areas...")
    
    # Merge trade data with yield data
    area_data = trade_data.merge(
        yield_data[["Producer_Country_Code", "Year", "Item_Code", "Yield"]], 
        on=["Producer_Country_Code", "Year", "Item_Code"], 
        how="left")
    

    # Calculate area (Value * 10000 / Yield)
    # Value is in tonnes so Value *1,000 gives kg then dividing by Yield (kg/ha) gives area in ha
    area_data["Area"] = (area_data["Value"].astype(float) * 1000) / area_data["Yield"]
    
    # Select output columns
    output_data = area_data[[
        "Consumer_Country_Code", 
        "Producer_Country_Code", 
        "Item_Code", 
        "Animal_Product_Code", 
        "Year", 
        "Value", 
        "Area"]]
    
    
    print("    Saving final results...")
    output_filename = f"results/final/TradeMatrixFeed_{prefer_import}_{conversion_opt}_{year}_Area.csv"
    output_data.to_csv(output_filename, index=False)

