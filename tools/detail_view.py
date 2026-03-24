"""Tool 3: get_detail_view — on-demand data views (table, snapshot, hidden costs). ~1-2KB."""

import json
import os
from typing import Annotated

from mcp.types import TextContent, EmbeddedResource, TextResourceContents
from core.calculator import compute_rent_vs_buy

_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "ui", "detail_view.html")
_TEMPLATE = None


def _load_template() -> str:
    global _TEMPLATE
    if _TEMPLATE is None:
        with open(_TEMPLATE_PATH, "r") as f:
            _TEMPLATE = f.read()
    return _TEMPLATE


def register(mcp):
    @mcp.tool(
        name="get_detail_view",
        description=(
            "Returns a lightweight detail view — year-by-year table, monthly snapshot, or hidden costs. "
            "Call when user asks for 'year by year breakdown', 'monthly snapshot', or 'hidden costs'. "
            "No charts, no sliders. Pure HTML tables — very fast."
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

        # Build data payload based on view type
        view_type = view if view in ("yearly_table", "monthly_snapshot", "hidden_costs") else "yearly_table"

        card_data = {
            "view_type": view_type,
            "verdict": result["verdict"],
            "breakeven_year": result["breakeven_year"],
            "inputs_used": result["inputs_used"],
        }

        if view_type == "yearly_table":
            card_data["yearly_series"] = result["yearly_series"]
            brief = f"Year-by-year breakdown for {city or 'property'}: break-even at year {result['breakeven_year'] or 'N/A'}"
        elif view_type == "monthly_snapshot":
            card_data["monthly_snapshot"] = result["monthly_snapshot"]
            brief = f"Monthly snapshot: EMI ₹{result['emi']:,} vs rent ₹{monthly_rent:,}"
        else:
            card_data["hidden_costs"] = result["hidden_costs"]
            brief = "Hidden costs comparison: buying vs renting"

        # Inject into template
        template = _load_template()
        html = template.replace("/*__DATA_PLACEHOLDER__*/{}", json.dumps(card_data, ensure_ascii=False))

        return [
            TextContent(type="text", text=brief),
            EmbeddedResource(
                type="resource",
                resource=TextResourceContents(
                    uri=f"ui://ghar-ya-kiraya/detail/{view_type}",
                    mimeType="text/html",
                    text=html,
                ),
            ),
        ]
