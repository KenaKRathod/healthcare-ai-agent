import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd


def parse_json(file_path: str | Path) -> pd.DataFrame:
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as file_handle:
        payload = json.load(file_handle)

    if isinstance(payload, list):
        return pd.json_normalize(payload)
    if isinstance(payload, dict):
        if "records" in payload and isinstance(payload["records"], list):
            return pd.json_normalize(payload["records"])
        return pd.json_normalize([payload])

    raise ValueError("Unsupported JSON format. Expected an object or a list of objects.")


def parse_csv(file_path: str | Path) -> pd.DataFrame:
    path = Path(file_path)
    return pd.read_csv(path)


def parse_xml(file_path: str | Path, record_tag: str = "record") -> pd.DataFrame:
    path = Path(file_path)
    tree = ET.parse(path)
    root = tree.getroot()

    records = []
    for element in root.findall(f".//{record_tag}"):
        record = {child.tag: child.text for child in element}
        records.append(record)

    if not records:
        records = [{child.tag: child.text for child in root}]

    return pd.DataFrame(records)
