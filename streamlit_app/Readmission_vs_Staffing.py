import streamlit as st

from streamlit_app.lib.staffing_chart import MeasureConfig, render_staffing_page

st.set_page_config(page_title="Staffing vs. Readmissions", layout="wide")

CONFIG = MeasureConfig(
    gold_dataset_name="readmission_vs_staffing",
    display_name="Readmission Rates",
    volume_col="readmission_volume",
    volume_label="Minimum readmission volume",
    rate_col="readmission_rsrr",
    rate_label="Average adjusted readmission rate",
    ci_lower_col="readmission_rsrr_lower_ci",
    ci_upper_col="readmission_rsrr_upper_ci",
    y_domain=(5, 11),
)

render_staffing_page(CONFIG)
