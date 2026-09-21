from pyspark_jobs.gold_transforms._shared import build_measure_vs_staffing

# S_038_02 -- pressure ulcers/injuries, new or worsened. ADJ_RATE is this
# family's name for the risk-adjusted headline rate (equivalent role to
# RSRR/RS_RATE in the other families). No COMP_PERF column in this family.
FACILITY_MEASURE_MAP = {
    "S_038_02_NUMERATOR": "pressure_ulcer_numerator",
    "S_038_02_DENOMINATOR": "pressure_ulcer_denominator",
    "S_038_02_OBS_RATE": "pressure_ulcer_obs_rate",
    "S_038_02_ADJ_RATE": "pressure_ulcer_adj_rate",
}

FACILITY_NUMERIC_COLUMNS = list(FACILITY_MEASURE_MAP.values())

NATIONAL_MEASURE_MAP = {
    "S_038_02_NATL_OBS_RATE": "pressure_ulcer_national_obs_rate",
}


def transform(spark, silver_frames: dict, gold_frames: dict):
    return build_measure_vs_staffing(
        spark, silver_frames, gold_frames,
        facility_measure_map=FACILITY_MEASURE_MAP,
        national_measure_map=NATIONAL_MEASURE_MAP,
        facility_numeric_columns=FACILITY_NUMERIC_COLUMNS,
    )
