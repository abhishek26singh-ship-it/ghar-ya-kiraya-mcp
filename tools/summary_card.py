"""Tool: get_verdict_card — primary rent vs buy tool returning text + UI card."""

import os
from typing import Annotated
from urllib.parse import urlencode

from mcp.types import TextContent, EmbeddedResource, TextResourceContents
from core.calculator import compute_rent_vs_buy, build_voice_summary
from core.rent_lookup import get_avg_rent

_BASE_URL = os.environ.get("MCP_BASE_URL", "https://ghar-ya-kiraya-mcp.onrender.com")


def register(mcp):
    @mcp.tool(
        name="get_verdict_card",
        description=(
            "MUST be called FIRST for any rent-vs-buy query. Returns a voice-friendly verdict "
            "(speak it immediately) and a visual summary card with chart and action buttons. "
            "Pass monthly_rent=0 to auto-fetch city average rent. Fast: under 200ms."
        ),
    )
    def get_verdict_card(
        property_price: Annotated[int, "Property price in INR"],
        monthly_rent: Annotated[int, "Current monthly rent in INR. Pass 0 to auto-fetch city average."] = 0,
        city: Annotated[str, "City name (e.g. Mumbai, Pune, Bengaluru)"] = "",
        down_payment_pct: Annotated[float, "Down payment percentage"] = 20.0,
        loan_tenure_years: Annotated[int, "Loan tenure in years"] = 20,
        interest_rate_pct: Annotated[float, "Annual interest rate %"] = 8.5,
        planning_horizon_years: Annotated[int, "Planning horizon years"] = 20,
        rent_escalation_pct: Annotated[float, "Annual rent increase %"] = 8.0,
        appreciation_rate_pct: Annotated[float, "Property appreciation %. 0 = auto from city data"] = 0.0,
        down_payment_inv_return_pct: Annotated[float, "Return if down payment invested instead %"] = 8.0,
    ) -> list:
        # --- Auto-resolve rent if not provided ---
        rent_value = monthly_rent
        if rent_value <= 0 and city:
            rent_data = get_avg_rent(city)
            if rent_data and "avg_monthly_rent" in rent_data:
                rent_value = rent_data["avg_monthly_rent"]
        if rent_value <= 0:
            rent_value = 18000  # national fallback

        # --- Full computation ---
        result = compute_rent_vs_buy(
            city=city,
            property_price=property_price,
            monthly_rent=rent_value,
            down_payment_pct=down_payment_pct,
            loan_tenure_years=loan_tenure_years,
            interest_rate_pct=interest_rate_pct,
            planning_horizon_years=planning_horizon_years,
            rent_escalation_pct=rent_escalation_pct,
            down_payment_inv_return_pct=down_payment_inv_return_pct,
            appreciation_rate_pct=appreciation_rate_pct,
        )

        # --- Voice summary (text block for LLM to speak) ---
        voice_summary = build_voice_summary(result)

        # --- Build card URL (JBIQ WebView fetches this) ---
        params = urlencode({
            "city": city,
            "property_price": property_price,
            "monthly_rent": rent_value,
            "down_payment_pct": down_payment_pct,
            "loan_tenure_years": loan_tenure_years,
            "interest_rate_pct": interest_rate_pct,
            "planning_horizon_years": planning_horizon_years,
            "rent_escalation_pct": rent_escalation_pct,
            "appreciation_rate_pct": appreciation_rate_pct,
            "down_payment_inv_return_pct": down_payment_inv_return_pct,
        })
        card_url = f"{_BASE_URL}/demo/summary?{params}"

        resource = TextResourceContents(
            uri="ui://ghar-ya-kiraya/summary-0",
            mimeType="text/uri-list",
            text=card_url,
            meta={
                "description": "Visual summary card showing rent vs buy verdict with chart and action buttons.",
                "name": "Verdict Card",
            },
        )

        return [
            EmbeddedResource(type="resource", resource=resource),
            TextContent(type="text", text=voice_summary),
        ]
