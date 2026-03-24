"""Main MCP tool: calculate_rent_vs_buy."""

import json
import os
from typing import Annotated

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
            f"Neeche dekho poora picture."
        )
    else:
        return (
            f"{city} mein ₹{price} ke ghar ke liye: EMI hogi ~₹{emi} — "
            f"abhi ke kiraye se ₹{delta} zyada. "
            f"{horizon} saal ke horizon mein renting financially better lag raha hai — "
            f"~₹{net} ka fark. Neeche dekho full analysis."
        )


def _build_html_card(result: dict) -> str:
    """Inject result data into card.html template."""
    template = _load_card_template()
    data_json = json.dumps(result, ensure_ascii=False)
    return template.replace("/*__DATA_PLACEHOLDER__*/{}", data_json)


def register(mcp):
    @mcp.tool(
        name="calculate_rent_vs_buy",
        description=(
            "Compare renting vs buying a home in India. "
            "Returns verdict, break-even year, yearly cost series, hidden costs, "
            "and an interactive MCP-UI card with charts and sliders. "
            "All computation is server-side."
        ),
    )
    def calculate_rent_vs_buy(
        property_price: Annotated[int, "Property price in INR (e.g. 5200000 for 52 lakh)"],
        monthly_rent: Annotated[int, "Current monthly rent in INR"],
        city: Annotated[str, "City name (e.g. Mumbai, Pune, Bangalore)"] = "",
        down_payment_pct: Annotated[float, "Down payment as percentage of property price"] = 20.0,
        loan_tenure_years: Annotated[int, "Loan tenure in years"] = 20,
        interest_rate_pct: Annotated[float, "Annual home loan interest rate percentage"] = 8.5,
        planning_horizon_years: Annotated[int, "How many years to compare over"] = 20,
        rent_escalation_pct: Annotated[float, "Annual rent increase percentage"] = 8.0,
        appreciation_rate_pct: Annotated[float, "Annual property appreciation %. Set 0 to auto-detect from city data"] = 0.0,
        down_payment_inv_return_pct: Annotated[float, "Expected annual return if down payment was invested instead"] = 8.0,
        stamp_duty_pct: Annotated[float, "Stamp duty percentage"] = 6.0,
        registration_fee: Annotated[int, "Registration fee in INR"] = 30000,
        monthly_maintenance: Annotated[int, "Monthly maintenance cost in INR"] = 3000,
        property_tax_per_year: Annotated[int, "Annual property tax in INR"] = 8000,
    ) -> str:
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

        # Return structured result with UI card
        output = {
            **result,
            "_voice_summary": voice_summary,
            "_ui_html": html_card,
        }
        return json.dumps(output, ensure_ascii=False)
