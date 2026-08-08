import pandas as pd
import requests

# Set Parameters
DATA_URL = 'https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/healthandsocialcare/healthandlifeexpectancies/datasets/healthstatelifeexpectancyallagesuk/current/healthylifeexpectancyuk.xlsx'
XLSX_FILE = 'healthylifeexpectancyuk.xlsx'
LCR_CSV = 'HealthyLifeExpectancyLCR.csv'

AREA_CODES = [
    'E08000011', 'E08000012', 'E08000015', 'E08000013',
    'E08000014', 'E06000006', 'W92000004', 'E92000001'
]

#COLUMNS_TO_KEEP = ['Period', 'Country', 'Area type', 'Area code', 'Area name', 'Sex', 'Sex code', 'Age group', 'Age code', 'HLE', 'LCI', 'UCI', 'Proportion (%)']


def download_file(DATA_URL, LCR_CSV):
    print("Downloading source file...")
    response = requests.get(DATA_URL)
    response.raise_for_status()
    with open(LCR_CSV, 'wb') as f:
        f.write(response.content)
    print(f"Saved to {LCR_CSV}")


def filter_data(xlsx_path: str) -> pd.DataFrame:
    df = pd.read_excel(xlsx_path, sheet_name='1', skiprows=6)

    filtered = df[
        (df['Area code'].isin(AREA_CODES)) &
        (df['Age group'] == '<1')
    ]
    print(f"Filtered {len(df)} rows down to {len(filtered)} rows.")

    return filtered
    #return filtered[COLUMNS_TO_KEEP]

def HealthyLifeExpectancyLCR():
    download_file(DATA_URL, XLSX_FILE)
    filtered_df = filter_data(XLSX_FILE)
    filtered_df.to_csv(LCR_CSV, index=False)
    print(f"Wrote filtered data to {LCR_CSV}")


if __name__ == '__main__':
    HealthyLifeExpectancyLCR()