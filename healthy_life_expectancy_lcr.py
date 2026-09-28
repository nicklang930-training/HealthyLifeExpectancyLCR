"""Download the ONS healthy life expectancy workbook and export filtered extracts.

Sheets 1 and 3 are filtered by area code. Sheet 2 is a pivot table in the source
workbook, so it is rebuilt from the filtered sheet 1 data. The cover, contents and
notes sheets are copied through unchanged.

Settings that can change between environments (download URL, area codes and output
folder) are read from a .env file or the environment, see load_settings.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Where to download the source workbook from and what to save it as
SOURCE_FILENAME = "healthylifeexpectancyuk.xlsx"

# Sheets that just get copied through as-is, no filtering required
PASSTHROUGH_SHEETS = {
    "Cover_sheet": "HLE_Cover_sheet.xlsx",
    "Contents": "HLE_Contents.xlsx",
    "Notes": "HLE_Notes.xlsx",
}

# Setting the parameters for maintaining meta data on the sheets 1 and 3
FILTER_SHEET_CONFIG = {
    "1": {
        "header_row": 6,
        "meta_rows": [0, 3, 4],
        "output": "HealthyLifeExpectancyLCR.xlsx",
    },
    "3": {
        "header_row": 6,
        "meta_rows": [0, 3, 4],
        "output": "ChangeInHealthyLifeExpectancyLCR.xlsx",
    },
}

# Settings for rebuilding the pivot table on sheet 2 of the source data. The data
# comes from the filtered PIVOT_SOURCE_SHEET and the meta data rows are 
# read from PIVOT_SHEET itself.
PIVOT_SOURCE_SHEET = "1"
PIVOT_SHEET = "2"
PIVOT_META_ROWS = [0, 4, 5, 6]
PIVOT_OUTPUT = "HealthyLifeExpectancyPivotLCR.xlsx"
PIVOT_INDEX = ["Area code", "Area name", "Sex", "Age group"]
PIVOT_COLUMNS = "Period"
PIVOT_VALUES = ["HLE", "LCI", "UCI", "Proportion (%)"]

@dataclass(frozen=True)
class Settings:
    """Settings that can change between environments."""

    data_url: str
    area_codes: tuple[str, ...]
    output_dir: Path


def _require_env(name: str) -> str:
    """Return an environment variable's value, or fail"""
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(
            f"Missing required setting {name}. "
            "Copy .env.template to .env and update settings."
        )
    return value


def load_settings(env_path: Path | None = None) -> Settings:
    """Load settings from a .env file and the environment.

    Values already set in the environment take priority over the .env file.
    """
    load_dotenv(env_path or Path(__file__).parent / ".env")
    area_codes = tuple(
        code.strip() for code in _require_env("AREA_CODES").split(",") if code.strip()
    )
    return Settings(
        data_url=_require_env("DATA_URL"),
        area_codes=area_codes,
        output_dir=Path(os.environ.get("OUTPUT_DIR") or "."),
    )

def download_file(url, path):
    """Download the file at url and save it to path."""
    logger.info("Downloading source file...")
    response = requests.get(url)
    response.raise_for_status()
    with open(path, "wb") as f:
        f.write(response.content)
    logger.info("Saved to %s", path)


def read_meta(xls, sheet_name, meta_rows) -> pd.DataFrame:
    """Read the title/notes rows above the table, keeping only the selected meta_rows (0-indexed)."""
    metafull = pd.read_excel(
        xls, sheet_name=sheet_name, header=None, nrows=max(meta_rows) + 1
    )
    return metafull.iloc[meta_rows]


def filter_data(
    xls, sheet_name, header_row, meta_rows, area_codes
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return a sheet's meta data rows and its table filtered to area_codes."""
    meta = read_meta(xls, sheet_name, meta_rows)
    df = pd.read_excel(xls, sheet_name=sheet_name, header=header_row)
    filtered = df[df["Area code"].isin(area_codes)]
    logger.info(
        "[Sheet %s] Filtered %d rows down to %d rows.",
        sheet_name,
        len(df),
        len(filtered),
    )
    return meta, filtered


def write_output(meta: pd.DataFrame, table: pd.DataFrame, output_path):
    """Write the meta data rows, a blank row, then the table to a new xlsx file."""
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        meta.to_excel(writer, index=False, header=False, startrow=0)
        table.to_excel(writer, index=False, startrow=len(meta) + 1)
    logger.info("Wrote data to %s", output_path)


def copy_sheet(xls, sheet_name, output_path):
    """Copy a sheet to a new xlsx file unchanged."""
    df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, header=False)
    logger.info("[Sheet %s] Copied %d rows to %s", sheet_name, len(df), output_path)


def build_pivot_summary(filtered_sheet1: pd.DataFrame) -> pd.DataFrame:
    """Rebuild the sheet 2 pivot layout from the filtered sheet 1 data."""
    pivot = filtered_sheet1.pivot_table(
        index=PIVOT_INDEX,
        columns=PIVOT_COLUMNS,
        values=PIVOT_VALUES,
        aggfunc="first",
    )
    # Put the period on the outer level of the column headers and the metric on
    # the inner level, to match the layout of the pivot table in the source.
    pivot.columns = pivot.columns.swaplevel(0, 1)
    pivot = pivot.sort_index(axis=1, level=0)

    # Flatten the two level column headers into one, like "2011 to 2013 - HLE"
    pivot.columns = [f"{period} - {metric}" for period, metric in pivot.columns]
    pivot = pivot.reset_index()
    return pivot


def healthy_life_expectancy_lcr(settings: Settings):
    """Run the full download, filter and export process."""
    output_dir = settings.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    source_path = output_dir / SOURCE_FILENAME
    download_file(settings.data_url, source_path)

    # Open the workbook for every sheet read
    with pd.ExcelFile(source_path) as xls:
        for sheet_name, filename in PASSTHROUGH_SHEETS.items():
            copy_sheet(xls, sheet_name, output_dir / filename)

        filtered_by_sheet = {}
        for sheet_name, cfg in FILTER_SHEET_CONFIG.items():
            meta, filtered_df = filter_data(
                xls,
                sheet_name,
                cfg["header_row"],
                cfg["meta_rows"],
                settings.area_codes,
            )
            write_output(meta, filtered_df, output_dir / cfg["output"])
            filtered_by_sheet[sheet_name] = filtered_df

        pivot_meta = read_meta(xls, PIVOT_SHEET, PIVOT_META_ROWS)

    pivot_summary = build_pivot_summary(filtered_by_sheet[PIVOT_SOURCE_SHEET])
    write_output(pivot_meta, pivot_summary, output_dir / PIVOT_OUTPUT)



if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        healthy_life_expectancy_lcr(load_settings())
        logger.info("healthy_life_expectancy_lcr completed successfully")
    except Exception:
        logger.exception("healthy_life_expectancy_lcr failed")
        raise