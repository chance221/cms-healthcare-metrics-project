import streamlit as st

from streamlit_app.lib.staffing_chart import MeasureConfig, render_staffing_page

st.set_page_config(page_title="Staffing vs. DTC", layout="wide")

CONFIG = MeasureConfig(
    gold_dataset_name="dtc_vs_staffing",
    display_name="Discharge-to-Community Rates",
    volume_col="dtc_volume",
    volume_label="Minimum DTC volume",
    rate_col="dtc_rs_rate",
    rate_label="Average adjusted discharge-to-community rate",
    ci_lower_col="dtc_rs_rate_lower_ci",
    ci_upper_col="dtc_rs_rate_upper_ci",
)

render_staffing_page(CONFIG)
