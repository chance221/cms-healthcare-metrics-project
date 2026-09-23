from dataclasses import dataclass

import altair as alt
import pandas as pd
import streamlit as st

from pyspark_jobs.common.config_loader import load_all_environment_configs, load_all_gold_configs
from pyspark_jobs.common.io_utils import resolve_pandas_path

STAFFING_METRICS = {
    "RN hours": "rn_hours_per_resident_day",
    "LPN hours": "lpn_hours_per_resident_day",
    "CNA hours": "cna_hours_per_resident_day",
    "Total nurse hours": "total_nurse_hours_per_resident_day",
}

QUARTILE_LABELS = ["Lower", "Lower middle", "Upper middle", "Upper"]

QUARTILE_COLORS = ["#86b6ef", "#5598e7", "#256abf", "#104281"]


@dataclass
class MeasureConfig:
    gold_dataset_name: str
    display_name: str  
    volume_col: str  
    volume_label: str  
    rate_col: str  
    rate_label: str  
    ci_lower_col: str | None = None  
    ci_upper_col: str | None = None
    y_domain: tuple[float, float] | None = None  


@st.cache_data
def load_gold(gold_dataset_name: str, env: str = "prod") -> pd.DataFrame:
    env_configs, _ = load_all_environment_configs()
    env_config = next(c for c in env_configs.values() if c.env == env)
    gold_configs, _ = load_all_gold_configs()
    gold_config = next(c for c in gold_configs.values() if c.gold_dataset_name == gold_dataset_name)
    path = resolve_pandas_path(env_config, gold_config.output_path.format(env=env_config.env))
    return pd.read_parquet(path)


def quartile_summary(d: pd.DataFrame, staffing_col: str, rate_col: str, period_label: str) -> pd.DataFrame:
    working = d.dropna(subset=[staffing_col, rate_col]).copy()
    if len(working) < 4:
        return pd.DataFrame(columns=["staffing_quartile", "avg_rate", "n", "period"])
    working["staffing_quartile"] = pd.qcut(working[staffing_col], 4, labels=QUARTILE_LABELS, duplicates="drop")
    summary = (
        working.groupby("staffing_quartile", observed=True)
        .agg(avg_rate=(rate_col, "mean"), n=(rate_col, "size"))
        .reset_index()
    )
    summary["period"] = period_label
    return summary


def render_staffing_page(config: MeasureConfig) -> None:
    st.title(f"Nurse Staffing vs. {config.display_name}")

    st.sidebar.header("Environment")
    selected_env = st.sidebar.selectbox(
        "Data environment", ["prod", "dev"], key="pipeline_env"
    )

    df = load_gold(config.gold_dataset_name, env=selected_env)
    key_prefix = config.gold_dataset_name

    st.sidebar.header("Filters")

    states = ["All states"] + sorted(df["state"].unique())
    selected_state = st.sidebar.selectbox("State", states, key=f"{key_prefix}_state")

    min_volume = st.sidebar.slider(
        config.volume_label,
        min_value=1,
        max_value=int(df[config.volume_col].max()),
        value=min(50, int(df[config.volume_col].max())),
        key=f"{key_prefix}_volume",
    )

    has_ci = config.ci_lower_col is not None and config.ci_upper_col is not None
    if has_ci:
        ci_width = df[config.ci_upper_col] - df[config.ci_lower_col]
        max_ci_width_available = float(ci_width.max())
        max_ci_width = st.sidebar.slider(
            "Maximum CI width",
            min_value=0.0,
            max_value=max_ci_width_available,
            value=max_ci_width_available,
            step=0.5,
            key=f"{key_prefix}_ci_width",
        )
    else:
        st.sidebar.caption("No confidence-interval columns for this measure -- CI-width filter not available.")
        ci_width = None
        max_ci_width = None

    max_staffing_coverage = int(df["staffing_quarters_expected"].max())
    min_staffing_coverage = st.sidebar.slider(
        f"Minimum staffing quarters matched (of {max_staffing_coverage})",
        min_value=0,
        max_value=max_staffing_coverage,
        value=max_staffing_coverage,
        key=f"{key_prefix}_coverage",
    )

    staffing_metric_label = st.sidebar.selectbox(
        "Staffing metric", list(STAFFING_METRICS.keys()), key=f"{key_prefix}_metric"
    )
    staffing_metric_base = STAFFING_METRICS[staffing_metric_label]

    filtered = df[
        (df[config.volume_col] > min_volume) & (df["staffing_quarters_matched"] >= min_staffing_coverage)
    ]
    if has_ci:
        filtered = filtered[ci_width.loc[filtered.index] < max_ci_width]
    if selected_state != "All states":
        filtered = filtered[filtered["state"] == selected_state]

    st.write(f"Facilities after filters: **{len(filtered):,}** (of {len(df):,} total)")

    weekday_col = f"{staffing_metric_base}_weekday"
    weekend_col = f"{staffing_metric_base}_weekend"

    chart_data = pd.concat(
        [
            quartile_summary(filtered, weekday_col, config.rate_col, "Weekday"),
            quartile_summary(filtered, weekend_col, config.rate_col, "Weekend"),
        ],
        ignore_index=True,
    )

    if chart_data.empty or chart_data["n"].sum() == 0:
        st.warning("Not enough facilities left after these filters to build quartiles. Try loosening them.")
        return

    y_encoding = alt.Y("avg_rate:Q", title=config.rate_label)
    encode_kwargs = {}
    if config.y_domain is not None:
        
        y_encoding = alt.Y(
            "avg_rate:Q",
            title=config.rate_label,
            scale=alt.Scale(domain=list(config.y_domain), zero=False),
        )
        encode_kwargs["y2"] = alt.Y2(datum=config.y_domain[0])

    chart = (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=32)
        .encode(
            x=alt.X("staffing_quartile:O", sort=QUARTILE_LABELS, title=f"{staffing_metric_label} quartile"),
            y=y_encoding,
            color=alt.Color(
                "staffing_quartile:O",
                sort=QUARTILE_LABELS,
                scale=alt.Scale(domain=QUARTILE_LABELS, range=QUARTILE_COLORS),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("staffing_quartile:O", title="Quartile"),
                alt.Tooltip("avg_rate:Q", title=config.rate_label, format=".2f"),
                alt.Tooltip("n:Q", title="Facilities"),
            ],
            **encode_kwargs,
        )
        .properties(width=300, height=350)
        .facet(column=alt.Column("period:N", title=None, sort=["Weekday", "Weekend"]))
        .resolve_scale(y="shared")
    )
    st.altair_chart(chart, width="content")
