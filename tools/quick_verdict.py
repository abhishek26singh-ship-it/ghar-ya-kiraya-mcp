"""Tool 1: get_quick_verdict — instant rent vs buy verdict. <5ms, ~500B response."""

from typing import Annotated
from core.calculator import compute_quick_verdict


def register(mcp):
    @mcp.tool(
        name="get_quick_verdict",
        description=(
            "Fast rent-vs-buy verdict for an Indian city. Returns verdict, break-even year, "
            "EMI, monthly delta, and voice summaries in Hindi and English. "
            "Call this FIRST — the LLM should speak the voice_summary immediately. "
            "If monthly_rent is 0, auto-fetches city average rent."
        ),
    )
    def get_quick_verdict(
        city: Annotated[str, "City name (e.g. Mumbai, Pune, Bengaluru)"],
        property_price: Annotated[int, "Property price in INR (e.g. 8000000 for 80 lakh)"],
        monthly_rent: Annotated[int, "Current monthly rent in INR. Pass 0 to auto-fetch city average."] = 0,
        down_payment_pct: Annotated[float, "Down payment as percentage of property price"] = 20.0,
    ) -> dict:
        return compute_quick_verdict(city, property_price, monthly_rent, down_payment_pct)
