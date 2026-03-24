"""Ghar Ya Kiraya — Rent vs Buy MCP Server (Progressive 4-tool architecture)."""

import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from fastmcp import FastMCP

mcp = FastMCP(
    "ghar-ya-kiraya",
    instructions=(
        "You are a friendly financial guide helping Indian users decide between renting and buying a home. "
        "Match the user's language — Hindi, English, or Hinglish. Be brief.\n\n"
        "TOOL CALLING ORDER — follow exactly:\n"
        "1. Call get_quick_verdict first → speak the voice_summary immediately (3 sentences max)\n"
        "2. Call get_summary_card in same turn → renders chart card with 4 buttons\n"
        "3. End with one sentence surfacing the defaults used (rent, down payment, city appreciation)\n\n"
        "When user taps buttons or asks follow-ups:\n"
        "- 'Year-by-year' / 'monthly snapshot' / 'hidden costs' → call get_detail_view with view param\n"
        "- 'Tune numbers' / 'what if' / slider requests → call get_interactive_card\n"
        "- Different city/price → re-call get_quick_verdict + get_summary_card\n\n"
        "Use get_city_appreciation for NHB RESIDEX data.\n"
        "Use get_avg_rent_for_city when user doesn't know their rent.\n"
        "Never call get_interactive_card on first response.\n"
        "Never recommend specific banks or lenders.\n"
        "2 sentences max on follow-up voice responses."
    ),
)

# Register all 6 tools
from tools.quick_verdict import register as register_quick_verdict
from tools.summary_card import register as register_summary_card
from tools.detail_view import register as register_detail_view
from tools.interactive_card import register as register_interactive_card
from tools.city_appreciation import register as register_city_appreciation
from tools.avg_rent import register as register_avg_rent

register_quick_verdict(mcp)
register_summary_card(mcp)
register_detail_view(mcp)
register_interactive_card(mcp)
register_city_appreciation(mcp)
register_avg_rent(mcp)

# ASGI app — MCP endpoint + demo page + health
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route, Mount

_DEMO_PATH = os.path.join(os.path.dirname(__file__), "demo.html")


async def homepage(request):
    with open(_DEMO_PATH, "r") as f:
        return HTMLResponse(f.read())


async def health(request):
    return JSONResponse({"status": "ok", "server": "ghar-ya-kiraya", "tools": 6})


async def demo_card(request):
    """Render the full interactive card — used by demo page."""
    from core.calculator import compute_rent_vs_buy
    from tools.interactive_card import _build_html_card, _build_voice_summary

    params = dict(request.query_params)
    result = compute_rent_vs_buy(
        city=params.get("city", "Pune"),
        property_price=int(params.get("property_price", 5200000)),
        monthly_rent=int(params.get("monthly_rent", 18000)),
        down_payment_pct=float(params.get("down_payment_pct", 20)),
        loan_tenure_years=int(params.get("loan_tenure_years", 20)),
        interest_rate_pct=float(params.get("interest_rate_pct", 8.5)),
        planning_horizon_years=int(params.get("planning_horizon_years", 20)),
        rent_escalation_pct=float(params.get("rent_escalation_pct", 8)),
        appreciation_rate_pct=float(params.get("appreciation_rate_pct", 0)),
        down_payment_inv_return_pct=float(params.get("down_payment_inv_return_pct", 8)),
    )
    result["_voice_summary"] = _build_voice_summary(result)
    html = _build_html_card(result)
    return HTMLResponse(html)


_mcp_app = mcp.http_app(path="/mcp")

starlette_app = Starlette(
    routes=[
        Route("/", homepage),
        Route("/health", health),
        Route("/demo/card", demo_card),
        Mount("/", app=_mcp_app),
    ],
    lifespan=_mcp_app.lifespan,
)
app = starlette_app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
