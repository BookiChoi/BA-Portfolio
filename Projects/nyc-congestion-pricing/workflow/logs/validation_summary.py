import pandas as pd
from pathlib import Path
pd.set_option("display.width", 250)
d = pd.read_csv(Path(__file__).resolve().parent / "validation_checks.csv")
x = d[(d.group == "Q4") & (d.number.str.contains("CI") & (d.number.str.contains("Delta") | d.number.str.contains("margin")))]
print(x[["number", "analyst", "validator"]].round(3).to_string())
x = d[(d.group == "Q1") & d.number.str.contains("top5 CI")]
print(x[["number", "analyst", "validator"]].round(4).to_string())
