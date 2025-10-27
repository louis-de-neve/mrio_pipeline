
import pandas as pd
import numpy as np
import os
import warnings


def main(year, coi_iso):
    datPath = "./input_data"
    scenPath = f"./results/{year}/{coi_iso}"

    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        country_code_data = pd.read_excel(f"{datPath}/nocsDataExport_20251021-164754.xlsx")
    coi = country_code_data.loc[country_code_data["ISO3"]==coi_iso]["FAOSTAT"].values[0]

    bd_path = f"{datPath}/country_opp_cost_v6.csv"
    grouping = "group_name_v7"
    
    # coi = 229
    
    #%%
    cropdb = pd.read_csv(f"{datPath}/crop_db.csv")
    bd_opp_cost = pd.read_csv(bd_path, index_col = 0)
    
    bh = pd.read_csv(f"{scenPath}/human_consumed_impacts_wErr.csv", index_col = 0)
    bf = pd.read_csv(f"{scenPath}/feed_impacts_wErr.csv", index_col = 0)
     
    #%%
    bf["bd_opp_cost_calc"] = bf["bd_opp_cost_calc"].mask(bf["bd_opp_cost_calc"].lt(0),0)
    
    bh = bh[np.logical_not(np.isinf(bh.FAO_land_calc_m2))]
    bh.loc[:, "ItemT_Name"] = bh.loc[:, "Item"]
    bh.loc[:, "ItemT_Code"] = bh.loc[:, "Item_Code"]
    bh.loc[:, "Arable_m2"] = bh.FAO_land_calc_m2
    bh.loc[:, "Pasture_m2"] = bh.Pasture_avg_calc.fillna(0)
    bh["bd_perc_err"] = bh["bd_opp_cost_calc_err"] / bh["bd_opp_cost_calc"]
    
    bf = bf[np.logical_not(np.isinf(bf.FAO_land_calc_m2))]
    bf.loc[:, "ItemT_Code"] = bf.loc[:, "Animal_Product_Code"]
    bf.loc[:, "ItemT_Name"] = bf.loc[:, "Animal_Product"]
    bf.loc[:, "Arable_m2"] = bf.FAO_land_calc_m2
    bf.loc[:, "Pasture_m2"] = 0
    bf["bd_perc_err"] = bf["bd_opp_cost_calc_err"] / bf["bd_opp_cost_calc"]
    bf = bf[~np.isinf(bf.bd_perc_err)]
    xdf = pd.concat([bh,bf])
    
    xdfs_uk = xdf[xdf.Producer_Country_Code == coi].groupby("ItemT_Name").sum()
    xdfs_os = xdf[~(xdf.Producer_Country_Code == coi)].groupby("ItemT_Name").sum()
    
    df_uk = pd.DataFrame()
    
    for item in xdfs_uk.index.tolist():
        x = xdfs_uk.loc[item]
        try:
            df_uk.loc[item, "Group"] = cropdb[cropdb.Item == item][grouping].values[0]
            df_uk.loc[item, "Pasture_m2"] = x.Pasture_m2
            df_uk.loc[item, "Arable_m2"] = x.Arable_m2
            df_uk.loc[item, "Scarcity_weighted_water_l"] = x.SWWU_avg_calc.sum()
            df_uk.loc[item, "ghg_food"] = bh[(bh.Item == item)&(bh.Producer_Country_Code == coi)].GHG_avg_calc.sum()
            df_uk.loc[item, "ghg_feed"] = bf[(bf.Animal_Product == item)&(bf.Producer_Country_Code == coi)].GHG_avg_calc.sum()
            df_uk.loc[item, "ghg_total"] =  df_uk.loc[item, "ghg_feed"] + df_uk.loc[item, "ghg_food"]
            df_uk.loc[item, "bd_opp_food"] = bh[(bh.Item == item)&(bh.Producer_Country_Code == coi)]["bd_opp_cost_calc"].sum()
            df_uk.loc[item, "bd_opp_feed"] = bf[(bf.Animal_Product == item)&(bf.Producer_Country_Code == coi)]["bd_opp_cost_calc"].sum()
            df_uk.loc[item, "bd_opp_total"] = df_uk.loc[item, "bd_opp_feed"] + df_uk.loc[item, "bd_opp_food"]
            
            # bd opp food err
            df_uk.loc[item, "bd_opp_food_err"] = df_uk.loc[item, "bd_opp_food"] \
                * np.sqrt(np.nansum(np.array(bh[(bh.Item==item)&(bh.Producer_Country_Code==coi)].bd_perc_err) ** 2))
            # bd opp feed err
            df_uk.loc[item, "bd_opp_feed_err"] = df_uk.loc[item, "bd_opp_feed"] \
                * np.sqrt(
                    np.nansum(np.array(bf[(bf.Animal_Product==item)&(bf.Producer_Country_Code==coi)].bd_perc_err) ** 2)
                    )
            # bd opp total error
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fe_err = df_uk.loc[item, "bd_opp_feed_err"]/df_uk.loc[item, "bd_opp_feed"]
                fo_err = df_uk.loc[item, "bd_opp_food_err"]/df_uk.loc[item, "bd_opp_food"]
            
            df_uk.loc[item, "bd_opp_total_err"] = df_uk.loc[item, "bd_opp_total"] \
                * np.sqrt(np.nansum(np.nansum([(fe_err)**2,(fo_err)**2])))
            
            
            df_uk.loc[item, "Cons"] = bh[(bh.Item == item)&(bh.Producer_Country_Code == coi)].provenance.sum()
            df_uk.loc[item, "Cons_err"] = np.sqrt(np.nansum(bh[(bh.Item == item)&(bh.Producer_Country_Code == coi)].provenance_err ** 2))
            
        except IndexError:
            print(f"Couldn't find {item} in the db")
    
    df_os = pd.DataFrame()
    count = 0
    for item in xdfs_os.index.tolist():
        x = xdfs_os.loc[item]
        try:
            df_os.loc[item, "Group"] = cropdb[cropdb.Item == item][grouping].values[0]
            df_os.loc[item, "Pasture_m2"] = x.Pasture_m2
            df_os.loc[item, "Arable_m2"] = x.Arable_m2
            df_os.loc[item, "Scarcity_weighted_water_l"] = x.SWWU_avg_calc.sum()
            df_os.loc[item, "ghg_food"] = bh[(bh.Item == item)&(bh.Producer_Country_Code != coi)].GHG_avg_calc.sum()
            df_os.loc[item, "ghg_feed"] = bf[(bf.Animal_Product == item)&(bf.Producer_Country_Code != coi)].GHG_avg_calc.sum()
            df_os.loc[item, "ghg_total"] =  df_os.loc[item, "ghg_feed"] + df_os.loc[item, "ghg_food"]
            df_os.loc[item, "bd_opp_food"] = bh[(bh.Item == item)&(bh.Producer_Country_Code != coi)]["bd_opp_cost_calc"].sum()
            df_os.loc[item, "bd_opp_feed"] = bf[(bf.Animal_Product == item)&(bf.Producer_Country_Code != coi)]["bd_opp_cost_calc"].sum()
            df_os.loc[item, "bd_opp_total"] = df_os.loc[item, "bd_opp_feed"] + df_os.loc[item, "bd_opp_food"]
            # if item not in df_uk.index:
            df_os.loc[item, "Cons"] = bh[(bh.Item == item)&(bh.Producer_Country_Code !=coi)].provenance.sum()
            df_os.loc[item, "Cons_err"] = np.sqrt(np.nansum(bh[(bh.Item == item)&(bh.Producer_Country_Code !=coi)].provenance_err ** 2))
            
            # bd opp food err
            df_os.loc[item, "bd_opp_food_err"] = df_os.loc[item, "bd_opp_food"] \
                * np.sqrt(np.nansum(np.array(bh[(bh.Item==item)&(bh.Producer_Country_Code!=coi)].bd_perc_err) ** 2))
            # bd opp feed err
            df_os.loc[item, "bd_opp_feed_err"] = df_os.loc[item, "bd_opp_feed"] \
                * np.sqrt(
                    np.nansum(np.array(bf[(bf.Animal_Product==item)&(bf.Producer_Country_Code!=coi)].bd_perc_err) ** 2)
                    )
            # bd opp total error
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fe_err = df_os.loc[item, "bd_opp_feed_err"]/df_os.loc[item, "bd_opp_feed"]
                fo_err = df_os.loc[item, "bd_opp_food_err"]/df_os.loc[item, "bd_opp_food"]
            
            df_os.loc[item, "bd_opp_total_err"] = df_os.loc[item, "bd_opp_total"] \
                * np.sqrt(np.nansum(np.nansum([(fe_err)**2,(fo_err)**2])))
    
        except IndexError:
            count += 1
            # print(f"Couldn't find {item} in the db")
    if count > 0:
        print("         WARNING: Some items missing from database")
    kdf = pd.concat([df_uk,df_os])
    kdf = kdf.groupby([kdf.index, "Group"]).sum().reset_index()

    df_uk.to_csv(f"{scenPath}/df_uk.csv")
    df_os.to_csv(f"{scenPath}/df_os.csv")
    xdf.to_csv(f"{scenPath}/xdf.csv")
    
    if "Item" not in kdf.columns:
        
        kdf.columns = [_ if _ != "level_0" else "Item" for _ in kdf.columns]
    
    kdf.to_csv(f"{scenPath}/kdf.csv")
    
if __name__ == "__main__":
    
    #%%
    datPath = "dat"
    # scenPath = os.path.join(odPath, "Work\\Work for others\\Catherine CLR\\food_results\\gbr")

