import argparse
import importlib

from pyspark_jobs.common.config_loader import (
    load_all_dataset_configs,
    load_all_environment_configs,
    load_all_gold_configs,
)
from pyspark_jobs.common.config_models import EnvironmentConfig, GoldConfig
from pyspark_jobs.common.io_utils import read_gold_dataset, read_silver_dataset, resolve_path
from pyspark_jobs.common.spark_session import build_spark_session


def order_gold_datasets_by_dependency(gold_configs: list[GoldConfig]) -> list[GoldConfig]:
    # Kahn's algorithm over gold_sources, so a gold job that reads another
    # gold job's output always builds before anything depending on it.
    
    by_name = {c.gold_dataset_name: c for c in gold_configs}
    in_degree = {name: 0 for name in by_name}
    dependents: dict[str, list[str]] = {name: [] for name in by_name}

    for c in gold_configs:
        for dep_name in c.gold_sources:
            if dep_name not in by_name:
                continue
            in_degree[c.gold_dataset_name] += 1
            dependents[dep_name].append(c.gold_dataset_name)

    queue = [name for name, degree in in_degree.items() if degree == 0]
    ordered_names = []
    while queue:
        name = queue.pop(0)
        ordered_names.append(name)
        for dependent_name in dependents[name]:
            in_degree[dependent_name] -= 1
            if in_degree[dependent_name] == 0:
                queue.append(dependent_name)

    if len(ordered_names) != len(gold_configs):
        unresolved = set(by_name) - set(ordered_names)
        raise RuntimeError(f"Cycle detected among gold_sources dependencies: {unresolved}")

    return [by_name[name] for name in ordered_names]


def run_gold_dataset(spark,
                     gold_config: GoldConfig,
                     env_config: EnvironmentConfig,
                     dataset_configs_by_name: dict,
                     gold_configs_by_name: dict) -> None:
    silver_frames = {
        source_name: read_silver_dataset(spark, env_config, dataset_configs_by_name[source_name])
        for source_name in gold_config.sources
    }
    gold_frames = {
        source_name: read_gold_dataset(spark, env_config, gold_configs_by_name[source_name])
        for source_name in gold_config.gold_sources
    }

    module = importlib.import_module(gold_config.transform_module)
    df_gold = module.transform(spark, silver_frames, gold_frames)

    output_relative_path = gold_config.output_path.format(env=env_config.env)
    output_path = resolve_path(env_config, output_relative_path)

    # Gold is always a full rebuild from current silver/gold inputs
    # As this grows over the years would refactor to partitioned writes, but for now it's small enough to overwrite
    df_gold.write.mode("overwrite").parquet(output_path)

    print(f"[{gold_config.gold_dataset_name}] gold row count: {df_gold.count()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run gold-layer transforms against current silver data")
    parser.add_argument("--env", required=True, choices=["local", "dev", "prod"])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--gold-dataset", help="gold_dataset_name of a single gold config to run")
    group.add_argument("--all", action="store_true", help="run every gold config")
    args, _unknown_args = parser.parse_known_args()

    env_configs, env_errors = load_all_environment_configs()
    if env_errors:
        raise RuntimeError(f"Cannot start: environment configs are invalid: {env_errors}")
    env_matches = [c for c in env_configs.values() if c.env == args.env]
    if not env_matches:
        raise ValueError(f"No environment config found with env='{args.env}'")
    env_config = env_matches[0]

    dataset_configs, dataset_errors = load_all_dataset_configs()
    if dataset_errors:
        raise RuntimeError(f"Cannot start: dataset configs are invalid: {dataset_errors}")
    dataset_configs_by_name = {c.dataset_name: c for c in dataset_configs.values()}

    gold_configs, gold_errors = load_all_gold_configs()
    if gold_errors:
        raise RuntimeError(f"Cannot start: gold configs are invalid: {gold_errors}")
    gold_configs_by_name = {c.gold_dataset_name: c for c in gold_configs.values()}

    if args.all:
        gold_datasets_to_run = order_gold_datasets_by_dependency(list(gold_configs.values()))
    else:
        gold_datasets_to_run = [c for c in gold_configs.values() if c.gold_dataset_name == args.gold_dataset]
        if not gold_datasets_to_run:
            raise ValueError(f"No gold config found with gold_dataset_name='{args.gold_dataset}'")

    spark = build_spark_session(env_config, app_name="silver-to-gold")
    try:
        for gold_config in gold_datasets_to_run:
            run_gold_dataset(spark, gold_config, env_config, dataset_configs_by_name, gold_configs_by_name)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
