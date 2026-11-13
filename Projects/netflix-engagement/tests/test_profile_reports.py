"""Unit tests for pipeline/profile_reports.py using tiny synthetic workbooks."""

import sys
from datetime import datetime
from pathlib import Path

import openpyxl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline import profile_reports as pr  # noqa: E402

HEADER = ["Title", "Available Globally?", "Release Date", "Hours Viewed", "Runtime", "Views"]


def make_workbook(path, sheets):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, rows in sheets.items():
        ws = wb.create_sheet(name)
        ws.append([None] * 7)
        ws.append([None, "What We Watched: A Netflix Engagement Report"])
        ws.append([None, "Views from January to June 2025"])
        ws.append([])
        ws.append([])
        ws.append([None] + HEADER)
        for r in rows:
            ws.append([None] + r)
    wb.save(path)
    return path


@pytest.fixture
def sample(tmp_path):
    rows = [
        ["Show A: Season 1", "Yes", "2025-01-02", 500, "2:00", 50],
        ["Show B: Limited Series", "No", None, 300, "1:30", 40],
        ["Available Globally?", "Yes", "2025-02-01", 100, "0:30", 10],  # header phrase in data
        ["Other Shows", "*", "*", 100, "*", "*"],
        [],
        ["*Footnote text."],
    ]
    return make_workbook(tmp_path / "t.xlsx", {"Shows": rows, "Movies": [["Film X", "Yes", datetime(2025, 3, 1), 200, "1:45", 99]]})


def test_find_header_row_skips_logo_and_meta_rows(sample):
    rows = pr.read_rows(sample, "Shows")
    assert pr.find_header_row(rows) == 5


def test_load_sheet_separates_footnotes_and_blanks(sample):
    loaded = pr.load_sheet(sample, "Shows")
    assert loaded["header_row_excel"] == 6
    assert len(loaded["footnotes"]) == 1
    assert loaded["rows_blank"] == 1
    assert len(loaded["df"]) == 4
    assert len(loaded["skipped_above"]) == 2


def test_profile_counts_other_and_header_phrase_rows(sample):
    prof, _, _ = pr.profile_file(sample)
    shows = next(s for s in prof["per_sheet"] if s["sheet"] == "Shows")
    assert shows["rows_data"] == 4
    assert shows["rows_other"] == 1
    assert shows["rows_with_header_phrase"] == 1
    assert shows["columns"]["title"]["header_phrase_rows"] == 1
    assert shows["release_date"]["missing"] == 1
    assert prof["content_type_split_source"] == "sheet name"
    assert prof["file_total"]["rows_by_content_type"] == {"series": 4, "film": 1}


def test_top10_share_and_totals(sample):
    prof, _, _ = pr.profile_file(sample)
    h = prof["file_total"]["hours"]
    assert h["total_incl_other"] == 1200
    assert h["total_title_level"] == 1100
    assert h["top10_share_of_total_incl_other"] == pytest.approx(1100 / 1200)
    assert h["top10_share_of_title_level"] == pytest.approx(1.0)


def test_runtime_and_date_parsing():
    assert pr.parse_runtime("7:34") == 454
    assert pr.parse_runtime("*") != pr.parse_runtime("*")  # NaN
    assert pr.parse_date(datetime(2023, 3, 23)) == pr.parse_date("2023-03-23")
    assert str(pr.parse_date("*")) == "NaT"


def test_normalisation_keys():
    assert pr.norm1("Love, Death & Robots") == pr.norm1("love death robots")
    assert pr.norm2("Squid Game: Season 2 // 오징어 게임: 시즌 2") == pr.norm1("Squid Game: Season 2")


def test_split_notation_and_classification():
    assert pr.split_notation("Bridgerton: Season 3") == ("Bridgerton", "Season 3")
    assert pr.split_notation("Stranger Things 5") == ("Stranger Things", "5")
    assert pr.classify_notation("Season 3", "Bridgerton: Season 3") == "Season N"
    assert pr.classify_notation("5", "Stranger Things 5") == "trailing number"
    assert pr.classify_notation("", "Damsel") == "none"
