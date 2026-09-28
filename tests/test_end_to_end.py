"""End-to-end tests: serve a known workbook over HTTP, run the whole process on it."""

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pandas as pd
import pytest
import requests

import healthy_life_expectancy_lcr as lcr

KEPT_CODES = ("E08000011", "E06000006")


class QuietHandler(SimpleHTTPRequestHandler):
    """Serve files without printing a line to the console for every request."""

    def log_message(self, *args):
        pass


@pytest.fixture
def served_url(sample_workbook, monkeypatch):
    """Serve the sample workbook from a local web server and return its URL."""
    handler = partial(QuietHandler, directory=str(sample_workbook.parent))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # Stop a proxy configured on the machine from intercepting localhost requests
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    try:
        port = server.server_address[1]
        yield f"http://127.0.0.1:{port}/{sample_workbook.name}"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture
def output_dir(tmp_path):
    """An output folder that does not exist yet, so the script has to create it."""
    return tmp_path / "output" / "nested"


@pytest.fixture
def run_process(served_url, output_dir):
    """Run the whole process against the local server and return the output folder."""
    settings = lcr.Settings(
        data_url=served_url, area_codes=KEPT_CODES, output_dir=output_dir
    )
    lcr.healthy_life_expectancy_lcr(settings)
    return output_dir


def test_download_file_saves_the_served_bytes(served_url, sample_workbook, tmp_path):
    saved = tmp_path / "downloaded.xlsx"

    lcr.download_file(served_url, saved)

    assert saved.read_bytes() == sample_workbook.read_bytes()


def test_download_file_raises_when_the_file_is_not_found(served_url, tmp_path):
    missing_url = served_url.rsplit("/", 1)[0] + "/missing.xlsx"

    with pytest.raises(requests.HTTPError):
        lcr.download_file(missing_url, tmp_path / "never_written.xlsx")


def test_every_expected_file_is_written(run_process):
    expected = {lcr.SOURCE_FILENAME, lcr.PIVOT_OUTPUT}
    expected |= set(lcr.PASSTHROUGH_SHEETS.values())
    expected |= {cfg["output"] for cfg in lcr.FILTER_SHEET_CONFIG.values()}

    written = {path.name for path in Path(run_process).iterdir()}

    assert expected <= written


@pytest.mark.parametrize("sheet_name", ["1", "3"])
def test_filtered_sheets_only_contain_the_requested_areas(run_process, sheet_name):
    cfg = lcr.FILTER_SHEET_CONFIG[sheet_name]
    header = len(cfg["meta_rows"]) + 1  # meta rows, a blank row, then the header

    table = pd.read_excel(run_process / cfg["output"], header=header)

    assert set(table["Area code"]) == set(KEPT_CODES)


def test_sheet_one_output_has_the_right_number_of_rows(run_process):
    cfg = lcr.FILTER_SHEET_CONFIG["1"]

    table = pd.read_excel(run_process / cfg["output"], header=len(cfg["meta_rows"]) + 1)

    assert len(table) == 16  # 2 areas x 2 periods x 2 sexes x 2 age groups


def test_pivot_output_keeps_the_meta_rows_and_only_the_requested_areas(run_process):
    output = run_process / lcr.PIVOT_OUTPUT

    raw = pd.read_excel(output, header=None)
    table = pd.read_excel(output, header=len(lcr.PIVOT_META_ROWS) + 1)

    assert raw[0].iloc[:4].tolist() == [
        "sheet2 line 0",
        "sheet2 line 4",
        "sheet2 line 5",
        "sheet2 line 6",
    ]
    assert set(table["Area code"]) == set(KEPT_CODES)
    assert len(table) == 8  # 2 areas x 2 sexes x 2 age groups


def test_passthrough_sheets_are_copied_unchanged(run_process):
    copied = pd.read_excel(run_process / "HLE_Notes.xlsx", header=None)

    assert copied[0].tolist() == [f"notes line {i}" for i in range(6)]
