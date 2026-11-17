"""Constants fixed by the approved plan (workflow/04_analysis_plan.md).

Every value here is a plan decision, not a tuning knob. Changing one changes the
meaning of a result, so edit only after the human changes the plan.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
CACHE = OUT / "cache"      # per-file aggregates; small and regenerable, so not for commit
LOGS = OUT / "logs"
SEED = 42                  # plan section 0: seed 42 for every bootstrap
B = 2000                   # plan section 0: 2000 replicates
ALPHA = 0.05

SERVICES = ("yellow", "fhvhv")
PICKUP_COL = {"yellow": "tpep_pickup_datetime", "fhvhv": "pickup_datetime"}
DROPOFF_COL = {"yellow": "tpep_dropoff_datetime", "fhvhv": "dropoff_datetime"}

# Q1-Q3: Oct 2025 - Sep 2026 ; Q4: Jan-Sep of 2023, 2024, 2026
Q123_MONTHS = [(2025, 10), (2025, 11), (2025, 12)] + [(2026, m) for m in range(1, 10)]
Q4_MONTHS = [(y, m) for y in (2023, 2024, 2026) for m in range(1, 10)]
ALL_MONTHS = sorted(set(Q123_MONTHS) | set(Q4_MONTHS))   # 30 per service

AIRPORTS = {1: "Newark Airport", 132: "JFK Airport", 138: "LaGuardia Airport"}
DAYPARTS = {"overnight": range(0, 6), "morning": range(6, 10), "midday": range(10, 16),
            "evening": range(16, 20), "night": range(20, 24)}
# Q3 night = hours 22-04 (human decision 2 at gate 2); S2 adds hour 5
NIGHT_HOURS = (22, 23, 0, 1, 2, 3, 4)
NIGHT_HOURS_S2 = (22, 23, 0, 1, 2, 3, 4, 5)

CRZ_FILE = DATA / "MTA_Central_Business_District_Taxi_Zones_20261113.csv"
LOOKUP_FILE = DATA / "taxi_zone_lookup.csv"
SHAPEFILE = DATA / "taxi_zones.shp"
DOWNLOAD_DATE = "2026-11-13"   # value given by the human in 03_data_plan.md
BASE_URL = "https://d37ci6vzurychx.cloudfront.net"


def parquet_path(service: str, ym: tuple) -> Path:
    return DATA / f"{service}_tripdata_{ym[0]}-{ym[1]:02d}.parquet"
