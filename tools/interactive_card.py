"""Tool 4: get_interactive_card — returns URL-based MCP-UI for full card with sliders."""

import json
import os
from typing import Annotated
from urllib.parse import urlencode

from mcp.types import TextContent, EmbeddedResource, TextResourceContents

_BASE_URL = os.environ.get("MCP_BASE_URL", "https://ghar-ya-kiraya-mcp.onrender.com")


def register(mcp):
    @mcp.tool(
        name="get_interactive_card",
        description=(
            "Full interactive card with sliders for what-if exploration. "
            "Call ONLY when user explicitly asks to tune numbers, change rates, or explore scenarios. "
            "Never call on first response."
        ),
    )
    def get_interactive_card(
        property_price: Annotated[int, "Property price in INR"],
        monthly_rent: Annotated[int, "Current monthly rent in INR"],
        city: Annotated[str, "City name"] = "",
        down_payment_pct: Annotated[float, "Down payment percentage"] = 20.0,
        loan_tenure_years: Annotated[int, "Loan tenure in years"] = 20,
        interest_rate_pct: Annotated[float, "Annual interest rate %"] = 8.5,
        planning_horizon_years: Annotated[int, "Planning horizon years"] = 20,
        rent_escalation_pct: Annotated[float, "Annual rent increase %"] = 8.0,
        appreciation_rate_pct: Annotated[float, "Property appreciation %. 0 = auto from city"] = 0.0,
        down_payment_inv_return_pct: Annotated[float, "Return if down payment invested %"] = 8.0,
        stamp_duty_pct: Annotated[float, "Stamp duty percentage"] = 6.0,
        registration_fee: Annotated[int, "Registration fee in INR"] = 30000,
        monthly_maintenance: Annotated[int, "Monthly maintenance in INR"] = 3000,
        property_tax_per_year: Annotated[int, "Annual property tax in INR"] = 8000,
    ) -> list:
        # Build URL for the full interactive card
        params = urlencode({
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
        card_url = f"{_BASE_URL}/demo/card?{params}"

        uri = "ui://ghar-ya-kiraya/interactive-0"
        widget_json = json.dumps({
            "type": "resource",
            "resource": {
                "uri": uri,
                "mimeType": "text/uri-list",
                "text": card_url,
            },
        })

        resource = TextResourceContents(
            uri=uri,
            mimeType="text/uri-list",
            text=widget_json,
            meta={
                "description": "Full interactive card with sliders for what-if rent vs buy scenario exploration.",
                "name": "Interactive Calculator",
            },
        )

        return [
            EmbeddedResource(type="resource", resource=resource),
            TextContent(type="text", text=f"Interactive card rendered for {city or 'property'}. Use sliders to explore scenarios."),
        ]
