import json
import os


def read_ccloud_config(config_file: str) -> dict:
    with open(config_file, "r") as f:
        return json.load(f)


def read_schema(schema_file: str) -> str:
    schema_str = ""
    current_path = os.path.realpath(os.path.dirname(__file__))
    with open(f"{current_path}/avro/{schema_file}") as f:
        schema_str = f.read()

    return schema_str
