#!/usr/bin/env python3
"""
This code is a translation/re-written python script of the original R code of the following publication:
Schwarzmueller, F. & Kastner, T (2022), Agricultural trade and its impact on cropland use
and the global loss of species' habitats. Sustainability Science, doi: 10.1007/s11625-022-01138-7
(c) Florian Schwarzmueller, December 2021

It is then combined with the food_LIFE codebase for impact assessment:
Ball, T.S., Dales, M., Eyres, A. et al. Food impacts on species extinction risks can vary by three orders of magnitude.
Nat Food 6, 848–856 (2025). doi: 10.1038/s43016-025-01224-w

Please cite ;-)

This script was written in Python, October 2025 by Louis De Neve

Added multiprocessing (country-level parallelism), October/December 2025 by Thomas Ball
"""

import os
from pathlib import Path
import time

import multiprocessing

from processing.unzip_data import unzip_data
from processing.calculate_trade_matrix import calculate_trade_matrix
from processing.calculate_error_matrix import calculate_error_matrix
from processing.animal_products_to_feed import animal_products_to_feed

from provenance._get_biodiversity_vals import fetch_biodiversity_vals_path
from provenance._provenance import main as consumption_provenance_main
from provenance._get_impacts_bd import get_impacts as get_impacts_main
from provenance._process_dat import main as process_dat_main
from provenance._process_dat import main_global as process_dat_main_global

from pandas import read_excel, read_csv

# CONFIG
RESULTS_DIR = "../mrio_pipeline_results_260713"
ERROR_ITERATIONS = 1000
YEARS = list(range(2010, 2022))

# Select a conversion method
CONVERSION_OPTION = "dry_matter"

# Prefer import or export data
PREFER_IMPORT = "import"

# select working directory
WORKING_DIR = '.'

USE_2020_DATA = True # have updated to use most recent mapspam - UK/Ghana/USA issues fixed though it seems some issues persist.

# Multiprocessing settings
N_PROCESSES = 32

# Pipeline components to run
# 0 = all, 1 = unzip, error matrix, 3 = trade matrix, 4 = animal products to feed, 5 = country impacts
PIPELINE_COMPONENTS: list = [0]

cdat = read_excel("input_data/nocsDataExport_20251021-164754.xlsx")
COUNTRIES = [_.upper() for _ in cdat["ISO3"].unique().tolist() if isinstance(_, str)]
# COUNTRIES = ["USA", "IND", "BRA", "JPN", "UGA", "GBR"]



def _process_year_matrices(year: int, hist: str, conversion_option: str, prefer_import: str, results_dir: Path, error_data):
    """
    Runs the per-year, all-countries-at-once steps (trade matrix + animal-to-feed
    conversion + biodiversity value fetch). Independent across years, so callers
    can run this over a pool spanning all years.
    """
    try:
        print(f"    [PID {os.getpid()}] Computing trade matrix for year {year}")
        t0 = time.perf_counter()
        calculate_trade_matrix(
            conversion_opt=conversion_option,
            prefer_import=prefer_import,
            year=year,
            historic=hist,
            results_dir=results_dir,
            all_error_data=error_data)
        animal_products_to_feed(
            prefer_import=prefer_import,
            conversion_opt=conversion_option,
            year=year,
            historic=hist,
            results_dir=results_dir)
        fetch_biodiversity_vals_path(year, "./input_data")
        t1 = time.perf_counter()
        print(f"    [PID {os.getpid()}] Completed matrices for year {year} in {t1 - t0:.2f} seconds")
        return (year, None)
    except Exception as e:
        print(f"    [PID {os.getpid()}] Error computing matrices for year {year}: {e}")
        return (year, str(e))


def _process_country(country: str, year: int, hist: str):
    missing_items_local = []
    try:
        print(f"    [PID {os.getpid()}] Processing country: {country}")
        t0 = time.perf_counter()
        # consumption_provenance_main returns (cons, feed) per original script
        cons, feed = consumption_provenance_main(year, country, hist, results_dir=Path(RESULTS_DIR))
        if len(cons) == 0:
            print(f"    [PID {os.getpid()}] No consumption data for {country} in {year}")
            return []  # nothing to do for this country
        bf = get_impacts_main(feed, year, country, "feed_impacts_wErr.csv", results_dir=Path(RESULTS_DIR), use_2020=USE_2020_DATA)
        bh = get_impacts_main(cons, year, country, "human_consumed_impacts_wErr.csv", results_dir=Path(RESULTS_DIR), use_2020=USE_2020_DATA)
        if country == "WORLD":
            mi = process_dat_main_global(year, "WORLD", bh, bf, results_dir=Path(RESULTS_DIR))
        else:
            mi = process_dat_main(year, country, bh, bf, results_dir=Path(RESULTS_DIR))
        missing_items_local.extend(mi)
        t1 = time.perf_counter()
        print(f"    [PID {os.getpid()}] Completed {country} in {t1 - t0:.2f} seconds")
        return missing_items_local
    except Exception as e:
        # Print error and continue; return empty list so caller can continue aggregating
        print(f"    [PID {os.getpid()}] Error processing {country} for {year}: {e}")
        return []


def main(years=list(range(1986, 2022)),
         conversion_option="dry_matter",
         prefer_import="import",
         pipeline_components=[0],
         working_dir=".",
         countries=None,
         results_dir="./results",
         n_processes=None):

    if countries is None:
        countries = COUNTRIES

    # os.system('cls' if os.name == 'nt' else 'clear')
    os.chdir(working_dir)

    component_dict = {
        0: "Full pipeline",
        1: "Unzipping data",
        2: "Error matrix calculation",
        3: "Trade matrix calculation",
        4: "Animal products to feed calculation",
        5: "Country-level provenance calculations",
    }

    print(f"""\nStarting MRIO calculations with options:
    Working directory: {working_dir}
    Using {conversion_option} as the conversion option
    Preferring {prefer_import} data
    Running pipeline component {[p for p in pipeline_components]}: {[component_dict[p] for p in pipeline_components]}

    Years to process: {years}
    """)

    # check results dir
    results_dir = Path(results_dir)
    results_dir.mkdir(exist_ok=True)

    if (0 in pipeline_components) or (1 in pipeline_components):
        print("Unzipping data...")
        try:
            unzip_data("./input_data") 
            print("Data already unzipped or unzipping completed successfully.")
        except Exception as e:
            print(f"Error during data unzipping: {e}")

    if pipeline_components == [1]:
        return
    
    if (0 in pipeline_components) or (2 in pipeline_components):
        error_data = calculate_error_matrix(
            conversion_opt=conversion_option,
            prefer_import=prefer_import,
            historic="",
            iterations=ERROR_ITERATIONS)
    else:
        error_data = None

    if n_processes is None:
        try:
            n_processes = max(1, multiprocessing.cpu_count() - 1)
        except Exception:
            n_processes = 1

    # Phase 0: directory setup + per-year historic flag, cheap and sequential
    year_hist = {}
    for year in years:
        year_dir = results_dir / str(year)
        year_dir.mkdir(exist_ok=True)
        mrio_dir = results_dir / str(year) / ".mrio"
        mrio_dir.mkdir(exist_ok=True)
        for country in countries:
            country_dir = results_dir / str(year) / country
            country_dir.mkdir(exist_ok=True)
        year_hist[year] = "Historic" if year < 2010 else ""

    # Phase 1: trade matrix + animal-to-feed conversion, parallel across years
    if (0 in pipeline_components) or (3 in pipeline_components) or (4 in pipeline_components):
        processes = min(n_processes, len(years))
        print(f"\nComputing trade matrices for {len(years)} years using up to {processes} worker processes")
        args_iterable = [(y, year_hist[y], conversion_option, prefer_import, results_dir, error_data) for y in years]
        if processes == 1:
            results = [_process_year_matrices(*args) for args in args_iterable]
        else:
            with multiprocessing.Pool(processes=processes) as pool:
                results = pool.starmap(_process_year_matrices, args_iterable)
        for y, err in results:
            if err:
                print(f"Error computing matrices for year {y}: {err}")

    # Phase 2: country-level provenance and impacts, parallel across (year, country)
    if (0 in pipeline_components) or (5 in pipeline_components):
        print("\nProcessing country-level provenance and impacts...")
        tasks = [(country, year, year_hist[year]) for year in years for country in countries]

        if n_processes == 1:
            results = [_process_country(*task) for task in tasks]
        else:
            processes = min(n_processes, len(tasks))
            print(f"    Spawning {processes} worker processes for {len(tasks)} (year, country) tasks")
            with multiprocessing.Pool(processes=processes) as pool:
                results = pool.starmap(_process_country, tasks)

        missing_by_year = {year: [] for year in years}
        for (country, year, hist), res in zip(tasks, results):
            if res:
                missing_by_year[year].extend(res)

        for year in years:
            missing_items_file = results_dir / str(year) / "missing_items.txt"
            with open(missing_items_file, "w") as f:
                f.write("Items missing from crosswalk and their codes:\n")
                for item, code in set(missing_by_year[year]):
                    f.write(f" - {item}: {code}\n")

    print("\nAll years processed successfully\n")

if __name__ == "__main__":

    main(
        years=YEARS,
        conversion_option=CONVERSION_OPTION,
        prefer_import=PREFER_IMPORT,
        pipeline_components=PIPELINE_COMPONENTS,
        working_dir=WORKING_DIR,
        results_dir=RESULTS_DIR,
        countries=COUNTRIES,
        n_processes=N_PROCESSES, 
    )