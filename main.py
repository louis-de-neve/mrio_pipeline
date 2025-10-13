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
YEARS = [2013]  # 1986 to 2013 inclusive # TODO: change back to list(range(1986, 2014))

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

# 0 = all, 1 = unzip only, 2 = trade matrix only, 3 = animal products to feed only, 4 = area calculation only
PIPELINE_COMPONENTS = 0


def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    os.chdir(WORKING_DIR)
    print(f"\nStarting MRIO calculations for years {YEARS[0]}-{YEARS[-1]}, using {CONVERSION_OPTION} as the conversion option and preferring {PREFER_IMPORT} data.\n")

    # Create directories
    results_dir = Path("./results")
    intermediate_results_dir = Path("./results/intermediate")
    final_results_dir = Path("./results/final")

    results_dir.mkdir(exist_ok=True)
    intermediate_results_dir.mkdir(exist_ok=True)
    final_results_dir.mkdir(exist_ok=True)

    if PIPELINE_COMPONENTS in [0, 1]:
        print("Unzipping data...")
        try:
            unzip_data("./input_data") # Uncomment this line to enable unzipping
            print("Data already unzipped or unzipping completed successfully.")
        except Exception as e:
            print(f"Error during data unzipping: {e}")
            # Continue anyway as data might already be unzipped

    if PIPELINE_COMPONENTS == 1:
        return
    
    for year in YEARS:
        print(f"\nProcessing year: {year}")
        
        if PIPELINE_COMPONENTS in [0, 2]:
            calculate_trade_matrix(
                conversion_opt=CONVERSION_OPTION,
                prefer_import=PREFER_IMPORT,
                year=year)
            
        if PIPELINE_COMPONENTS in [0, 3]:
            animal_products_to_feed(
                prefer_import=PREFER_IMPORT,
                conversion_opt=CONVERSION_OPTION,
                year=year)
            
        if PIPELINE_COMPONENTS in [0, 4]:
            calculate_area(
                prefer_import=PREFER_IMPORT,
                conversion_opt=CONVERSION_OPTION,
                year=year)

        print(f"Year {year} processing completed successfully\n")



if __name__ == "__main__":
    main()