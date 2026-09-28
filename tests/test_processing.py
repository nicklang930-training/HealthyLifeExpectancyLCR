"""Unit tests for the individual functions: known input gives known output."""

import numpy as np
import pandas as pd
import pytest

import healthy_life_expectancy_lcr as lcr

KEPT_CODES = ("E08000011", "E06000006")
ROWS_PER_AREA = 8  # 2 periods x 2 sexes x 2 age groups in the sample workbook


@pytest.fixture
def xls(sample_workbook):
    """The sample workbook, opened the same way the script opens the real one."""
    with pd.ExcelFile(sample_workbook) as workbook:
        yield workbook


# --- read_meta ---------------------------------------------------------------


def test_read_meta_keeps_only_the_requested_rows(xls):
    meta = lcr.read_meta(xls, "1", [0, 3, 4])

    assert meta[0].tolist() == ["sheet1 line 0", "sheet1 line 3", "sheet1 line 4"]


# --- filter_data -------------------------------------------------------------


def test_filter_data_keeps_only_the_requested_area_codes(xls):
    _, filtered = lcr.filter_data(xls, "1", 6, [0, 3, 4], KEPT_CODES)

    assert set(filtered["Area code"]) == set(KEPT_CODES)
    assert len(filtered) == ROWS_PER_AREA * len(KEPT_CODES)


def test_filter_data_returns_the_meta_rows_as_well(xls):
    meta, _ = lcr.filter_data(xls, "1", 6, [0, 3, 4], KEPT_CODES)

    assert len(meta) == 3


def test_filter_data_returns_no_rows_when_nothing_matches(xls):
    _, filtered = lcr.filter_data(xls, "1", 6, [0, 3, 4], ("NOT_A_CODE",))

    assert filtered.empty


# --- write_output and copy_sheet ---------------------------------------------


def test_write_output_puts_meta_then_a_blank_row_then_the_table(tmp_path):
    meta = pd.DataFrame([["title"], ["note"]])
    table = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    output = tmp_path / "out.xlsx"

    lcr.write_output(meta, table, output)

    written = pd.read_excel(output, header=None)
    assert written.iloc[0, 0] == "title"
    assert written.iloc[1, 0] == "note"
    assert written.iloc[2].isna().all()  # the blank row
    assert written.iloc[3].tolist() == ["a", "b"]  # the table's header row
    assert written.iloc[4].tolist() == [1, 3]


def test_copy_sheet_copies_every_line_unchanged(xls, tmp_path):
    output = tmp_path / "notes.xlsx"

    lcr.copy_sheet(xls, "Notes", output)

    copied = pd.read_excel(output, header=None)
    assert copied[0].tolist() == [f"notes line {i}" for i in range(6)]


# --- build_pivot_summary -----------------------------------------------------


def make_table():
    """Two areas x two periods, one sex and age group, with values worked out by hand.

    Area E1 has an HLE of 60 then 61, and area E2 has 70 then 71. LCI is HLE - 2
    and UCI is HLE + 2.
    """
    rows = []
    for code, name, base in [("E1", "Areaone", 60.0), ("E2", "Areatwo", 70.0)]:
        for period, bump in [("2011 to 2013", 0.0), ("2022 to 2024", 1.0)]:
            hle = base + bump
            rows.append(
                {
                    "Area code": code,
                    "Area name": name,
                    "Sex": "Male",
                    "Age group": "<1",
                    "Period": period,
                    "HLE": hle,
                    "LCI": hle - 2,
                    "UCI": hle + 2,
                    "Proportion (%)": 72,
                }
            )
    return pd.DataFrame(rows)


def test_pivot_has_one_row_per_area_sex_and_age_group():
    pivot = lcr.build_pivot_summary(make_table())

    assert len(pivot) == 2
    assert pivot["Area code"].tolist() == ["E1", "E2"]


def test_pivot_columns_are_the_row_labels_then_period_and_metric():
    pivot = lcr.build_pivot_summary(make_table())

    assert list(pivot.columns[:4]) == ["Area code", "Area name", "Sex", "Age group"]
    expected = {
        f"{period} - {metric}"
        for period in ("2011 to 2013", "2022 to 2024")
        for metric in ("HLE", "LCI", "UCI", "Proportion (%)")
    }
    assert set(pivot.columns[4:]) == expected


def test_pivot_groups_the_columns_by_period():
    pivot = lcr.build_pivot_summary(make_table())

    value_columns = list(pivot.columns[4:])
    assert all(column.startswith("2011 to 2013") for column in value_columns[:4])
    assert all(column.startswith("2022 to 2024") for column in value_columns[4:])


def test_pivot_values_land_in_the_right_cells():
    pivot = lcr.build_pivot_summary(make_table()).set_index("Area code")

    assert pivot.loc["E1", "2011 to 2013 - HLE"] == 60.0
    assert pivot.loc["E1", "2022 to 2024 - UCI"] == 63.0
    assert pivot.loc["E2", "2011 to 2013 - LCI"] == 68.0
    assert pivot.loc["E2", "2022 to 2024 - HLE"] == 71.0


def test_pivot_keeps_a_missing_value_blank_instead_of_turning_it_into_zero():
    table = make_table()
    is_e1_2022 = (table["Area code"] == "E1") & (table["Period"] == "2022 to 2024")
    table.loc[is_e1_2022, "HLE"] = np.nan

    pivot = lcr.build_pivot_summary(table).set_index("Area code")

    assert pd.isna(pivot.loc["E1", "2022 to 2024 - HLE"])
    assert pivot.loc["E2", "2022 to 2024 - HLE"] == 71.0
