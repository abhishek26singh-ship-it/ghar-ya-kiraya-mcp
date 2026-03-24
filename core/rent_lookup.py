from core.city_lookup import normalise_city, _CITIES, _SOURCE

_BHK_MULTIPLIER = {1: 0.65, 2: 1.0, 3: 1.5}


def get_avg_rent(city: str, bhk: int = 2) -> dict | None:
    """Return average monthly rent for a city and BHK type."""
    canonical = normalise_city(city)
    if not canonical or canonical not in _CITIES:
        return None
    base_rent = _CITIES[canonical].get("avg_rent_2bhk")
    if not base_rent:
        return None
    multiplier = _BHK_MULTIPLIER.get(bhk, 1.0)
    return {
        "city": canonical,
        "bhk": bhk,
        "avg_monthly_rent": int(base_rent * multiplier),
        "source": "seeded",
        "note": f"Estimated average {bhk}BHK rent in {canonical} (based on market data)",
    }
