from pyspark_jobs.gold_transforms._shared import build_measure_vs_staffing

# S_004_01 -- potentially preventable readmissions. Hand-curated from CMS's
# measure definitions (not derivable from the strings alone). COMP_PERF is
# CMS's own pre-computed "Better/Worse/No Different Than National Rate"
# category and is deliberately NOT cast to numeric.
FACILITY_MEASURE_MAP = {
    "S_004_01_PPR_PD_OBS_READM": "readmission_number",
    "S_004_01_PPR_PD_VOLUME": "readmission_volume",
    "S_004_01_PPR_PD_OBS": "readmission_obs_rate",              # unadjusted -- pairs with the national unadjusted avg
    "S_004_01_PPR_PD_RSRR": "readmission_rsrr",                 # facility's own risk-standardized headline rate
    "S_004_01_PPR_PD_RSRR_2_5": "readmission_rsrr_lower_ci",
    "S_004_01_PPR_PD_RSRR_97_5": "readmission_rsrr_upper_ci",
    "S_004_01_PPR_PD_COMP_PERF": "readmission_comp_perf",
}

FACILITY_NUMERIC_COLUMNS = [
    v for k, v in FACILITY_MEASURE_MAP.items() if not k.endswith("_COMP_PERF")
]

NATIONAL_MEASURE_MAP = {
    "S_004_01_PPR_PD_NAT_UNADJUST_AVG": "readmission_national_unadjusted_avg",
}


def transform(spark, silver_frames: dict, gold_frames: dict):
    return build_measure_vs_staffing(
        spark, silver_frames, gold_frames,
        facility_measure_map=FACILITY_MEASURE_MAP,
        national_measure_map=NATIONAL_MEASURE_MAP,
        facility_numeric_columns=FACILITY_NUMERIC_COLUMNS,
    )
