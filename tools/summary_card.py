"""Tool 2: get_verdict_card — returns URL-based MCP-UI card for JBIQ WebView."""

import os
from typing import Annotated
from urllib.parse import urlencode

from mcp.types import TextContent, EmbeddedResource, TextResourceContents
from core.calculator import compute_rent_vs_buy

_BASE_URL = os.environ.get("MCP_BASE_URL", "https://ghar-ya-kiraya-mcp.onrender.com")


def register(mcp):
    @mcp.tool(
        name="get_verdict_card",
        description=(
            "Call AFTER get_quick_verdict. Returns a visual card rendered in the chat. "
            "Do NOT narrate or describe the card contents — the card speaks for itself. "
            "Just let it render silently."
        ),
    )
    def get_verdict_card(
        property_price: Annotated[int, "Property price in INR"],
        monthly_rent: Annotated[int, "Current monthly rent in INR"],
        city: Annotated[str, "City name"] = "",
        down_payment_pct: Annotated[float, "Down payment percentage"] = 20.0,
        loan_tenure_years: Annotated[int, "Loan tenure in years"] = 20,
        interest_rate_pct: Annotated[float, "Annual interest rate %"] = 8.5,
        planning_horizon_years: Annotated[int, "Planning horizon years"] = 20,
        rent_escalation_pct: Annotated[float, "Annual rent increase %"] = 8.0,
        appreciation_rate_pct: Annotated[float, "Property appreciation %. 0 = auto from city data"] = 0.0,
        down_payment_inv_return_pct: Annotated[float, "Return if down payment invested instead %"] = 8.0,
    ) -> list:
        # Quick compute just for the verdict_text fallback
        result = compute_rent_vs_buy(
            city=city,
            property_price=property_price,
            monthly_rent=monthly_rent,
            down_payment_pct=down_payment_pct,
            loan_tenure_years=loan_tenure_years,
            interest_rate_pct=interest_rate_pct,
            planning_horizon_years=planning_horizon_years,
            rent_escalation_pct=rent_escalation_pct,
            down_payment_inv_return_pct=down_payment_inv_return_pct,
            appreciation_rate_pct=appreciation_rate_pct,
        )

        city_name = result["inputs_used"].get("city", city or "your city")
        verdict_text = result.get("verdict_text", "")

        # Build URL for the card — JBIQ WebView will fetch this
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
        card_url = f"{_BASE_URL}/demo/summary?{params}"

        return [
            TextContent(type="text", text=f"Card rendered for {city_name}. {verdict_text}"),
            EmbeddedResource(
                type="resource",
                resource=TextResourceContents(
                    uri="ui://ghar-ya-kiraya/summary",
                    mimeType="text/uri-list",
                    text=card_url,
                ),
            ),
        ]
