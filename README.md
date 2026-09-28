# HealthyLifeExpectancyLCR
 
This project downloads, filters, and republishes Healthy Life Expectancy (HLE) data
for the Liverpool City Region (LCR) local authorities, sourced from the Office for
National Statistics (ONS).
 
The data shows the number of years people are expected to spend in "good" general
health in these areas, as well as the average in England and Wales.
 
## What it produces
 
| Output file | Source sheet | Notes |
|---|---|---|
| `CoverSheet.xlsx` | `Cover_sheet` | Copied as-is |
| `Contents.xlsx` | `Contents` | Copied as-is |
| `Notes.xlsx` | `Notes` | Copied as-is |
| `HealthyLifeExpectancyLCR.xlsx` | `1` | Healthy life expectancy, filtered by area code |
| `ChangeInHealthyLifeExpectancyLCR.xlsx` | `3` | Change in healthy life expectancy (England and Wales only), filtered by area code |
| `HealthyLifeExpectancyPivotLCR.xlsx` | `2` | Rebuilt from the filtered sheet 1 data (see below) |
 
Sheet 2 in the ONS workbook is an Excel PivotTable built from the same table as
sheet 1. Python can't create or edit PivotTable objects, so the script rebuilds the
same layout from the filtered sheet 1 data as a **regular table** (not an
interactive pivot).
 
Filtering keeps the Liverpool City Region local authorities (Liverpool, Knowsley,
Sefton, St Helens, Wirral, Halton), plus England and Wales for comparison. See the
`AREA_CODES` setting below to change which areas are kept.
 
## Data
 
See [DATA_LICENSE.md](DATA_LICENSE.md) for source and licensing information.
 
## Setup
 
This project uses [uv](https://docs.astral.sh/uv/) for dependency management.
 
1. Install uv: `python -m pip install uv` (or see uv's own install instructions).
2. Install dependencies:
```
   uv sync
```
 
3. Create your settings file (see below).
## Settings (`.env`)
 
Settings that can change between environments live in a file called `.env` in the
same folder as the script. Copy the template and edit it:
 
```
copy .env.template .env        (Windows)
cp .env.template .env          (macOS / Linux)
```
 
| Variable | Required | What to put |
|---|---|---|
| `DATA_URL` | Yes | The ONS download link for the workbook. Update it if ONS moves the file. |
| `AREA_CODES` | Yes | The ONS area codes to keep, separated by commas, e.g. `E08000011,E06000006`. |
| `OUTPUT_DIR` | No | Folder for the downloaded workbook and the output files. Defaults to the folder you run the script from. Created if it doesn't exist. |
 
If a required setting is missing, the script stops straight away with a message
naming it. Values already set in the environment take priority over the `.env` file.
 
`.env` should be listed in `.gitignore`. Commit `.env.template`, not `.env`.
 
## Other settings
 
These describe the layout of the ONS workbook rather than the environment, so they
stay as constants at the top of `healthy_life_expectancy_lcr.py`. Change them only
if ONS changes the workbook:
 
- `PASSTHROUGH_SHEETS`, `FILTER_SHEET_CONFIG`, `PIVOT_*`: which sheets are copied,
  filtered or rebuilt, which rows hold the header and meta data, and the output
  filenames.
## Running
 
```
uv run healthy_life_expectancy_lcr.py
```
 
Output files are written to `OUTPUT_DIR`. Progress is logged to the console with
timestamps. If any step fails, the traceback is logged and the script exits with an
error.
 
If ONS renames a sheet or column, the script stops with an error from pandas
naming the missing sheet or column.
 
## Running the tests
 
The tests need no `.env` file and no internet connection. The end-to-end tests serve
a small generated workbook from a local web server and run the whole process
against it.
 
```
uv run pytest
```
 
| File | What it covers |
|---|---|
| `tests/test_processing.py` | The individual functions: filtering, meta data rows, writing output, and the pivot layout (including that a missing value stays blank) |
| `tests/test_settings.py` | Loading settings from a `.env` file and the environment |
| `tests/test_end_to_end.py` | The whole process, from download to output files |
| `tests/conftest.py` | The small sample workbook the tests share |
 
To run only the quick unit tests: `uv run pytest tests/test_processing.py`.
 
## Linting
 
```
uv run ruff check .
uv run ruff format .
```