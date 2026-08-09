import pandas as pd
import requests

# Set Parameters
DATA_URL = 'https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/healthandsocialcare/healthandlifeexpectancies/datasets/healthstatelifeexpectancyallagesuk/current/healthylifeexpectancyuk.xlsx'
XLSX_FILE = 'healthylifeexpectancyuk.xlsx'
LCR_CSV = 'HealthyLifeExpectancyLCR.csv'

#Areas to filter: Halton, Knowsley, Liverpool, St Helens, Sefton, Wirral, England, Wales
AREA_CODES = [
    'E06000006','E08000011', 'E08000012', 'E08000013', 'E08000014','E08000015', 'E92000001', 'W92000004'
]

#Comment Line below in and specify required columns if needed
#COLUMNS_TO_KEEP = ['Period', 'Country', 'Area type', 'Area code', 'Area name', 'Sex', 'Sex code', 'Age group', 'Age code', 'HLE', 'LCI', 'UCI', 'Proportion (%)']

def download_file(DATA_URL, LCR_CSV):
    print("Downloading data file...")
    response = requests.get(DATA_URL)
    response.raise_for_status()
    with open(LCR_CSV, 'wb') as f:
        f.write(response.content)
    print(f"Saved to {LCR_CSV}")

#Selects the correct tab from data sheet and removes the 6 lines of header before column headers
def filter_data(xlsx_path):
    df = pd.read_excel(xlsx_path, sheet_name='1', skiprows=6)

    filtered = df[
        (df['Area code'].isin(AREA_CODES)) &
        (df['Age group'] == '<1')
    ]
    print(f"Filtered {len(df)} rows down to {len(filtered)} rows.")

    return filtered
    #return filtered[COLUMNS_TO_KEEP] - Comment this line back in and comment out line 35 if COLUMNS_TO_KEEP has been set.

def HealthyLifeExpectancyLCR():
    download_file(DATA_URL, XLSX_FILE)
    filtered_df = filter_data(XLSX_FILE)
    filtered_df.to_csv(LCR_CSV, index=False)
    print(f"Filtered data saved to {LCR_CSV}")


if __name__ == '__main__':
    HealthyLifeExpectancyLCR()
