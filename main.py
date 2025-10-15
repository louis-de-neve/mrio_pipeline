#!/usr/bin/env python3
"""
This code is a translation/re-written python script of the original R code of the following publication:
Schwarzmueller, F. & Kastner, T (2022), Agricultural trade and its impact on cropland use
and the global loss of species' habitats. Sustainability Science, doi: 10.1007/s11625-022-01138-7

Please cite ;-)
(c) Florian Schwarzmueller, December 2021
Re-written in Python, October 2025 by Louis De Neve
"""

from pathlib import Path

from processing.unzip_data import unzip_data
from processing.calculate_trade_matrix import calculate_trade_matrix
from processing.animal_products_to_feed import animal_products_to_feed
from processing.calculate_area import calculate_area

import os



# CONFIG
# Select years for which to calculate the results 
YEARS = [2023, 2024] #list(range(2014, 2024))

# Select a conversion method
# inputs: ("dry_matter", "Energy", "Protein", "Fiber_TD", "Zinc", "Iron", "Calcium",
#          "Folate_Tot", "Riboflavin", "Choline_Tot", "Potassium", "Vit_E", "Vit_B12",
#          "Vit_K", "Vit_A")
CONVERSION_OPTION = "dry_matter"

# elect whether to prefer reported import or export data
# inputs: ("import", "export")
PREFER_IMPORT = "import"

# select working directory
WORKING_DIR = '/home/louis/Documents/zoology/pipeline/mrio'

# 0 = all, 1 = unzip, 2 = trade matrix, 3 = animal products to feed, 4 = area calculation
PIPELINE_COMPONENTS:list = [0]

SAVE_INTERMEDIATES = True  # Whether to save intermediate results or not



def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    os.chdir(WORKING_DIR)

    component_dict = {
        0: "Full pipeline",
        1: "Unzipping data",
        2: "Trade matrix calculation",
        3: "Animal products to feed calculation",
        4: "Area calculation"}

    print(f"""\nStarting MRIO calculations with options:
    Working directory: {WORKING_DIR}
    Using {CONVERSION_OPTION} as the conversion option
    Preferring {PREFER_IMPORT} data
    Running pipeline component {[p for p in PIPELINE_COMPONENTS]}: {[component_dict[p] for p in PIPELINE_COMPONENTS]} 
    Saving intermediate results: {SAVE_INTERMEDIATES}

    Years to process: {YEARS}
    """)

    # Create directories
    results_dir = Path("./results")
    intermediate_results_dir = Path("./results/intermediate")
    final_results_dir = Path("./results/final")

    results_dir.mkdir(exist_ok=True)
    intermediate_results_dir.mkdir(exist_ok=True)
    final_results_dir.mkdir(exist_ok=True)


    if (0 in PIPELINE_COMPONENTS) or (1 in PIPELINE_COMPONENTS):
        print("Unzipping data...")
        try:
            unzip_data("./input_data") # Uncomment this line to enable unzipping
            print("Data already unzipped or unzipping completed successfully.")
        except Exception as e:
            print(f"Error during data unzipping: {e}")
            # Continue anyway as data might already be unzipped

    if PIPELINE_COMPONENTS == [1]:
        return
    
    for year in YEARS:
        print(f"\nProcessing year: {year}")
        
        hist = "Historic" if year < 2014 else ""

        if (0 in PIPELINE_COMPONENTS) or (2 in PIPELINE_COMPONENTS):
            calculate_trade_matrix(
                conversion_opt=CONVERSION_OPTION,
                prefer_import=PREFER_IMPORT,
                year=year,
                historic=hist)
            
        if (0 in PIPELINE_COMPONENTS) or (3 in PIPELINE_COMPONENTS):
            animal_products_to_feed(
                prefer_import=PREFER_IMPORT,
                conversion_opt=CONVERSION_OPTION,
                year=year,
                historic=hist)
            
        if (0 in PIPELINE_COMPONENTS) or (4 in PIPELINE_COMPONENTS):
            calculate_area(
                prefer_import=PREFER_IMPORT,
                conversion_opt=CONVERSION_OPTION,
                year=year)

        print(f"Year {year} processing completed successfully\n")


    if (not SAVE_INTERMEDIATES) and (PIPELINE_COMPONENTS in [0, 4]):
        print("\nRemoving intermediate files...")
        for year in YEARS:
            intermediate_file = f"./results/intermediate/{year}_TradeMatrix_{PREFER_IMPORT}_{CONVERSION_OPTION}.csv"
            if Path(intermediate_file).exists():
                os.remove(intermediate_file)
            intermediate_file = f"./results/intermediate/{year}_TradeMatrixFeed_{PREFER_IMPORT}_{CONVERSION_OPTION}.csv"
            if Path(intermediate_file).exists():
                os.remove(intermediate_file)



if __name__ == "__main__":
    main()