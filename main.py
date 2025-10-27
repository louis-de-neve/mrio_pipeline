#!/usr/bin/env python3
"""
This code is a translation/re-written python script of the original R code of the following publication:
Schwarzmueller, F. & Kastner, T (2022), Agricultural trade and its impact on cropland use
and the global loss of species' habitats. Sustainability Science, doi: 10.1007/s11625-022-01138-7

Please cite ;-)
(c) Florian Schwarzmueller, December 2021
Re-written in Python, October 2025 by Louis De Neve
"""

import os
from pathlib import Path

from processing.unzip_data import unzip_data
from processing.calculate_trade_matrix import calculate_trade_matrix
from processing.animal_products_to_feed import animal_products_to_feed
from processing.calculate_area import calculate_area

from provenance._consumption_provenance import main as consumption_provenance_main
from provenance._get_impacts import get_impacts as get_impacts_main
from provenance._process_dat import main as process_dat_main
# from provenance.global_commodity_impacts import main as global_commodity_impacts_main



# CONFIG
# Select years for which to calculate the results 
YEARS = list(range(2009, 2015))
YEARS = [2013]

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

# 0 = all, 1 = unzip, 2 = trade matrix, 3 = animal products to feed, 4 = area calculation, 5 = country impacts
PIPELINE_COMPONENTS:list = [0]



from pandas import read_excel
cdat = read_excel("input_data/nocsDataExport_20251021-164754.xlsx")
COUNTRIES = [_.upper() for _ in cdat["ISO3"].unique().tolist() if isinstance(_, str)]
# COUNTRIES = ["GBR"]

##########################################################


def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    os.chdir(WORKING_DIR)

    component_dict = {
        0: "Full pipeline",
        1: "Unzipping data",
        2: "Trade matrix calculation",
        3: "Animal products to feed calculation",
        4: "Area calculation",
        5: "Country-level impact calculation"}

    print(f"""\nStarting MRIO calculations with options:
    Working directory: {WORKING_DIR}
    Using {CONVERSION_OPTION} as the conversion option
    Preferring {PREFER_IMPORT} data
    Running pipeline component {[p for p in PIPELINE_COMPONENTS]}: {[component_dict[p] for p in PIPELINE_COMPONENTS]} 

    Years to process: {YEARS}
    """)

    # Create directories
    results_dir = Path("./results")
    results_dir.mkdir(exist_ok=True)


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

        year_dir = Path(f"./results/{year}")
        year_dir.mkdir(exist_ok=True)
        mrio_dir = Path(f"./results/{year}/.mrio")
        mrio_dir.mkdir(exist_ok=True)

        print(f"\nProcessing year: {year}")
        
        hist = "Historic" if year < 2012 else ""

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
            if 4 in PIPELINE_COMPONENTS:
                print("    MRIO area calculation is deprecated")
            else:
                print("   MRIO complete") 
            
            # calculate_area(
            #     prefer_import=PREFER_IMPORT,
            #     conversion_opt=CONVERSION_OPTION,
            #     year=year)
            

        if (0 in PIPELINE_COMPONENTS) or (5 in PIPELINE_COMPONENTS):
            print("    Processing country-level impacts...")
            for country in COUNTRIES:
                print(f"    Processing country: {country}")
                
                cons, feed = consumption_provenance_main(year, country)

                print("         Calculating impacts")
                get_impacts_main(feed, year, country, "feed_impacts_wErr.csv")  
                get_impacts_main(cons, year, country, "human_consumed_impacts_wErr.csv")  
                print("         Organising data")   
                process_dat_main(year, country)

        print(f"Year {year} processing completed successfully\n")




if __name__ == "__main__":
    main()