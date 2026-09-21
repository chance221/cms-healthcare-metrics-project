from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Literal, Optional


class ColumnDef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: Literal["string", "int", "long", "double", "timestamp", "boolean"]
    nullable: bool = True
    expected_raw_header: str


class RawConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prefix_pattern: str
    format: Literal["csv"] = "csv"


class SilverConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output_path: str


class DatasetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    description: Optional[str] = None
    raw: RawConfig
    primary_key: list[str]
    dedup_order_by: Optional[str] = None
    delete_missing_keys: bool = False
    ignore_extra_columns: list[str] = Field(default_factory=list)
    schema_: list[ColumnDef] = Field(alias="schema")
    silver: SilverConfig
    partition_source_column: Optional[str] = None

    @field_validator("primary_key")
    @classmethod
    def primary_key_not_empty_and_no_duplicates(cls, v):
        if not v:
            raise ValueError("primary_key must list at least one column")
        dupes = {x for x in v if v.count(x) > 1}
        if dupes:
            raise ValueError(f"primary_key lists the same column twice: {dupes}")
        return v

    @model_validator(mode="after")
    def primary_key_and_dedup_columns_exist(self):
        
        UNSAFE_KEY_TYPES = {"int", "long"}

        columns_by_name = {c.name: c for c in self.schema_}

        for pk_col in self.primary_key:
            if pk_col not in columns_by_name:
                raise ValueError(f"primary_key column '{pk_col}' not found in schema")
            if columns_by_name[pk_col].type in UNSAFE_KEY_TYPES:
                raise ValueError(
                    f"primary_key column '{pk_col}' should not be type "
                    f"'{columns_by_name[pk_col].type}' (risks losing leading "
                    f"zeros/precision on ID-like codes) — use 'string' instead"
                )

        if self.dedup_order_by is not None and self.dedup_order_by not in columns_by_name:
            raise ValueError(
                f"dedup_order_by column '{self.dedup_order_by}' not found in schema"
            )

        if self.partition_source_column is not None and self.partition_source_column not in columns_by_name:
            raise ValueError(
                f"partition_source_column '{self.partition_source_column}' not found in schema"
            )

        return self


class GoldConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gold_dataset_name: str
    description: Optional[str] = None    
    sources: list[str] = Field(default_factory=list)
    gold_sources: list[str] = Field(default_factory=list)
    transform_module: str
    output_path: str

    @model_validator(mode="after")
    def at_least_one_source(self):
        if not self.sources and not self.gold_sources:
            raise ValueError("gold config must list at least one of 'sources' or 'gold_sources'")
        return self


class EnvironmentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    env: Literal["local", "dev", "prod"]
    s3_bucket: str
    aws_profile: Optional[str] = None
    spark_master: Optional[str] = None
    write_strategy: Literal["local", "aws"]
