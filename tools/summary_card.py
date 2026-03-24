"""Tool 2: get_summary_card — lightweight visual card with chart and buttons."""

import json
import os
from typing import Annotated

from mcp.types import TextContent, EmbeddedResource, TextResourceContents
from core.calculator import compute_rent_vs_buy

_CARD_PATH = os.path.join(os.path.dirname(__file__), "..", "ui", "summary_card.html")
_CARD_TEMPLATE = None


def _load_template() -> str:
    global _CARD_TEMPLATE
    if _CARD_TEMPLATE is None:
        with open(_CARD_PATH, "r") as f:
            _CARD_TEMPLATE = f.read()
    return _CARD_TEMPLATE


def register(mcp):
    @mcp.tool(
        name="get_summary_card",
        description=(
            "Returns a lightweight visual card with verdict banner, key stats, crossover chart, "
            "and 4 action buttons. Call this AFTER get_quick_verdict to show the visual summary. "
            "The card loads in ~4KB — no sliders, no tables."
        ),
    )
    def get_summary_card(
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

        # Extract only what the summary card needs
        card_data = {
            "verdict": result["verdict"],
            "verdict_text": result["verdict_text"],
            "breakeven_year": result["breakeven_year"],
            "emi": result["emi"],
            "monthly_delta": result["monthly_delta"],
            "yearly_series": result["yearly_series"],
            "horizon_summary": result["horizon_summary"],
            "inputs_used": result["inputs_used"],
        }

        # Inject data into template
        template = _load_template()
        html = template.replace("/*__DATA_PLACEHOLDER__*/{}", json.dumps(card_data, ensure_ascii=False))

        # Brief text summary for LLM context
        summary = {
            "verdict": result["verdict"],
            "breakeven_year": result["breakeven_year"],
            "horizon_summary": result["horizon_summary"],
        }

        return [
            TextContent(type="text", text=json.dumps(summary, ensure_ascii=False)),
            EmbeddedResource(
                type="resource",
                resource=TextResourceContents(
                    uri="ui://ghar-ya-kiraya/summary",
                    mimeType="text/html",
                    text=html,
                ),
            ),
        ]
