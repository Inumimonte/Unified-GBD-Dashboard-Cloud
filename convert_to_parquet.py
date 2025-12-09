import pandas as pd
from pathlib import Path

data_dir = Path("data")

files = [
    "Unified_GBD_Fact_Table_CLEAN.csv",
    "Unified_GBD_Fact_Table_RAW.csv",
]

for fname in files:
    csv_path = data_dir / fname
    parquet_path = data_dir / fname.replace(".csv", ".parquet")
    print(f"Converting {csv_path} -> {parquet_path}")
    df = pd.read_csv(csv_path)
    df.to_parquet(parquet_path, index=False)
    print("Done.")
