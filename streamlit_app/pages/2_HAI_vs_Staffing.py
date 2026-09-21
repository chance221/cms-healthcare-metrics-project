import streamlit as st

from streamlit_app.lib.staffing_chart import MeasureConfig, render_staffing_page

st.set_page_config(page_title="Staffing vs. HAI", layout="wide")

CONFIG = MeasureConfig(
    gold_dataset_name="hai_vs_staffing",
    display_name="Healthcare-Associated Infection Rates",
    volume_col="hai_volume",
    volume_label="Minimum HAI volume",
    rate_col="hai_rs_rate",
    rate_label="Average adjusted HAI rate",
    ci_lower_col="hai_rs_rate_lower_ci",
    ci_upper_col="hai_rs_rate_upper_ci",
)

render_staffing_page(CONFIG)
