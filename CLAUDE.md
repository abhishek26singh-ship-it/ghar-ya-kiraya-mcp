# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ghar Ya Kiraya is a Python MCP (Model Context Protocol) server that helps Indian users decide between renting and buying a home. It runs as a FastMCP + Starlette ASGI app with dual MCP transports and serves interactive HTML UI cards for the JBIQ partner platform.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server locally (http://localhost:8000, MCP at /mcp)
python main.py

# Test the calculator and open interactive card in browser
python test_local.py
```

There is no linter, formatter, or test suite configured beyond `test_local.py`.

## Ground Rules (MUST follow for all changes)

### Tool Return Contract

Every UI tool MUST return both content blocks in a single response, in this order:
1. **`EmbeddedResource`** — card URL for visual rendering in JBIQ WebView. **MUST be first.**
2. **`TextContent`** — concise voice-friendly summary (2-3 sentences with key numbers). This is what the LLM speaks/narrates. NOT raw JSON.

Data-lookup tools (no UI) return text-only (dict or TextContent).

### MCP-UI Format (JBIQ Standard)

Match the exact wire format used by aicore-jiomart-mcp-service (verified working on JBIQ via Langfuse):
- **MIME type**: `text/uri-list` (this is what JBIQ expects for external URL resources)
- **`meta`**: Must include `description` and `name` — pass via `meta=` constructor kwarg (NOT `.meta =` assignment)
- **URI scheme**: `ui://ghar-ya-kiraya/{component}-{index}` (e.g. `ui://ghar-ya-kiraya/summary-0`)
- **Content order**: EmbeddedResource FIRST, TextContent SECOND (matches JioMart)
- **Pydantic note**: `meta=` in constructor stores as Pydantic extra field → serializes as `meta` on wire (matching JioMart). Do NOT use `.meta =` assignment which serializes as `_meta`.

### Performance

- Each tool response MUST complete in < 2 seconds
- `compute_rent_vs_buy()` takes ~100ms — well within budget
- Tools build URLs; heavy compute happens server-side when WebView fetches the URL

### Self-Contained Tools (not progressive)

Each tool is self-contained — returns everything (text + UI) in one call. The LLM does NOT need to chain multiple tools for a single response. This follows the JBIQ standard pattern (reference: aicore-jiomart-mcp-service).

## Architecture

### 5-Tool Layout

1. **`get_verdict_card`** — primary entry point. Returns voice summary (TextContent) + visual summary card URL (EmbeddedResource). Handles auto-rent resolution (monthly_rent=0 → fetch city average).
2. **`get_detail_view`** — year-by-year / monthly snapshot / hidden costs. Returns brief text + detail card URL.
3. **`get_interactive_card`** — full card with sliders for what-if scenarios. Returns brief text + interactive card URL. Never on first response.
4. **`get_city_appreciation`** — NHB RESIDEX data lookup (text-only, no UI).
5. **`get_avg_rent_for_city`** — city average rent lookup (text-only, no UI).

### Module Layout

- **`main.py`** — ASGI entry point. Creates the FastMCP instance with LLM instructions, registers all 5 tools, defines HTTP routes, mounts dual transports (`/mcp` streamable-http + `/sse` legacy SSE).
- **`core/calculator.py`** — Financial engine. `compute_rent_vs_buy()` runs a year-by-year simulation. `build_voice_summary()` generates concise Hinglish voice text from a result dict.
- **`core/city_lookup.py`** — Loads `data/residex.json`, handles city name normalization with aliases (Bombay→Mumbai, etc.), returns NHB RESIDEX appreciation rates.
- **`core/rent_lookup.py`** — BHK-based rent estimation using seeded market data.
- **`tools/`** — Each file exports a `register(mcp)` function that adds one MCP tool. UI tools return `list[TextContent, EmbeddedResource]` with `text/html;profile=mcp-app` MIME pointing to `/demo/*` endpoints.
- **`ui/`** — Three HTML templates (`card.html`, `summary_card.html`, `detail_view.html`) using vanilla JS + Chart.js. Data is injected via `/*__DATA_PLACEHOLDER__*/{}` replacement. Templates include JBIQ WebView integration (postMessage protocol for height reporting, theme detection, prompt triggers).
- **`data/residex.json`** — NHB RESIDEX HPI data for 12 cities (FY21-FY25) plus average 2BHK rents.

### Key Patterns

- **Tool registration**: Each tool file in `tools/` exports `register(mcp)` which is called in `main.py`. Tools use `@mcp.tool()` decorator.
- **Currency formatting**: `core/calculator.py` has `format_inr()` (₹X.XL / ₹X.XCr) and `format_inr_comma()` for Indian number formatting.
- **Voice summary**: `core/calculator.py` has `build_voice_summary()` — takes a `compute_rent_vs_buy()` result and returns 2-3 sentence Hinglish summary.
- **UI data injection**: HTML templates use `/*__DATA_PLACEHOLDER__*/{}` as a JSON injection point, replaced server-side before serving.
- **Demo routes** (`/demo/card`, `/demo/summary`, `/demo/detail`): Parse query params, run `compute_rent_vs_buy()`, inject result into HTML templates. These URLs are what the MCP tools return to clients.
- **Auto-rent resolution**: `get_verdict_card` accepts `monthly_rent=0` and auto-fetches city average rent via `get_avg_rent()`. Fallback: ₹18,000.

### Defaults (in `core/calculator.py`)

Interest rate 8.5%, tenure 20yr, rent escalation 8%, stamp duty 6%, maintenance ₹3K/mo, property tax ₹8K/yr, registration ₹30K, investment return 8%.

## Deployment

Docker-based on Render (see `render.yaml` and `Dockerfile`). The `MCP_BASE_URL` env var sets the base URL for tool-returned card URLs. Health check at `/health`.

## Supported Cities

12 cities with NHB RESIDEX data: Mumbai, Pune, Bengaluru, Delhi, Hyderabad, Chennai, Kolkata, Ahmedabad, Jaipur, Lucknow, Kochi, Kanpur. Aliases map common variants (Bangalore, Bombay, Noida, Gurgaon, etc.).
