from pyspark_jobs.gold_transforms._shared import build_measure_vs_staffing

# S_013_02 -- falls with major injury. No COMP_PERF column in this family.
FACILITY_MEASURE_MAP = {
    "S_013_02_OBS_RATE": "falls_obs_rate",
    "S_013_02_NUMERATOR": "falls_numerator",
    "S_013_02_DENOMINATOR": "falls_denominator",
}

FACILITY_NUMERIC_COLUMNS = list(FACILITY_MEASURE_MAP.values())

NATIONAL_MEASURE_MAP = {
    "S_013_02_NATL_OBS_RATE": "falls_national_obs_rate",
}


def transform(spark, silver_frames: dict, gold_frames: dict):
    return build_measure_vs_staffing(
        spark, silver_frames, gold_frames,
        facility_measure_map=FACILITY_MEASURE_MAP,
        national_measure_map=NATIONAL_MEASURE_MAP,
        facility_numeric_columns=FACILITY_NUMERIC_COLUMNS,
    )
