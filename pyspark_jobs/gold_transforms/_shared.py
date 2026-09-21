from pyspark.sql import functions as F

from pyspark_jobs.gold_transforms.facility_staffing_by_quarter import STAFFING_METRIC_COLUMNS


def pivot_measures(df, measure_map: dict, group_cols: list[str]):
    # Explicit pivot values (not auto-discovered) guarantee every mapped
    # column exists in the output even if a given run's data is missing some
    # measure_code entirely -- null in that case, not a missing column.
    measure_codes = list(measure_map.keys())
    df_pivoted = (
        df.filter(F.col("measure_code").isin(measure_codes))
        .groupBy(*group_cols)
        .pivot("measure_code", measure_codes)
        .agg(F.first("score"))
    )

    for original, renamed in measure_map.items():
        df_pivoted = df_pivoted.withColumnRenamed(original, renamed)

    return df_pivoted


def _assert_quarter_aligned_windows(df_keys) -> None:
    # The staffing-quarter join below generates the quarter list spanned by
    # [start_date, end_date] by stepping 3 calendar months at a time from
    # start_date. That's only correct if start_date/end_date actually fall
    # on calendar-quarter boundaries (true for every window seen so far --
    # verified empirically across all measure families currently in silver).
    # Fail loudly rather than silently mislabel quarters if a future data
    # release ever breaks that assumption.
    parsed = (
        df_keys
        .select("start_date", "end_date")
        .distinct()
        .withColumn("_start", F.to_date(F.col("start_date"), "MM/dd/yyyy"))
        .withColumn("_end", F.to_date(F.col("end_date"), "MM/dd/yyyy"))
        .withColumn("_expected_start", F.date_trunc("quarter", F.col("_start")).cast("date"))
        .withColumn("_expected_end", F.last_day(F.add_months(F.date_trunc("quarter", F.col("_end")), 2)))
    )

    bad_rows = (
        parsed
        .filter((F.col("_start") != F.col("_expected_start")) | (F.col("_end") != F.col("_expected_end")))
        .select("start_date", "end_date")
        .collect()
    )

    if bad_rows:
        raise ValueError(
            "Non-quarter-aligned measure window(s) found -- the staffing join assumes "
            f"start_date/end_date fall on calendar-quarter boundaries: {[r.asDict() for r in bad_rows]}"
        )


def _join_windowed_staffing(df_outcomes, df_staffing_by_quarter):
    df_keys = df_outcomes.select("ccn", "measurement_period", "start_date", "end_date").distinct()
    _assert_quarter_aligned_windows(df_keys)

    df_exploded = (
        df_keys
        .withColumn(
            "_window_quarter_date",
            F.explode(F.sequence(
                F.to_date(F.col("start_date"), "MM/dd/yyyy"),
                F.to_date(F.col("end_date"), "MM/dd/yyyy"),
                F.expr("interval 3 month"),
            ))
        )
        .withColumn(
            "_window_quarter",
            F.concat(F.year("_window_quarter_date"), F.lit("Q"), F.quarter("_window_quarter_date"))
        )
    )

    df_joined = df_exploded.join(
        df_staffing_by_quarter,
        (df_exploded["ccn"] == df_staffing_by_quarter["provnum"]) &
        (df_exploded["_window_quarter"] == df_staffing_by_quarter["measurement_period"]),
        how="left",
    )

    agg_exprs = [F.avg(F.col(c)).alias(c) for c in STAFFING_METRIC_COLUMNS]
    # Transparency, not a silent partial average: how many of the quarters
    # this measure's window actually spans had staffing data available vs.
    # how many the window expects. A left join means a facility missing
    # staffing for some quarters in its window still gets an average over
    # whatever quarters it does have -- these two counts make that visible
    # instead of hiding it behind a single number.
    agg_exprs.append(F.count(df_staffing_by_quarter["provnum"]).alias("staffing_quarters_matched"))
    agg_exprs.append(F.count(F.lit(1)).alias("staffing_quarters_expected"))

    return (
        df_joined
        .groupBy(df_exploded["ccn"], df_exploded["measurement_period"], df_exploded["start_date"], df_exploded["end_date"])
        .agg(*agg_exprs)
    )


def build_measure_vs_staffing(spark,
                              silver_frames: dict,
                              gold_frames: dict,
                              facility_measure_map: dict,
                              national_measure_map: dict,
                              facility_numeric_columns: list[str]):
    df_facility_quality = silver_frames["provider_quality_reporting"]
    df_national_quality = silver_frames["national_provider_quality_reporting_averages"]
    df_national_staffing = silver_frames["national_provider_averages"]
    df_staffing_by_quarter = gold_frames["facility_staffing_by_quarter"]

    # start_date/end_date ride along in the pivot's group_cols (not just
    # ccn+measurement_period) so the true window drives the staffing join
    # below, rather than assuming every facility shares one window per
    # measurement_period. state rides along too -- 
    df_facility_wide = pivot_measures(
        df_facility_quality, facility_measure_map,
        group_cols=["ccn", "state", "measurement_period", "start_date", "end_date"],
    )
    for col_name in facility_numeric_columns:
        # try_cast, not cast: real CMS data uses text like "Not Available" for
        # suppressed/uncomputed values even in columns that are otherwise
        # numeric. A hard cast fails the whole job on the first one; try_cast
        # nulls it out and keeps going, and is using a sqlexpression 
        # because there is no true trycast in pyspark's DataFrame API. 
        # The nulls are handled downstream in the transform logic.
        df_facility_wide = df_facility_wide.withColumn(col_name, F.expr(f"try_cast({col_name} AS DOUBLE)"))

    df_national_wide = pivot_measures(
        df_national_quality, national_measure_map, group_cols=["measurement_period"],
    )
    for col_name in national_measure_map.values():
        df_national_wide = df_national_wide.withColumn(col_name, F.expr(f"try_cast({col_name} AS DOUBLE)"))

    df_outcomes = df_facility_wide.join(
        F.broadcast(df_national_wide), on="measurement_period", how="left"
    )

    df_windowed_staffing = _join_windowed_staffing(df_outcomes, df_staffing_by_quarter)

    df_result = df_outcomes.join(
        df_windowed_staffing, on=["ccn", "measurement_period", "start_date", "end_date"], how="left"
    )

    # National/state staffing baseline. national_provider_averages is not
    # period-partitioned in silver -- it's a plain current-state table -- so
    # this is always the latest known national snapshot, not period-matched
    # to each row the way the outcome baselines and windowed staffing are.
    df_national_staffing_row = df_national_staffing.filter(F.col("state") == "NATION").select(
        F.col("reported_rn_hours_per_resident_day").alias("national_rn_hours_per_resident_day"),
        F.col("reported_lpn_hours_per_resident_day").alias("national_lpn_hours_per_resident_day"),
        F.col("reported_total_nurse_hours_per_resident_day").alias("national_total_nurse_hours_per_resident_day"),
        F.col("total_nursing_staff_turnover").alias("national_total_nursing_staff_turnover"),
        F.col("rn_turnover").alias("national_rn_turnover"),
    )

    return df_result.crossJoin(F.broadcast(df_national_staffing_row))
