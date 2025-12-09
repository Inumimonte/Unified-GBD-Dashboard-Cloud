import os
import pandas as pd


DATA_DIR = "data"

RAW_FILES = [
    "DALYs_Rate.csv",
    "Death_rate.csv",
    "Incidence_rate.csv",
    "Prevelance_rate.csv",
    "YLLs_rate.csv",
    "Injuries_Rate.csv",
    "NCD_Rate.csv",
    "Maternal Disorder.csv",
    "Neonatal Disorder.csv",
]

RAW_OUT = "Unified_GBD_Fact_Table_RAW.csv"
CLEAN_OUT = "Unified_GBD_Fact_Table_CLEAN.csv"


def standardize_measure_name(raw_name: str) -> str:
    """Turn the original measure_name into a short, consistent label."""
    s = str(raw_name).lower()

    # Order matters: check the more specific ones first
    if "dalys" in s:
        return "DALYs Rate"
    if "yll" in s:
        return "YLLs Rate"
    if "death" in s:
        return "Death Rate"
    if "incidence" in s:
        return "Incidence Rate"
    if "prevalence" in s:
        return "Prevalence Rate"
    if "injur" in s:
        return "Injury Rate"

    # Fallback: just return the original text
    return str(raw_name)


def map_measure_from_filename(filename: str) -> str:
    """Fallback mapping if a file has no measure_name column."""
    name = filename.lower()
    if "daly" in name:
        return "DALYs Rate"
    if "death" in name:
        return "Death Rate"
    if "incidence" in name:
        return "Incidence Rate"
    if "prevelance" in name or "prevalence" in name:
        return "Prevalence Rate"
    if "yll" in name:
        return "YLLs Rate"
    if "injur" in name:
        return "Injury Rate"

    # For NCD_Rate or anything else we couldn't detect
    return "NCD Rate"


def merge_raw_files() -> pd.DataFrame:
    """Load all CSVs, add measure_name_standard, and merge into one DF."""
    frames = []

    for fname in RAW_FILES:
        file_path = os.path.join(DATA_DIR, fname)
        print(f"Loading {file_path} ...")
        df = pd.read_csv(file_path)

        # Track source (useful for debugging later)
        df["source_file"] = fname

        # Ensure we have a measure_name_standard column
        if "measure_name_standard" not in df.columns:
            if "measure_name" in df.columns:
                # Use the actual measure_name text (works for NCD_Rate.csv too)
                df["measure_name_standard"] = df["measure_name"].apply(
                    standardize_measure_name
                )
            else:
                # Last resort: infer from the filename
                df["measure_name_standard"] = map_measure_from_filename(fname)

        frames.append(df)

    merged = pd.concat(frames, ignore_index=True)
    print(f"Merged shape: {merged.shape}")

    # Save raw merged version
    raw_out_path = os.path.join(DATA_DIR, RAW_OUT)
    merged.to_csv(raw_out_path, index=False)
    print(f"Saved RAW merged table to {raw_out_path}")

    return merged


def clean_merged_df(df: pd.DataFrame) -> pd.DataFrame:
    """Drop ID columns and keep the main analytical fields."""
    cols_to_drop = ["measure_id", "location_id", "sex_id", "cause_id", "metric_id"]

    # Only drop columns that actually exist
    cols_to_drop = [c for c in cols_to_drop if c in df.columns]
    df = df.drop(columns=cols_to_drop)

    # Preferred column order (won't break if some are missing)
    preferred = [
        "measure_name_standard",
        "measure_name",
        "location_name",
        "sex_name",
        "age_name",
        "cause_name",
        "metric_name",
        "year",
        "val",
        "upper",
        "lower",
        "age_id",
        "source_file",
    ]

    final_cols = [c for c in preferred if c in df.columns] + [
        c for c in df.columns if c not in preferred
    ]

    return df[final_cols]


def main():
    merged = merge_raw_files()
    cleaned = clean_merged_df(merged)

    clean_out_path = os.path.join(DATA_DIR, CLEAN_OUT)
    cleaned.to_csv(clean_out_path, index=False)
    print(f"Saved CLEAN fact table to {clean_out_path}")


if __name__ == "__main__":
    main()
