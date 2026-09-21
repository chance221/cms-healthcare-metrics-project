from pyspark_jobs.gold_transforms._shared import build_measure_vs_staffing

# S_005_02 -- discharge to community.
FACILITY_MEASURE_MAP = {
    "S_005_02_DTC_NUMBER": "dtc_number",
    "S_005_02_DTC_VOLUME": "dtc_volume",
    "S_005_02_DTC_OBS_RATE": "dtc_obs_rate",                    # pairs with national observed rate
    "S_005_02_DTC_RS_RATE": "dtc_rs_rate",
    "S_005_02_DTC_RS_RATE_2_5": "dtc_rs_rate_lower_ci",
    "S_005_02_DTC_RS_RATE_97_5": "dtc_rs_rate_upper_ci",
    "S_005_02_DTC_COMP_PERF": "dtc_comp_perf",
}

FACILITY_NUMERIC_COLUMNS = [
    v for k, v in FACILITY_MEASURE_MAP.items() if not k.endswith("_COMP_PERF")
]

NATIONAL_MEASURE_MAP = {
    "S_005_02_DTC_NAT_OBS_RATE": "dtc_national_obs_rate",
}


def transform(spark, silver_frames: dict, gold_frames: dict):
    return build_measure_vs_staffing(
        spark, silver_frames, gold_frames,
        facility_measure_map=FACILITY_MEASURE_MAP,
        national_measure_map=NATIONAL_MEASURE_MAP,
        facility_numeric_columns=FACILITY_NUMERIC_COLUMNS,
    )
