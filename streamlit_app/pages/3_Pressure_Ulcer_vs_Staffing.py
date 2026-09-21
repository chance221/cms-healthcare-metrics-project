import streamlit as st

from streamlit_app.lib.staffing_chart import MeasureConfig, render_staffing_page

st.set_page_config(page_title="Staffing vs. Pressure Ulcers", layout="wide")

# No readmission-style CI columns exist for this measure family -- CMS's own
# S_038_02 data never included them (confirmed against the real gold table),
# so ci_lower_col/ci_upper_col stay unset and the CI-width filter is skipped.
CONFIG = MeasureConfig(
    gold_dataset_name="pressure_ulcer_vs_staffing",
    display_name="Pressure Ulcer Rates",
    volume_col="pressure_ulcer_denominator",
    volume_label="Minimum pressure ulcer denominator",
    rate_col="pressure_ulcer_adj_rate",
    rate_label="Average adjusted pressure ulcer rate",
)

render_staffing_page(CONFIG)
