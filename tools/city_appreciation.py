"""MCP tool: get_city_appreciation."""

from typing import Annotated

from core.city_lookup import get_city_info, list_available_cities


def register(mcp):
    @mcp.tool(
        name="get_city_appreciation",
        description=(
            "Returns NHB RESIDEX property appreciation data for an Indian city. "
            "Includes 5-year yearly data (FY21-FY25), 5-year average, and national average."
        ),
    )
    def get_city_appreciation(
        city: Annotated[str, "City name (e.g. Mumbai, Pune, Bangalore, Hyderabad)"],
    ) -> dict:
        info = get_city_info(city)
        if not info:
            return {
                "error": f"No RESIDEX data for '{city}'",
                "available_cities": list_available_cities(),
                "tip": "Try one of the available cities listed above.",
            }
        return {
            "city": info["city"],
            "avg_5yr_pct": info["avg_5yr_pct"],
            "yearly_data": info["appreciation"],
            "national_avg_pct": info["national_avg_pct"],
            "source": info["source"],
        }
