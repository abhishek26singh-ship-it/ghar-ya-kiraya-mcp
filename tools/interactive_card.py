"""Tool 4: get_interactive_card — full card with sliders, charts, hidden costs. ~32KB."""

import json
import os
from typing import Annotated

from mcp.types import TextContent, EmbeddedResource, TextResourceContents
from core.calculator import compute_rent_vs_buy, format_inr

_CARD_PATH = os.path.join(os.path.dirname(__file__), "..", "ui", "card.html")
_CARD_TEMPLATE = None


def _load_card_template() -> str:
    global _CARD_TEMPLATE
    if _CARD_TEMPLATE is None:
        with open(_CARD_PATH, "r") as f:
            _CARD_TEMPLATE = f.read()
    return _CARD_TEMPLATE


def _build_voice_summary(result: dict) -> str:
    """Build a short voice-friendly summary."""
    city = result["inputs_used"]["city"] or "your chosen location"
    price = format_inr(result["inputs_used"]["property_price"])
    emi = format_inr(result["emi"])
    delta = format_inr(abs(result["monthly_delta"]))
    horizon = result["inputs_used"]["planning_horizon_years"]
    be = result["breakeven_year"]
    net = format_inr(abs(result["horizon_summary"]["net_delta"]))
    verdict = result["verdict"]

    if verdict == "BUY":
        return (
            f"{city} mein ₹{price} ke ghar ke liye: EMI hogi ~₹{emi} — "
            f"abhi ke kiraye se ₹{delta} zyada. "
            f"Lekin year {be} ke baad buying financially better ho jaata hai. "
            f"{horizon} saal mein buying se ~₹{net} ka net fayda. "
            f"Neeche sliders se numbers adjust kar sakte ho."
        )
    else:
        return (
            f"{city} mein ₹{price} ke ghar ke liye: EMI hogi ~₹{emi} — "
            f"abhi ke kiraye se ₹{delta} zyada. "
            f"{horizon} saal ke horizon mein renting financially better lag raha hai — "
            f"~₹{net} ka fark. Sliders se explore karo."
        )


def _build_html_card(result: dict) -> str:
    """Inject result data into card.html template."""
    template = _load_card_template()
    data_json = json.dumps(result, ensure_ascii=False)
    return template.replace("/*__DATA_PLACEHOLDER__*/{}", data_json)


def register(mcp):
    @mcp.tool(
        name="get_interactive_card",
        description=(
            "Full interactive card with sliders, hidden costs, charts, city appreciation, "
            "and follow-up buttons. Call ONLY when user wants to tune numbers, explore what-ifs, "
            "or explicitly asks for sliders. Do NOT call on first response."
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
            stamp_duty_pct=stamp_duty_pct,
            registration_fee=registration_fee,
            monthly_maintenance=monthly_maintenance,
            property_tax_per_year=property_tax_per_year,
            appreciation_rate_pct=appreciation_rate_pct,
        )

        voice_summary = _build_voice_summary(result)
        html_card = _build_html_card(result)

        return [
            TextContent(type="text", text=voice_summary),
            EmbeddedResource(
                type="resource",
                resource=TextResourceContents(
                    uri="ui://ghar-ya-kiraya/interactive",
                    mimeType="text/html",
                    text=html_card,
                ),
            ),
        ]
