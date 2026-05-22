from pathlib import Path
import pandas as pd

results_dir = Path("/maps/tsb42/leakage_v1/mrio_pipeline_results_260409")

countries = ["USA", "NLD", "GBR", "DEU", "FRA", "TZA"]
years = None

def calculate_self_sufficiency_ratios(results_dir: Path, countries=None, years=None) -> pd.DataFrame:

    df = pd.DataFrame()

    year_dirs = sorted(results_dir.glob("*"))
    year_dirs = [d for d in year_dirs if "impacts" not in d.name and d.is_dir()]
    if years is not None:
        year_dirs = [d for d in year_dirs if d.name in years]

    for year_dir in year_dirs:
        c_dirs= list(year_dir.glob("*"))
        c_dirs = [f for f in c_dirs if f.is_dir() and f.name != ".mrio"] #and f.name != "impacts"]
        if countries is not None:
            c_dirs = [f for f in c_dirs if f.name in countries]

        for c_dir in c_dirs:
            c = c_dir.name
            year = year_dir.name
            print(f"Processing {c} in {year}...")
            
            try:
                df_c = pd.read_csv(c_dir / f"df_{c.lower()}.csv")
                df_imported = pd.read_csv(c_dir / f"df_os.csv")
                df_full = pd.read_csv(c_dir / f"impacts_full.csv")

                domestic_no_feed = df_c.tonnage.sum()
                imported_no_feed = df_imported.tonnage.sum()

                domestic_full = df_full[df_full.Country_ISO == c.upper()].provenance.sum()
                imported_full = df_full[df_full.Country_ISO != c.upper()].provenance.sum()

                new_row = pd.DataFrame([{
                    "country": c,
                    "year": year,
                    "domestic_tonnes_no_feed": domestic_no_feed,
                    "imported_tonnes_no_feed": imported_no_feed,
                    "ratio_no_feed": domestic_no_feed / (domestic_no_feed + imported_no_feed),
                    "domestic_tonnes_full": domestic_full,
                    "imported_tonnes_full": imported_full,
                    "ratio_full": domestic_full / (domestic_full + imported_full)
                }])

                df = pd.concat([df, new_row], ignore_index=True)

            except Exception as e:
                print(f"Error processing {c} in {year}: {e}")
            

    return df

if __name__ == "__main__":
    df = calculate_self_sufficiency_ratios(results_dir=results_dir, years=years, countries=countries)
    Path(results_dir / "ssr").mkdir(exist_ok=True)
    df.to_csv(results_dir / "ssr" /  "self_sufficiency_ratios.csv", index=False)