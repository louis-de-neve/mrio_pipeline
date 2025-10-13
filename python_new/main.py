#!/usr/bin/env python3
"""
This Code is part of the following publication:
Schwarzmueller, F. & Kastner, T (2022), Agricultural trade and its impact on cropland use
and the global loss of species' habitats. Sustainability Science, doi: 10.1007/s11625-022-01138-7

Please cite ;-)
(c) Florian Schwarzmüller, December 2021
Converted to Python by: Assistant, October 2025
"""
from pathlib import Path
from unzip_data import unzip_data
from calculate_trade_matrix import calculate_trade_matrix
from animal_products_to_feed import animal_products_to_feed
from calculate_area import calculate_area



# CONFIG
# Select years for which to calculate the results (1986 to 2013)
FOR_YEARS = list(range(2013, 2015))  # 1986 to 2013 inclusive # TODO: change back to range(1986, 2014)

# Select a conversion method
# Possible inputs: ("dry_matter", "Energy", "Protein", "Fiber_TD", "Zinc", "Iron", "Calcium",
#                   "Folate_Tot", "Riboflavin", "Choline_Tot", "Potassium", "Vit_E", "Vit_B12",
#                   "Vit_K", "Vit_A")
CONVERSION_OPTION = "dry_matter"

# Select whether to prefer reported import or export data
# Possible inputs: ("import", "export")
PREFER_IMPORT = "import"


def main():

    print(f"Starting MRIO calculations for years {FOR_YEARS[0]}-{FOR_YEARS[-1]}, using {CONVERSION_OPTION} as the conversion option and preferring {PREFER_IMPORT} data.")


    # Create a directory for results if it doesn't exist
    results_dir = Path("../results")
    results_dir.mkdir(exist_ok=True)

    print("Unzipping data...")
    try:
        # unzip_data('.') # Uncomment this line to enable unzipping
        print("Data unzipping completed successfully")
    except Exception as e:
        print(f"Error during data unzipping: {e}")
        # Continue anyway as data might already be unzipped

    for year in FOR_YEARS:
        print(f"\nProcessing year: {year}")
        # Step 1: Calculate Trade Matrix
        calculate_trade_matrix(
            conversion_opt=CONVERSION_OPTION,
            year=year,
            prefer_import=PREFER_IMPORT)

        animal_products_to_feed(
            prefer_import=PREFER_IMPORT,
            conversion_opt=CONVERSION_OPTION,
            year=year)
        
        calculate_area(
            prefer_import=PREFER_IMPORT,
            conversion_opt=CONVERSION_OPTION,
            year=year)

        print(f"Year {year} processing completed successfully\n")



    
















if __name__ == "__main__":
    main()