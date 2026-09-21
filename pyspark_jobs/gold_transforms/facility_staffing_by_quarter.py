from pyspark.sql import functions as F

# One row per (provnum, measurement_period). measurement_period here is
# derived from work_date, not carried from silver -- provider_nurse_staffing
# is a plain current-state silver table (no partition_source_column), so
# this quarter derivation is interpretive gold-layer logic, same as the
# raw yyyyMMdd work_date parsing itself.

STAFFING_METRIC_COLUMNS = [
    "avg_daily_rn_hours",
    "avg_weekday_rn_hours",
    "avg_weekend_rn_hours",
    "avg_weekday_rn_staff_hours",
    "avg_weekend_rn_staff_hours",
    "avg_weekday_rn_admin_hours",
    "avg_weekend_rn_admin_hours",
    "avg_weekday_rn_director_of_nursing_hours",
    "avg_weekend_rn_director_of_nursing_hours",

    "avg_daily_lpn_hours",
    "avg_weekday_lpn_hours",
    "avg_weekend_lpn_hours",
    "avg_weekday_lpn_staff_hours",
    "avg_weekend_lpn_staff_hours",
    "avg_weekday_lpn_admin_hours",
    "avg_weekend_lpn_admin_hours",

    "avg_daily_cna_hours",
    "avg_weekday_cna_hours",
    "avg_weekend_cna_hours",

    "avg_daily_na_trainee_hours",
    "avg_weekday_na_trainee_hours",
    "avg_weekend_na_trainee_hours",

    "avg_daily_med_aide_hours",
    "avg_weekday_med_aide_hours",
    "avg_weekend_med_aide_hours",

    "avg_daily_total_nurse_hours",
    "avg_weekday_total_nurse_hours",
    "avg_weekend_total_nurse_hours",

    "avg_daily_census",
    "avg_weekday_census",
    "avg_weekend_census",

    "rn_hours_per_resident_day",
    "rn_hours_per_resident_day_weekday",
    "rn_hours_per_resident_day_weekend",

    "lpn_hours_per_resident_day",
    "lpn_hours_per_resident_day_weekday",
    "lpn_hours_per_resident_day_weekend",

    "cna_hours_per_resident_day",
    "cna_hours_per_resident_day_weekday",
    "cna_hours_per_resident_day_weekend",

    "na_trainee_hours_per_resident_day",
    "na_trainee_hours_per_resident_day_weekday",
    "na_trainee_hours_per_resident_day_weekend",

    "med_aide_hours_per_resident_day",
    "med_aide_hours_per_resident_day_weekday",
    "med_aide_hours_per_resident_day_weekend",

    "total_nurse_hours_per_resident_day",
    "total_nurse_hours_per_resident_day_weekday",
    "total_nurse_hours_per_resident_day_weekend",
]


def _is_weekend(date_col):
    return (F.dayofweek(date_col) == 1) | (F.dayofweek(date_col) == 7)


def _sum_nonnull(*columns):
    # PBJ hours columns are nullable; treat a missing sub-category as 0
    # hours rather than letting a single null null out the whole role total.
    return sum(F.coalesce(F.col(c), F.lit(0.0)) for c in columns)


def transform(spark, silver_frames: dict, gold_frames: dict):
    df_staffing = silver_frames["provider_nurse_staffing"]

    df_dated = df_staffing.withColumn(
        "work_date_parsed", F.to_date(F.col("work_date"), "yyyyMMdd")
    )
    df_dated = df_dated.withColumn(
        "measurement_period",
        F.concat(F.year("work_date_parsed"), F.lit("Q"), F.quarter("work_date_parsed"))
    )
    df_dated = df_dated.withColumn(
        "is_weekend",
        _is_weekend(F.col("work_date_parsed"))
    )

    # RN and LPN are each split across multiple PBJ sub-categories (line
    # staff, admin, and -- for RN only -- Director of Nursing), not a
    # "total" column plus a breakdown. CMS's own national RN/LPN figures
    # (national_provider_averages) sum all of a role's sub-categories, so
    # the facility-level figures need to as well to be comparable -- verified
    # empirically against the NATION row: hrs_rn_staff alone landed at 0.42
    # hours/resident/day vs. CMS's reported 0.668; summing all three RN
    # sub-categories closes most of that gap.
    df_dated = df_dated.withColumn("_all_levels_rn_hours", _sum_nonnull("hrs_rn_staff", "hrs_rn_admin", "hrs_rn_director_of_nursing"))
    df_dated = df_dated.withColumn("_all_levels_lpn_hours", _sum_nonnull("hrs_lpn", "hrs_lpn_admin"))

    # is_weekend-masked columns: each holds its source value on the matching
    # days and null otherwise, so F.avg() over it later averages only those
    # days (F.avg ignores nulls) instead of dragging the average toward zero
    # with the "wrong half" of the week mixed in.
    df_dated = df_dated.withColumn("_weekend_all_levels_rn_hours", F.when(F.col("is_weekend"), F.col("_all_levels_rn_hours")))
    df_dated = df_dated.withColumn("_weekday_all_levels_rn_hours", F.when(~F.col("is_weekend"), F.col("_all_levels_rn_hours")))

    df_dated = df_dated.withColumn("_weekday_hrs_rn_staff", F.when(~F.col("is_weekend"), F.col("hrs_rn_staff")))
    df_dated = df_dated.withColumn("_weekend_hrs_rn_staff", F.when(F.col("is_weekend"), F.col("hrs_rn_staff")))

    df_dated = df_dated.withColumn("_weekday_hrs_rn_admin", F.when(~F.col("is_weekend"), F.col("hrs_rn_admin")))
    df_dated = df_dated.withColumn("_weekend_hrs_rn_admin", F.when(F.col("is_weekend"), F.col("hrs_rn_admin")))

    df_dated = df_dated.withColumn("_weekend_hrs_rn_director_of_nursing", F.when(F.col("is_weekend"), F.col("hrs_rn_director_of_nursing")))
    df_dated = df_dated.withColumn("_weekday_hrs_rn_director_of_nursing", F.when(~F.col("is_weekend"), F.col("hrs_rn_director_of_nursing")))

    df_dated = df_dated.withColumn("_weekday_all_levels_lpn_hours", F.when(~F.col("is_weekend"), F.col("_all_levels_lpn_hours")))
    df_dated = df_dated.withColumn("_weekend_all_levels_lpn_hours", F.when(F.col("is_weekend"), F.col("_all_levels_lpn_hours")))

    df_dated = df_dated.withColumn("_weekday_hrs_lpn", F.when(~F.col("is_weekend"), F.col("hrs_lpn")))
    df_dated = df_dated.withColumn("_weekend_hrs_lpn", F.when(F.col("is_weekend"), F.col("hrs_lpn")))

    df_dated = df_dated.withColumn("_weekend_hrs_lpn_admin", F.when(F.col("is_weekend"), F.col("hrs_lpn_admin")))
    df_dated = df_dated.withColumn("_weekday_hrs_lpn_admin", F.when(~F.col("is_weekend"), F.col("hrs_lpn_admin")))

    df_dated = df_dated.withColumn("_weekday_hrs_cna", F.when(~F.col("is_weekend"), F.col("hrs_cna")))
    df_dated = df_dated.withColumn("_weekend_hrs_cna", F.when(F.col("is_weekend"), F.col("hrs_cna")))

    df_dated = df_dated.withColumn("_weekend_hrs_na_trn", F.when(F.col("is_weekend"), F.col("hrs_na_trn")))
    df_dated = df_dated.withColumn("_weekday_hrs_na_trn", F.when(~F.col("is_weekend"), F.col("hrs_na_trn")))

    df_dated = df_dated.withColumn("_weekday_hrs_med_aide", F.when(~F.col("is_weekend"), F.col("hrs_med_aide")))
    df_dated = df_dated.withColumn("_weekend_hrs_med_aide", F.when(F.col("is_weekend"), F.col("hrs_med_aide")))

    df_dated = df_dated.withColumn("_mds_census_weekend", F.when(F.col("is_weekend"), F.col("mds_census")))
    df_dated = df_dated.withColumn("_mds_census_weekday", F.when(~F.col("is_weekend"), F.col("mds_census")))

    return df_dated.groupBy("provnum", "measurement_period").agg(
        # --- RN ---
        F.avg("_all_levels_rn_hours").alias("avg_daily_rn_hours"),
        F.avg("_weekend_all_levels_rn_hours").alias("avg_weekend_rn_hours"),
        F.avg("_weekday_all_levels_rn_hours").alias("avg_weekday_rn_hours"),
        F.avg("_weekday_hrs_rn_staff").alias("avg_weekday_rn_staff_hours"),
        F.avg("_weekend_hrs_rn_staff").alias("avg_weekend_rn_staff_hours"),
        F.avg("_weekday_hrs_rn_admin").alias("avg_weekday_rn_admin_hours"),
        F.avg("_weekend_hrs_rn_admin").alias("avg_weekend_rn_admin_hours"),
        F.avg("_weekend_hrs_rn_director_of_nursing").alias("avg_weekend_rn_director_of_nursing_hours"),
        F.avg("_weekday_hrs_rn_director_of_nursing").alias("avg_weekday_rn_director_of_nursing_hours"),

        # --- LPN ---
        F.avg("_all_levels_lpn_hours").alias("avg_daily_lpn_hours"),
        F.avg("_weekend_all_levels_lpn_hours").alias("avg_weekend_lpn_hours"),
        F.avg("_weekday_all_levels_lpn_hours").alias("avg_weekday_lpn_hours"),
        F.avg("_weekday_hrs_lpn").alias("avg_weekday_lpn_staff_hours"),
        F.avg("_weekend_hrs_lpn").alias("avg_weekend_lpn_staff_hours"),
        F.avg("_weekend_hrs_lpn_admin").alias("avg_weekend_lpn_admin_hours"),
        F.avg("_weekday_hrs_lpn_admin").alias("avg_weekday_lpn_admin_hours"),

        # --- CNA ---
        F.avg("hrs_cna").alias("avg_daily_cna_hours"),
        F.avg("_weekday_hrs_cna").alias("avg_weekday_cna_hours"),
        F.avg("_weekend_hrs_cna").alias("avg_weekend_cna_hours"),

        # --- NA trainee ---
        F.avg("hrs_na_trn").alias("avg_daily_na_trainee_hours"),
        F.avg("_weekend_hrs_na_trn").alias("avg_weekend_na_trainee_hours"),
        F.avg("_weekday_hrs_na_trn").alias("avg_weekday_na_trainee_hours"),

        # --- Med aide ---
        F.avg("hrs_med_aide").alias("avg_daily_med_aide_hours"),
        F.avg("_weekday_hrs_med_aide").alias("avg_weekday_med_aide_hours"),
        F.avg("_weekend_hrs_med_aide").alias("avg_weekend_med_aide_hours"),

        # --- Total nurse (RN + LPN + CNA) ---
        F.avg(F.col("_all_levels_rn_hours") + F.col("_all_levels_lpn_hours") + F.coalesce(F.col("hrs_cna"), F.lit(0.0))).alias("avg_daily_total_nurse_hours"),
        F.avg(F.col("_weekday_all_levels_rn_hours") + F.col("_weekday_all_levels_lpn_hours") + F.coalesce(F.col("_weekday_hrs_cna"), F.lit(0.0))).alias("avg_weekday_total_nurse_hours"),
        F.avg(F.col("_weekend_all_levels_rn_hours") + F.col("_weekend_all_levels_lpn_hours") + F.coalesce(F.col("_weekend_hrs_cna"), F.lit(0.0))).alias("avg_weekend_total_nurse_hours"),

        # --- Census ---
        F.avg("mds_census").alias("avg_daily_census"),
        F.avg("_mds_census_weekend").alias("avg_weekend_census"),
        F.avg("_mds_census_weekday").alias("avg_weekday_census"),

        # --- Hours per resident day: RN ---
        F.try_divide(F.avg("_all_levels_rn_hours"), F.avg("mds_census")).alias("rn_hours_per_resident_day"),
        F.try_divide(F.avg("_weekday_all_levels_rn_hours"), F.avg("_mds_census_weekday")).alias("rn_hours_per_resident_day_weekday"),
        F.try_divide(F.avg("_weekend_all_levels_rn_hours"), F.avg("_mds_census_weekend")).alias("rn_hours_per_resident_day_weekend"),

        # --- Hours per resident day: LPN ---
        F.try_divide(F.avg("_all_levels_lpn_hours"), F.avg("mds_census")).alias("lpn_hours_per_resident_day"),
        F.try_divide(F.avg("_weekday_all_levels_lpn_hours"), F.avg("_mds_census_weekday")).alias("lpn_hours_per_resident_day_weekday"),
        F.try_divide(F.avg("_weekend_all_levels_lpn_hours"), F.avg("_mds_census_weekend")).alias("lpn_hours_per_resident_day_weekend"),

        # --- Hours per resident day: CNA ---
        F.try_divide(F.avg("hrs_cna"), F.avg("mds_census")).alias("cna_hours_per_resident_day"),
        F.try_divide(F.avg("_weekday_hrs_cna"), F.avg("_mds_census_weekday")).alias("cna_hours_per_resident_day_weekday"),
        F.try_divide(F.avg("_weekend_hrs_cna"), F.avg("_mds_census_weekend")).alias("cna_hours_per_resident_day_weekend"),

        # --- Hours per resident day: NA trainee ---
        F.try_divide(F.avg("hrs_na_trn"), F.avg("mds_census")).alias("na_trainee_hours_per_resident_day"),
        F.try_divide(F.avg("_weekday_hrs_na_trn"), F.avg("_mds_census_weekday")).alias("na_trainee_hours_per_resident_day_weekday"),
        F.try_divide(F.avg("_weekend_hrs_na_trn"), F.avg("_mds_census_weekend")).alias("na_trainee_hours_per_resident_day_weekend"),

        # --- Hours per resident day: med aide ---
        F.try_divide(F.avg("hrs_med_aide"), F.avg("mds_census")).alias("med_aide_hours_per_resident_day"),
        F.try_divide(F.avg("_weekday_hrs_med_aide"), F.avg("_mds_census_weekday")).alias("med_aide_hours_per_resident_day_weekday"),
        F.try_divide(F.avg("_weekend_hrs_med_aide"), F.avg("_mds_census_weekend")).alias("med_aide_hours_per_resident_day_weekend"),

        # --- Hours per resident day: total nurse ---
        F.try_divide(F.avg(F.col("_all_levels_rn_hours") + F.col("_all_levels_lpn_hours") + F.coalesce(F.col("hrs_cna"), F.lit(0.0))), F.avg("mds_census")).alias("total_nurse_hours_per_resident_day"),
        F.try_divide(F.avg(F.col("_weekday_all_levels_rn_hours") + F.col("_weekday_all_levels_lpn_hours") + F.coalesce(F.col("_weekday_hrs_cna"), F.lit(0.0))), F.avg("_mds_census_weekday")).alias("total_nurse_hours_per_resident_day_weekday"),
        F.try_divide(F.avg(F.col("_weekend_all_levels_rn_hours") + F.col("_weekend_all_levels_lpn_hours") + F.coalesce(F.col("_weekend_hrs_cna"), F.lit(0.0))), F.avg("_mds_census_weekend")).alias("total_nurse_hours_per_resident_day_weekend"),
    )
