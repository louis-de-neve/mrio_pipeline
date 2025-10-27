# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 16:55:34 2022

@author: Thomas Ball
"""
import pandas as pd
import numpy as np
import os
    

def area_code_to_iso(code, area_codes):
    iso3 = area_codes[area_codes["FAOSTAT"] == code]["ISO3"].values[0]
    return iso3


def item_code_to_product(code, item_codes):
    vals = item_codes[item_codes["Item Code"] == code]["Item"].values
    product = vals[0] if len(vals) > 0 else None
    return product


def add_cols(indf, area_codes, item_codes):
    ac = area_codes[["ISO3", "FAOSTAT"]].rename(columns={"ISO3":"Country_ISO", "FAOSTAT":"Producer_Country_Code"})
    indf = indf.merge(ac, on="Producer_Country_Code", how="left")
    
    ic = item_codes[["Item Code", "Item"]].rename(columns={"Item Code":"Item_Code"})
    indf = indf.merge(ic, on="Item_Code", how="left")

    if "Animal_Product_Code" in indf.columns:
        ic = ic.rename(columns={"Item_Code":"Animal_Product_Code", "Item":"Animal_Product"})
        indf = indf.merge(ic, on="Animal_Product_Code", how="left")

    return indf


def calculate_conversion_factors(conversion_opt, content_factors, item_map_for_cf):
        """Calculate conversion factors from processed to primary items"""

        content_factors.rename(columns=lambda x: x.replace(" ", "_"), inplace=True)
        item_map_for_cf.rename(columns=lambda x: x.replace(" ", "_"), inplace=True)    
    
        # Calculate conversion factors
        if conversion_opt not in content_factors.columns:
                raise ValueError(f"Primary Conversion option ({conversion_opt}) not available")
                
        joined = item_map_for_cf.merge(
            content_factors[["Item_Code", conversion_opt]], 
            left_on="FAO_code", 
            right_on="Item_Code", 
            how="left")

        joined = joined.merge(
            content_factors[["Item_Code", conversion_opt]], 
            left_on="primary_item", 
            right_on="Item_Code", 
            how="left",
            suffixes=("_processed", "_primary"))

        joined["Conversion_factor"] = joined[f"{conversion_opt}_primary"] / joined[f"{conversion_opt}_processed"]
        joined.loc[~np.isfinite(joined["Conversion_factor"]), "Conversion_factor"] = 0
        joined = joined.dropna(subset=["Conversion_factor"])
        conversion_factors = joined[["FAO_code", "FAO_name_primary", "primary_item", "Conversion_factor"]]
        conversion_factors = conversion_factors.rename(columns={"primary_item":"primary_item_code",
                                           "FAO_name_primary":"primary_item",
                                           "Conversion_factor":"ratio"})
        conversion_factors.drop_duplicates(subset=["FAO_code"], inplace=True)
        return conversion_factors


def main(year, country_of_interest):

    country_savefile_path = f"./results/{year}/{country_of_interest}"
    if not os.path.isdir(country_savefile_path):
        os.makedirs(country_savefile_path)   

    datPath = "./input_data"
    trade_feed = f"./results/{year}/.mrio/TradeMatrixFeed_import_dry_matter.csv"
    trade_nofeed = f"./results/{year}/.mrio/TradeMatrix_import_dry_matter.csv"

    item_codes = pd.read_csv(f"{datPath}/SUA_Crops_Livestock_E_ItemCodes.csv", encoding = "latin-1", low_memory=False)

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        area_codes = pd.read_excel(f"{datPath}/nocsDataExport_20251021-164754.xlsx", engine="openpyxl")  
        factors = pd.read_excel(f"{datPath}/content_factors_per_100g.xlsx", skiprows=1, engine="openpyxl")

    item_map = pd.read_csv(f"{datPath}/primary_item_map_feed.csv", encoding = "latin-1")
    weighing_factors = pd.read_csv(f"{datPath}/weighing_factors.csv", encoding = "latin-1")
    prov_mat_no_feed = pd.read_csv(trade_nofeed)
    prov_mat_feed = pd.read_csv(trade_feed)

    coi_code = area_codes[area_codes["ISO3"] == country_of_interest]["FAOSTAT"].values[0]

    item_codes.columns = [_.strip() for _ in item_codes.columns]
    add_palestine = pd.DataFrame({"ISO3":["PSE"], "FAOSTAT":[299]})
    area_codes = pd.concat([area_codes, add_palestine], ignore_index=True)

    sua = pd.read_csv(f"{datPath}/SUA_Crops_Livestock_E_All_Data_(Normalized).csv", encoding="latin-1", low_memory=False)
    fs = sua[(sua["Area Code"]==coi_code)&(sua["Element Code"]==5141)]




    fs = fs[fs.Year == year]
    fserr = fs.copy()

    # ERROR CALCULATION - commented out for now
    # fs = fs[(fs.Year <= year+2) & (fs.Year >= year-2)]
    # fserr = fserr[(fserr.Year <= year+2) & (fserr.Year >= year-2)]

    # means = fs.groupby(["Item", "Item Code"]).Value.mean().reset_index()
    # errs = fs.groupby(["Item", "Item Code"]).Value.sem().reset_index() # no groupings so this is just zero

    # for item in means.Item:
    #     fs.loc[fs.Item == item, "Value"] = means[means.Item==item].Value.values[0]
    #     fserr.loc[fserr.Item == item, "Value"] = errs[errs.Item==item].Value.values[0]

    ic = item_codes.rename(columns={"CPC Code":"Item Code (CPC)", "Item Code":"FAO_code", "Item":"item_name"})
    fs = fs.merge(ic, on="Item Code (CPC)", how="left")
    fserr = fserr.merge(ic, on="Item Code (CPC)", how="left")

    

    imports_feed = prov_mat_feed[prov_mat_feed.Consumer_Country_Code == coi_code]
    imports_feed = add_cols(imports_feed, area_codes=area_codes, item_codes=item_codes)
    imports_feed = imports_feed[~imports_feed.Item.isna()]   
    imports_feed_crops = imports_feed[(imports_feed.Animal_Product.isna()) & (imports_feed.Value >= 0)]
    imports_feed_crops.loc[:, 'Animal_Product'] = ""

    imports_no_feed = prov_mat_no_feed[prov_mat_no_feed.Consumer_Country_Code == coi_code]
    imports_no_feed = add_cols(imports_no_feed, area_codes=area_codes, item_codes=item_codes)
    imports_no_feed = imports_no_feed[~imports_no_feed.Item.isna()]
    imports_no_feed = imports_no_feed[imports_no_feed.Item_Code.isin(imports_feed.Animal_Product_Code.unique())]
    imports_no_feed.loc[:, 'Animal_Product'] = "Primary"

    imports_total = pd.concat([imports_feed_crops, imports_no_feed])

    human_consumed_import_ratios = (imports_total
        .groupby(["Item_Code", "Animal_Product"])[imports_total.columns]
        .apply(lambda x: x.assign(Ratio=x["Value"] / x["Value"].sum()))
        .reset_index(drop=True)
        .drop(columns=["Value"]))
    
    human_consumed_import_ratios.loc[human_consumed_import_ratios.Animal_Product=="", "Animal_Product"] = np.nan



    df_hc, df_hc_err = fs.copy(), fserr.copy() # TODO remove copy
    cf = calculate_conversion_factors("dry_matter", factors.copy(), item_map.copy())
    df_hc = df_hc.merge(cf, on="FAO_code", how="left")
    df_hc_err = df_hc_err.merge(cf, on="FAO_code", how="left")
    df_hc=df_hc[df_hc["ratio"]!=0]

    df_hc.dropna(subset=["ratio"], inplace=True)
    
    df_hc["value_primary"] = df_hc.Value / df_hc.ratio
    df_hc_err["value_primary_err"] = df_hc_err["Value"]**2


    primary_consumption = (df_hc
        .groupby(["primary_item_code"])[df_hc.columns]
        .apply(lambda x: x.assign(value_primary=x["value_primary"].sum()))
        .reset_index(drop=True)
        [['primary_item_code', 'value_primary']]
        .drop_duplicates(subset=["primary_item_code"])
        .merge(
            item_codes[["Item Code", "Item"]].rename(columns={"Item Code":"primary_item_code", "Item":"item_name"}),
            on="primary_item_code",
            how="left"))
        
    df_hc_err = (df_hc_err
        .groupby(["primary_item_code"])[df_hc_err.columns]
        .apply(lambda x: x.assign(value_primary_err=np.sqrt(x["value_primary_err"].sum())))
        .reset_index(drop=True)
        [['primary_item_code', 'value_primary_err']]
        .drop_duplicates(subset=["primary_item_code"]))
    primary_consumption = primary_consumption.merge(df_hc_err, on="primary_item_code", how="left")

    
    print("         Calculating human consumed provenance")
    cons_prov = (human_consumed_import_ratios
        .merge(primary_consumption, left_on="Item_Code", right_on="primary_item_code", how="left")
        .drop(columns=["primary_item_code", "item_name"]))
    cons_prov["provenance"] = cons_prov["Ratio"] * cons_prov["value_primary"]
    cons_prov["provenance_err"] = cons_prov.provenance * np.sqrt(1+(cons_prov.value_primary_err/cons_prov.value_primary)**2)
    cons_prov = (cons_prov
        .drop(columns=["value_primary", "value_primary_err"])
        .dropna(subset=["provenance"]))


    primary_consumption_anim = primary_consumption[primary_consumption.primary_item_code.isin(weighing_factors.Item_Code)]
    
    ##################################################

    primary_consumption_anim = primary_consumption_anim.merge(weighing_factors, left_on="primary_item_code", right_on="Item_Code", how="left")
    primary_consumption_anim['value_primary'] = primary_consumption_anim['value_primary'] * primary_consumption_anim['Weighing factors']
    primary_consumption_anim['value_primary_err'] = primary_consumption_anim['value_primary_err'] * primary_consumption_anim['Weighing factors']
    primary_consumption_anim = primary_consumption_anim[primary_consumption_anim['Weighing factors'] > 0]
    primary_consumption_anim = primary_consumption_anim.drop(columns=["Item_Code", "Item", "Weighing factors"])
    
    prov_mat_feed.loc[prov_mat_feed["Animal_Product_Code"].isna(), "Animal_Product_Code"] = 0
    prov_mat_feed = prov_mat_feed[~(prov_mat_feed.Value.isna())&(prov_mat_feed.Value > 0)]
    prov_mat_feed = (prov_mat_feed
        .groupby(["Animal_Product_Code", "Consumer_Country_Code"])[prov_mat_feed.columns]
        .apply(lambda x: x.assign(prov_ratio=x["Value"] / x["Value"].sum()))
        .reset_index(drop=True))
    prov_mat_feed.loc[prov_mat_feed["Animal_Product_Code"]==0, "Animal_Product_Code"] = np.nan


    ##################################################

    # provenance of feed
    feed_prov = pd.DataFrame()
    # primary_consumption_anim = primary_consumption_anim[primary_consumption_anim.primary_item_code==882] # REMOVE ##################
    # get animal product
    print("         Calculating feed provenance")

    for row in primary_consumption_anim.iterrows():
        primary_item_code, value_primary, item_name, value_primary_err = row[1]
        source_countries = human_consumed_import_ratios[
            human_consumed_import_ratios.Item_Code == primary_item_code]
        
        # source_countries = source_countries[source_countries.Producer_Country_Code.isin([229,104,68])] # REMOVE ##################

        # prov_mat_feed = prov_mat_feed.merge

        # get countries that produce the animal product
        for rowx in source_countries.iterrows():
            cRatio = rowx[1].Ratio
            country_code = rowx[1].Producer_Country_Code
            cVal = value_primary * cRatio
            cVal_err = value_primary_err * cRatio
            # where do they get their feed from?
            dfx = prov_mat_feed[
                (prov_mat_feed.Animal_Product_Code==primary_item_code)\
                    &(prov_mat_feed.Consumer_Country_Code==country_code)].copy()

            dfx["provenance"] = dfx.prov_ratio * cVal
            if dfx["provenance"].sum() > 0 and cVal > 0:
                dfx["provenance_err"] = dfx["provenance"] * np.sqrt(1+(cVal_err/cVal)**2)
            dfx["Country_ISO"] = [area_code_to_iso(code, area_codes) for code in dfx.Producer_Country_Code]
            dfx["Item"] = [item_code_to_product(code, item_codes) for code in dfx.Item_Code]
            dfx["Animal_Product"] = item_name
            feed_prov = pd.concat([feed_prov, dfx])
    
    cons_prov["Value"] = cons_prov["Ratio"]



    cons_prov = cons_prov[(cons_prov.Ratio > 1E-8)&(cons_prov.provenance > 0)]
    cons_prov.to_csv(f"{country_savefile_path}/human_consumed.csv")
    feed_prov = feed_prov[(feed_prov.Value > 1E-8)&(feed_prov.provenance > 0)]
    feed_prov.to_csv(f"{country_savefile_path}/feed.csv")
    return cons_prov, feed_prov
