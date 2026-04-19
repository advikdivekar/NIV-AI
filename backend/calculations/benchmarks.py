"""
Mumbai real estate benchmark loader.
Fuzzy-matches user-entered area names to static dataset.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from typing import Optional

_DATA_PATH = Path(__file__).parent.parent / "data" / "mumbai_benchmarks.json"
_cache: Optional[dict] = None


@dataclass
class AreaBenchmark:
    key: str
    name: str
    price_min: float
    price_median: float
    price_max: float
    maintenance_typical: float
    rental_yield_pct: float
    distance_to_bkc_km: float
    distance_to_lower_parel_km: float
    metro_connectivity: bool
    infrastructure_notes: str
    flood_risk: str
    data_as_of: str


def _load() -> dict:
    global _cache
    if _cache is None:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            _cache = json.load(f)
    return _cache


def _normalize(name: str) -> str:
    return (name.lower().strip().replace("-", " ").replace("_", " ")
            .replace("(", "").replace(")", "").replace(",", ""))


def lookup_area(user_input: str) -> Optional[AreaBenchmark]:
    data = _load()
    normalized = _normalize(user_input)
    key_attempt = normalized.replace(" ", "_")
    if key_attempt in data:
        return _build(key_attempt, data[key_attempt])
    name_map = {}
    for key, info in data.items():
        name_map[_normalize(info["name"])] = key
    matches = get_close_matches(normalized, name_map.keys(), n=1, cutoff=0.6)
    if matches:
        return _build(name_map[matches[0]], data[name_map[matches[0]]])
    key_matches = get_close_matches(normalized.replace(" ", "_"), data.keys(), n=1, cutoff=0.6)
    if key_matches:
        return _build(key_matches[0], data[key_matches[0]])
    return None


def list_areas() -> list:
    return [info["name"] for info in _load().values()]


def get_maintenance_estimate(user_area: str) -> float:
    area = lookup_area(user_area)
    return area.maintenance_typical if area else 5.5


def get_rental_yield(user_area: str) -> float:
    area = lookup_area(user_area)
    return area.rental_yield_pct if area else 2.5


def _build(key: str, raw: dict) -> AreaBenchmark:
    return AreaBenchmark(key=key, name=raw["name"],
                         price_min=raw["avg_price_per_sqft"]["min"],
                         price_median=raw["avg_price_per_sqft"]["median"],
                         price_max=raw["avg_price_per_sqft"]["max"],
                         maintenance_typical=raw["maintenance_per_sqft_monthly"]["typical"],
                         rental_yield_pct=raw["rental_yield_pct"],
                         distance_to_bkc_km=raw["distance_to_bkc_km"],
                         distance_to_lower_parel_km=raw["distance_to_lower_parel_km"],
                         metro_connectivity=raw["metro_connectivity"],
                         infrastructure_notes=raw["infrastructure_notes"],
                         flood_risk=raw["flood_risk"],
                         data_as_of=raw["data_as_of"])
