import importlib
import os
import sys
from pathlib import Path
import yaml
from pydantic import ValidationError

try:
    from awsglue.utils import getResolvedOptions
except ImportError:
    getResolvedOptions = None

if getResolvedOptions is not None:
    args = getResolvedOptions(sys.argv, ["PIPELINE_CONFIG_ROOT"])
    os.environ["PIPELINE_CONFIG_ROOT"] = args["PIPELINE_CONFIG_ROOT"]
    import zipfile
    config_root = Path(args["PIPELINE_CONFIG_ROOT"])
    configs_zip = config_root / "configs.zip"
    if configs_zip.exists():
        with zipfile.ZipFile(configs_zip) as zf:
            zf.extractall(config_root)


from pyspark_jobs.common.config_models import DatasetConfig, EnvironmentConfig, GoldConfig


def _resolve_repo_root() -> Path:   
    #Override for glue job
    override = os.environ.get("PIPELINE_CONFIG_ROOT")
    if override is not None:
        override_root = Path(override)
        if not (override_root / "configs").is_dir():
            raise RuntimeError(
                f"PIPELINE_CONFIG_ROOT={override!r} does not contain a 'configs' directory -- "
                f"check the deployment's job parameters point at the right location."
            )
        return override_root
    return Path(__file__).resolve().parents[2]


REPO_ROOT = _resolve_repo_root()
DATASETS_DIR = REPO_ROOT / "configs" / "datasets"
ENVIRONMENTS_DIR = REPO_ROOT / "configs" / "environment"
GOLD_DIR = REPO_ROOT / "configs" / "gold"


def _find_config_files(directory: Path) -> list[Path]:
    return sorted(set(directory.glob("*.yaml")) | set(directory.glob("*.yml")))


def _load_yaml_dict(path: Path) -> dict:
    with open(path, "r") as targetConfigFile:
        raw = yaml.safe_load(targetConfigFile)

    if raw is None:
        raise ValueError(f"{path.name} is empty")
    if not isinstance(raw, dict):
        raise ValueError(f"{path.name} does not contain a YAML mapping at the top level")

    return raw


def load_dataset_config(path: Path) -> DatasetConfig:
    raw = _load_yaml_dict(path)
    return DatasetConfig.model_validate(raw)


def load_environment_config(path: Path) -> EnvironmentConfig:
    raw = _load_yaml_dict(path)
    return EnvironmentConfig.model_validate(raw)


def load_gold_config(path: Path) -> GoldConfig:
    raw = _load_yaml_dict(path)
    return GoldConfig.model_validate(raw)


def load_all_dataset_configs() -> tuple[dict[str, DatasetConfig], dict[str, str]]:
    configs: dict[str, DatasetConfig] = {}
    errors: dict[str, str] = {}

    for path in _find_config_files(DATASETS_DIR):
        try:
            configs[path.name] = load_dataset_config(path)
        except (ValueError, ValidationError) as e:
            errors[path.name] = str(e)

    return configs, errors


def load_all_gold_configs() -> tuple[dict[str, GoldConfig], dict[str, str]]:
    configs: dict[str, GoldConfig] = {}
    errors: dict[str, str] = {}

    for path in _find_config_files(GOLD_DIR):
        try:
            configs[path.name] = load_gold_config(path)
        except (ValueError, ValidationError) as e:
            errors[path.name] = str(e)
    
    dataset_configs, dataset_errors = load_all_dataset_configs()
    known_dataset_names = {c.dataset_name for c in dataset_configs.values()}
    known_gold_dataset_names = {c.gold_dataset_name for c in configs.values()}

    for name, gold_config in list(configs.items()):
        missing_sources = [s for s in gold_config.sources if s not in known_dataset_names]
        if missing_sources and not dataset_errors:

            errors[name] = f"sources not found among known datasets: {missing_sources}"
            del configs[name]
            continue

        missing_gold_sources = [
            s for s in gold_config.gold_sources
            if s not in known_gold_dataset_names or s == gold_config.gold_dataset_name
        ]
        if missing_gold_sources:
            errors[name] = f"gold_sources not found among known gold datasets (or self-referencing): {missing_gold_sources}"
            del configs[name]
            continue

        try:
            module = importlib.import_module(gold_config.transform_module)
        except ImportError as e:
            errors[name] = f"transform_module '{gold_config.transform_module}' is not importable: {e}"
            del configs[name]
            continue

        if not callable(getattr(module, "transform", None)):
            errors[name] = f"transform_module '{gold_config.transform_module}' has no callable 'transform' function"
            del configs[name]

    return configs, errors


def load_all_environment_configs() -> tuple[dict[str, EnvironmentConfig], dict[str, str]]:
    configs: dict[str, EnvironmentConfig] = {}
    errors: dict[str, str] = {}

    for path in _find_config_files(ENVIRONMENTS_DIR):
        try:
            configs[path.name] = load_environment_config(path)
        except (ValueError, ValidationError) as e:
            errors[path.name] = str(e)

    s3buckets = {name: cfg.s3_bucket for name, cfg in configs.items()}
    distinct_buckets = set(s3buckets.values())
    if len(distinct_buckets) > 1:
        errors["(cross-file)"] = (
            f"environment configs disagree on s3_bucket: {s3buckets}"
        )

    return configs, errors


def _print_report(kind: str, 
                  configs: dict, 
                  errors: dict) -> bool:
    print(f"\n{kind}:")
    for name in configs:
        print(f"  [OK]   {name}")
    for name, message in errors.items():
        print(f"  [FAIL] {name}: {message}")
    return not errors


if __name__ == "__main__":
    dataset_configs, dataset_errors = load_all_dataset_configs()
    env_configs, env_errors = load_all_environment_configs()
    gold_configs, gold_errors = load_all_gold_configs()

    datasets_ok = _print_report("Dataset configs", dataset_configs, dataset_errors)
    envs_ok = _print_report("Environment configs", env_configs, env_errors)
    gold_ok = _print_report("Gold configs", gold_configs, gold_errors)

    if datasets_ok and envs_ok and gold_ok:
        print("\nAll configs valid.")
        sys.exit(0)
    else:
        print("\nValidation failed.")
        sys.exit(1)
