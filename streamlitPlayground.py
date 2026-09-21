import pandas as pd
import streamlit as st
from pyspark_jobs.common.config_loader import load_all_environment_configs, load_all_gold_configs
from pyspark_jobs.common.io_utils import resolve_path

env_configs, _ = load_all_environment_configs()
env_config = next(c for c in env_configs.values() if c.env == "local")

gold_configs, _ = load_all_gold_configs()
gold_config = gold_configs["readmission_vs_staffing.yaml"]

path = resolve_path(env_config, gold_config.output_path.format(env=env_config.env))
df = pd.read_parquet(path)

st.dataframe(df.head(10))