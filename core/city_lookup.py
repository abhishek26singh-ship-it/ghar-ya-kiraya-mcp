import json
import os

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "residex.json")

with open(_DATA_PATH, "r") as f:
    _RESIDEX = json.load(f)

_CITIES = _RESIDEX["cities"]
_ALIASES = {k.lower(): v for k, v in _RESIDEX["aliases"].items()}
_NATIONAL_AVG = _RESIDEX["national_avg_appreciation"]
_SOURCE = _RESIDEX["source"]

# Build a lowercase lookup for city names
_CITY_LOWER = {k.lower(): k for k in _CITIES}


def normalise_city(raw: str) -> str | None:
    """Normalise a city name to canonical form. Returns None if unrecognised."""
    key = raw.strip().lower()
    # Direct match
    if key in _CITY_LOWER:
        return _CITY_LOWER[key]
    # Alias match
    if key in _ALIASES:
        return _ALIASES[key]
    return None


def get_appreciation_data(city: str) -> dict | None:
    """Return yearly appreciation dict for a normalised city."""
    canonical = normalise_city(city)
    if canonical and canonical in _CITIES:
        return _CITIES[canonical]["appreciation"]
    return None


def get_avg_appreciation(city: str) -> float:
    """Return 5-year average appreciation for a city. Falls back to national average."""
    data = get_appreciation_data(city)
    if data:
        values = list(data.values())
        return round(sum(values) / len(values), 1)
    return _NATIONAL_AVG


def get_city_info(city: str) -> dict | None:
    """Return full city info including appreciation and rent."""
    canonical = normalise_city(city)
    if canonical and canonical in _CITIES:
        info = _CITIES[canonical].copy()
        info["city"] = canonical
        info["avg_5yr_pct"] = get_avg_appreciation(canonical)
        info["national_avg_pct"] = _NATIONAL_AVG
        info["source"] = _SOURCE
        return info
    return None


def list_available_cities() -> list[str]:
    """Return list of available city names."""
    return list(_CITIES.keys())
