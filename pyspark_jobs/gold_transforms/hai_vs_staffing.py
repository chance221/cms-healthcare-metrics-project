from pyspark_jobs.gold_transforms._shared import build_measure_vs_staffing

# S_039_01 -- healthcare-associated infections.
FACILITY_MEASURE_MAP = {
    "S_039_01_HAI_NUMBER": "hai_number",
    "S_039_01_HAI_VOLUME": "hai_volume",
    "S_039_01_HAI_OBS_RATE": "hai_obs_rate",
    "S_039_01_HAI_RS_RATE": "hai_rs_rate",
    "S_039_01_HAI_RS_RATE_2_5": "hai_rs_rate_lower_ci",
    "S_039_01_HAI_RS_RATE_97_5": "hai_rs_rate_upper_ci",
    "S_039_01_HAI_COMP_PERF": "hai_comp_perf",
}

FACILITY_NUMERIC_COLUMNS = [
    v for k, v in FACILITY_MEASURE_MAP.items() if not k.endswith("_COMP_PERF")
]

# HAI's national file also carries the same "N Better/No Different/Worse/Too
# Small" distribution CMS shows for COMP_PERF, but as national aggregate
# counts rather than a per-facility category.
NATIONAL_MEASURE_MAP = {
    "S_039_01_HAI_NAT_OBS_RATE": "hai_national_obs_rate",
    "S_039_01_HAI_N_BETTER_NAT": "hai_national_n_better",
    "S_039_01_HAI_N_NO_DIFF_NAT": "hai_national_n_no_diff",
    "S_039_01_HAI_N_WORSE_NAT": "hai_national_n_worse",
    "S_039_01_HAI_N_TOO_SMALL": "hai_national_n_too_small",
}


def transform(spark, silver_frames: dict, gold_frames: dict):
    return build_measure_vs_staffing(
        spark, silver_frames, gold_frames,
        facility_measure_map=FACILITY_MEASURE_MAP,
        national_measure_map=NATIONAL_MEASURE_MAP,
        facility_numeric_columns=FACILITY_NUMERIC_COLUMNS,
    )
