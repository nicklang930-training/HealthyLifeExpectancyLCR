"""Tests for loading settings from a .env file and the environment."""

from pathlib import Path

import pytest

import healthy_life_expectancy_lcr as lcr

SETTING_NAMES = ("DATA_URL", "AREA_CODES", "OUTPUT_DIR")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Start every test with none of the settings in the environment.

    load_dotenv writes straight into os.environ, so registering each variable with
    monkeypatch first makes sure it is put back the way it was after the test.
    """
    for name in SETTING_NAMES:
        monkeypatch.setenv(name, "placeholder")
        monkeypatch.delenv(name)


def write_env_file(tmp_path, text):
    """Write text to a .env style file and return its path."""
    path = tmp_path / "test.env"
    path.write_text(text)
    return path


def test_reads_all_values_from_env_file(tmp_path):
    env_file = write_env_file(
        tmp_path,
        "DATA_URL=http://example.test/file.xlsx\n"
        "AREA_CODES=E08000011,E06000006\n"
        "OUTPUT_DIR=results\n",
    )

    settings = lcr.load_settings(env_file)

    assert settings.data_url == "http://example.test/file.xlsx"
    assert settings.area_codes == ("E08000011", "E06000006")
    assert settings.output_dir == Path("results")


def test_area_codes_ignore_spaces_and_empty_entries(tmp_path):
    env_file = write_env_file(
        tmp_path, "DATA_URL=http://x/f.xlsx\nAREA_CODES= E1 , E2 ,,\n"
    )

    settings = lcr.load_settings(env_file)

    assert settings.area_codes == ("E1", "E2")


def test_output_dir_defaults_to_current_folder(tmp_path):
    env_file = write_env_file(tmp_path, "DATA_URL=http://x/f.xlsx\nAREA_CODES=E1\n")

    settings = lcr.load_settings(env_file)

    assert settings.output_dir == Path(".")


@pytest.mark.parametrize(
    ("contents", "missing_name"),
    [
        ("DATA_URL=http://x/f.xlsx\n", "AREA_CODES"),
        ("AREA_CODES=E1\n", "DATA_URL"),
    ],
)
def test_missing_required_setting_raises_and_names_it(tmp_path, contents, missing_name):
    env_file = write_env_file(tmp_path, contents)

    with pytest.raises(ValueError, match=missing_name):
        lcr.load_settings(env_file)


def test_environment_takes_priority_over_env_file(tmp_path, monkeypatch):
    env_file = write_env_file(
        tmp_path, "DATA_URL=http://from-file/f.xlsx\nAREA_CODES=E1\n"
    )
    monkeypatch.setenv("DATA_URL", "http://from-environment/f.xlsx")

    settings = lcr.load_settings(env_file)

    assert settings.data_url == "http://from-environment/f.xlsx"
