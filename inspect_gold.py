import argparse

import pandas as pd

from pyspark_jobs.common.config_loader import load_all_environment_configs, load_all_gold_configs
from pyspark_jobs.common.io_utils import resolve_pandas_path


def inspect_gold_dataset(gold_config, env_config) -> None:
    output_relative_path = gold_config.output_path.format(env=env_config.env)
    output_path = resolve_pandas_path(env_config, output_relative_path)

    df = pd.read_parquet(output_path)

    print(f"\n=== {gold_config.gold_dataset_name} ===")
    print(f"path: {output_path}")
    print(f"rows: {len(df):,}")
    print(f"columns ({len(df.columns)}):")
    for col in df.columns:
        non_null = df[col].notna().sum()
        print(f"  {col:<50} {str(df[col].dtype):<10} non-null: {non_null:,}/{len(df):,}")
    print("\nsample rows:")
    print(df.head(3).to_string())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect gold-layer parquet output (local or S3, via --env). Reads "
        "directly with pandas for fast ad hoc exploration, not through Spark."
    )
    parser.add_argument("--env", default="local", choices=["local", "dev", "prod"])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--gold-dataset", help="gold_dataset_name of a single gold config to inspect")
    group.add_argument("--all", action="store_true", help="inspect every gold config")
    args = parser.parse_args()

    env_configs, env_errors = load_all_environment_configs()
    if env_errors:
        raise RuntimeError(f"Cannot start: environment configs are invalid: {env_errors}")
    env_matches = [c for c in env_configs.values() if c.env == args.env]
    if not env_matches:
        raise ValueError(f"No environment config found with env='{args.env}'")
    env_config = env_matches[0]

    gold_configs, gold_errors = load_all_gold_configs()
    if gold_errors:
        raise RuntimeError(f"Cannot start: gold configs are invalid: {gold_errors}")

    if args.all:
        datasets_to_inspect = list(gold_configs.values())
    else:
        datasets_to_inspect = [c for c in gold_configs.values() if c.gold_dataset_name == args.gold_dataset]
        if not datasets_to_inspect:
            raise ValueError(f"No gold config found with gold_dataset_name='{args.gold_dataset}'")

    for gold_config in datasets_to_inspect:
        inspect_gold_dataset(gold_config, env_config)


if __name__ == "__main__":
    main()
