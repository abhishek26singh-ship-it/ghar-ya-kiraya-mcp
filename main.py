"""Ghar Ya Kiraya — Rent vs Buy MCP Server."""

import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from fastmcp import FastMCP

mcp = FastMCP(
    "ghar-ya-kiraya",
    instructions=(
        "You are a friendly financial guide helping Indian users decide between renting and buying a home. "
        "Use the calculate_rent_vs_buy tool to run the full comparison. "
        "Use get_city_appreciation for NHB RESIDEX data. "
        "Use get_avg_rent_for_city when the user doesn't know their rent. "
        "Always match the user's language (Hindi/English/Hinglish). "
        "Never recommend specific banks or lenders. "
        "Show assumptions transparently."
    ),
)

# Register all tools
from tools.calculate import register as register_calculate
from tools.city_appreciation import register as register_city_appreciation
from tools.avg_rent import register as register_avg_rent

register_calculate(mcp)
register_city_appreciation(mcp)
register_avg_rent(mcp)

# ASGI app — MCP endpoint + demo page
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route, Mount

_DEMO_PATH = os.path.join(os.path.dirname(__file__), "demo.html")


async def homepage(request):
    with open(_DEMO_PATH, "r") as f:
        return HTMLResponse(f.read())


async def health(request):
    return JSONResponse({"status": "ok", "server": "ghar-ya-kiraya"})


async def demo_card(request):
    """Render the calculator card directly as HTML — used by demo page iframe."""
    from core.calculator import compute_rent_vs_buy
    from tools.calculate import _build_html_card, _build_voice_summary

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
