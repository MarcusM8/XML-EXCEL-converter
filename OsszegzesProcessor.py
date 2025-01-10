import pandas as pd
import os
import requests
import xml.etree.ElementTree as ET

ecorgan_url = "https://ecorgan.connectcenter.hu/feed/xml"  
ecorgan_username = "ecorgan"  
ecorgan_password = "blvTwEj6o"  

urls = {
    "Well": "https://www.weltservis.sk/feed.php?pass=5ceed4d7bed8ae6a4ed7a39d9cbaabe8",
    "DomaceKavovary": "https://feeds.mergado.com/domaci-kavovary-shoptet-dodavatelsky-cz-1-20747445fe2931179a409d9f156b45b6.xml"
}

local_files = {
    "Saját Sklad": "C:\\Users\\meszl\\OneDrive\\Dokumentumok\\sajatraktar.xls",  
    "Franke": "C:\\Users\\meszl\\OneDrive\\Dokumentumok\\Franke.xlsx"       
}


def download_ecorgan():
    response = requests.get(ecorgan_url, auth=(ecorgan_username, ecorgan_password))
    if response.status_code == 200:
        with open("ecorgan.xml", "wb") as file:
            file.write(response.content)
        print("Ecorgan XML sikeresen letöltve.")
        df = pd.read_xml("ecorgan.xml")
        if 'szabad_keszlet' in df.columns:
            df.rename(columns={'szabad_keszlet': 'STOCK'}, inplace=True)
        return df
    else:
        print(f"Hiba az Ecorgan letöltésekor: {response.status_code}")
        return pd.DataFrame()  


def download_xml(url, filename, stock_column):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, "wb") as file:
            file.write(response.content)
        print(f"{filename} sikeresen letöltve.")
        df = pd.read_xml(filename)
        if stock_column in df.columns:
            df.rename(columns={stock_column: 'STOCK'}, inplace=True)
        return df
    else:
        print(f"Hiba történt a fájl letöltésekor: {filename}")
        return pd.DataFrame() 

xml_dataframes = []


ecorgan_df = download_ecorgan()
if not ecorgan_df.empty:
    ecorgan_df['Source'] = "Ecorgan"
    xml_dataframes.append(ecorgan_df)


well_df = download_xml(urls["Well"], "Well.xml", "sklad")
if not well_df.empty:
    well_df['STOCK'] = pd.to_numeric(well_df['STOCK'], errors='coerce').fillna(0)
    well_df['Source'] = "Well"
    xml_dataframes.append(well_df)


domace_kavovary_df = download_xml(urls["DomaceKavovary"], "DomaceKavovary.xml", "Stock Amount")
if not domace_kavovary_df.empty:
    domace_kavovary_df['Source'] = "DomaceKavovary"
    xml_dataframes.append(domace_kavovary_df)


if os.path.exists(local_files["Saját Sklad"]):
    sklad_df = pd.read_excel(local_files["Saját Sklad"])
    if 'stock' in sklad_df.columns:
        sklad_df.rename(columns={'stock': 'STOCK'}, inplace=True)
    sklad_df['Source'] = "Saját Sklad"
    xml_dataframes.append(sklad_df)
else:
    print("Saját sklad fájl nem található!")


if os.path.exists(local_files["Franke"]):
    franke_df = pd.read_excel(local_files["Franke"])
    if 'amount' in franke_df.columns:
        franke_df.rename(columns={'amount': 'STOCK'}, inplace=True)
    franke_df['Source'] = "Franke"
    xml_dataframes.append(franke_df)
else:
    print("Franke napi táblázat nem található!")


for df in xml_dataframes:
    if 'cikkszam' in df.columns:
        df.rename(columns={'cikkszam': 'Product Code'}, inplace=True)


all_data = pd.concat(xml_dataframes, ignore_index=True)


all_data['STOCK'] = pd.to_numeric(all_data['STOCK'], errors='coerce').fillna(0)


if 'Product Code' in all_data.columns and 'STOCK' in all_data.columns:
    summary_table = all_data.groupby('Product Code', as_index=False)['STOCK'].sum()
    print("Csoportosítás sikeresen elkészült.")
else:
    print("A 'Product Code' vagy 'STOCK' oszlop nem található az összesített adatokban.")
    summary_table = pd.DataFrame()


if not summary_table.empty:
    excel_output = "C:\\Users\\meszl\\OneDrive\\Dokumentumok\\summary_data.xlsx"
    summary_table.to_excel(excel_output, index=False)
    print(f"Az Excel fájl sikeresen elkészült: {excel_output}")


if not summary_table.empty:
    root = ET.Element("SHOP")
    for _, row in summary_table.iterrows():
        shopitem = ET.SubElement(root, "SHOPITEM")
        code = ET.SubElement(shopitem, "CODE")
        code.text = str(row['Product Code'])
        stock = ET.SubElement(shopitem, "STOCK")
        stock.text = str(int(row['STOCK']))

    final_xml = "C:\\Users\\meszl\\OneDrive\\Dokumentumok\\final_output.xml"
    tree = ET.ElementTree(root)
    tree.write(final_xml, encoding="utf-8", xml_declaration=True)
    print(f"A végleges XML fájl elkészült: {final_xml}")
