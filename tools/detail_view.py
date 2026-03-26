"""Tool 3: get_detail_view — returns URL-based MCP-UI for detail views."""

import os
from typing import Annotated
from urllib.parse import urlencode

from mcp.types import TextContent, EmbeddedResource, TextResourceContents

_BASE_URL = os.environ.get("MCP_BASE_URL", "https://ghar-ya-kiraya-mcp.onrender.com")


def register(mcp):
    @mcp.tool(
        name="get_detail_view",
        description=(
            "Returns a detail view (year-by-year table, monthly snapshot, or hidden costs). "
            "Call when user asks for breakdowns or details. "
            "Pass view='yearly_table', 'monthly_snapshot', or 'hidden_costs'."
        ),
    )
    def get_detail_view(
        property_price: Annotated[int, "Property price in INR"],
        monthly_rent: Annotated[int, "Current monthly rent in INR"],
        view: Annotated[str, "View type: 'yearly_table', 'monthly_snapshot', or 'hidden_costs'"] = "yearly_table",
        city: Annotated[str, "City name"] = "",
        down_payment_pct: Annotated[float, "Down payment percentage"] = 20.0,
        loan_tenure_years: Annotated[int, "Loan tenure in years"] = 20,
        interest_rate_pct: Annotated[float, "Annual interest rate %"] = 8.5,
        planning_horizon_years: Annotated[int, "Planning horizon years"] = 20,
        rent_escalation_pct: Annotated[float, "Annual rent increase %"] = 8.0,
        appreciation_rate_pct: Annotated[float, "Property appreciation %. 0 = auto"] = 0.0,
        down_payment_inv_return_pct: Annotated[float, "Return if down payment invested %"] = 8.0,
    ) -> list:
        view_type = view if view in ("yearly_table", "monthly_snapshot", "hidden_costs") else "yearly_table"

        # Build URL for the detail card
        params = urlencode({
            "view": view_type,
            "city": city,
            "property_price": property_price,
            "monthly_rent": monthly_rent,
            "down_payment_pct": down_payment_pct,
            "loan_tenure_years": loan_tenure_years,
            "interest_rate_pct": interest_rate_pct,
            "planning_horizon_years": planning_horizon_years,
            "rent_escalation_pct": rent_escalation_pct,
            "appreciation_rate_pct": appreciation_rate_pct,
            "down_payment_inv_return_pct": down_payment_inv_return_pct,
        })
        card_url = f"{_BASE_URL}/demo/detail?{params}"

        view_labels = {
            "yearly_table": "Year-by-year breakdown",
            "monthly_snapshot": "Monthly snapshot",
            "hidden_costs": "Hidden costs comparison",
        }
        brief = f"{view_labels.get(view_type, view_type)} rendered for {city or 'property'}."

        resource = TextResourceContents(
            uri=f"ui://ghar-ya-kiraya/detail/{view_type}-0",
            mimeType="text/uri-list",
            text=card_url,
            meta={
                "description": f"{view_labels.get(view_type, view_type)} showing detailed rent vs buy cost analysis.",
                "name": view_labels.get(view_type, "Detail View"),
            },
        )

        return [
            EmbeddedResource(type="resource", resource=resource),
            TextContent(type="text", text=brief),
        ]
