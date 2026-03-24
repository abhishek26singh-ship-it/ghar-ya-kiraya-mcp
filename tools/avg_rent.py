"""MCP tool: get_avg_rent_for_city."""

from typing import Annotated

from core.rent_lookup import get_avg_rent
from core.city_lookup import list_available_cities


def register(mcp):
    @mcp.tool(
        name="get_avg_rent_for_city",
        description=(
            "Returns estimated average monthly rent for an Indian city. "
            "Useful when the user doesn't currently pay rent and needs a baseline figure."
        ),
    )
    def get_avg_rent_for_city(
        city: Annotated[str, "City name (e.g. Mumbai, Pune, Bangalore)"],
        bhk: Annotated[int, "BHK type: 1, 2, or 3. Default is 2."] = 2,
    ) -> dict:
        result = get_avg_rent(city, bhk=bhk)
        if not result:
            return {
                "error": f"No rent data for '{city}'",
                "available_cities": list_available_cities(),
                "tip": "Try one of the available cities listed above.",
            }
        return result
