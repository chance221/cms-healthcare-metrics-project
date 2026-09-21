import streamlit as st

from streamlit_app.lib.staffing_chart import MeasureConfig, render_staffing_page

st.set_page_config(page_title="Staffing vs. Falls", layout="wide")

# S_013_02 has no risk-adjusted rate and no CI columns at all in the real
# gold table -- falls_obs_rate (observed, unadjusted) is the only rate this
# measure family provides, so that's what's used here. Labeled "observed",
# not "adjusted", so it isn't mistaken for the same kind of figure the other
# four pages show.
CONFIG = MeasureConfig(
    gold_dataset_name="falls_vs_staffing",
    display_name="Falls Rates",
    volume_col="falls_denominator",
    volume_label="Minimum falls denominator",
    rate_col="falls_obs_rate",
    rate_label="Average observed falls rate (unadjusted -- no adjusted rate available)",
)

render_staffing_page(CONFIG)
