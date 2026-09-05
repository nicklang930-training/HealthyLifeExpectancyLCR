import os
import smtplib
from email.mime.text import MIMEText
import traceback
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import requests

##load in email variables
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Set Parameters
DATA_URL = 'https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/healthandsocialcare/healthandlifeexpectancies/datasets/healthstatelifeexpectancyallagesuk/current/healthylifeexpectancyuk.xlsx'
XLSX_FILE = 'healthylifeexpectancyuk.xlsx'

AREA_CODES = [
    'E08000011', 'E08000012', 'E08000015', 'E08000013',
    'E08000014', 'E06000006', 'W92000004', 'E92000001'
]

SHEET_CONFIG = {
    '1': {'header_row': 6, 'meta_rows': [0, 3, 4], 'output': 'HealthyLifeExpectancyLCR.xlsx'},
    '3': {'header_row': 6, 'meta_rows': [0, 3, 4], 'output': 'ChangeInHealthyLifeExpectancyLCR.xlsx'},
}

EMAIL_SENDER = os.environ.get("EMAIL_APP_SENDER")
EMAIL_RECIPIENT = os.environ.get("EMAIL_APP_FAIL_RECIPIENT")
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")

def send_error_email(subject: str, body: str):
    if not EMAIL_APP_PASSWORD:
        print("Warning: EMAIL_APP_PASSWORD not set, cannot send error email.")
        return
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECIPIENT
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
        server.send_message(msg)

def download_file(DATA_URL, LCR_CSV):
    print("Downloading source file...")
    response = requests.get(DATA_URL)
    response.raise_for_status()
    with open(LCR_CSV, 'wb') as f:
        f.write(response.content)
    print(f"Saved to {LCR_CSV}")




def filter_data(xlsx_path, sheet_name, header_row, meta_rows) -> pd.DataFrame:
    max_meta_row = max(meta_rows)
    metafull = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=None, nrows=max_meta_row + 1)
    meta = metafull.iloc[meta_rows]
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=header_row)
    filtered = df[
        (df['Area code'].isin(AREA_CODES)) &
        (df['Age group'] == '<1')
    ]
    print(f"[Sheet {sheet_name}] Filtered {len(df)} rows down to {len(filtered)} rows.")
    return meta, filtered

def write_output(meta: pd.DataFrame, filtered: pd.DataFrame, output_path):
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        meta.to_excel(writer, index=False, header=False, startrow=0)
        filtered.to_excel(writer, index=False, startrow=len(meta) + 1)
    print(f"Wrote filtered data to {output_path}")

def healthy_life_expectancy_LCR():
    download_file(DATA_URL, XLSX_FILE)
    for sheet_name, cfg in SHEET_CONFIG.items():
        meta, filtered_df = filter_data(XLSX_FILE, sheet_name, cfg['header_row'], cfg['meta_rows'])
        write_output(meta, filtered_df, cfg['output'])

if __name__ == '__main__':
    try:
        healthy_life_expectancy_LCR()
    except Exception:
        error_details = traceback.format_exc()
        print(error_details)  
        try:
            send_error_email(
                subject="healthy_life_expectancy_LCR script failed",
                body=f"The script failed:\n\n{error_details}"
            )
        except Exception as email_err:
            print(f"Failed to send error email: {email_err}")
        raise