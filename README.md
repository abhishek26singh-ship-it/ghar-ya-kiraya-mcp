# Ghar Ya Kiraya — Rent vs Buy MCP Server

A public MCP server that helps Indian users decide between renting and buying a home. Returns an interactive MCP-UI card with charts, sliders, and financial analysis.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py
# Server starts at http://localhost:8000, MCP endpoint at /mcp

# Test the calculator (opens interactive card in browser)
python test_local.py
```

## MCP Tools

### 1. `calculate_rent_vs_buy`
Main calculator — compares renting vs buying over a planning horizon.

**Required inputs:**
- `property_price` (int): Property price in INR
- `monthly_rent` (int): Current monthly rent in INR

**Optional inputs (with smart defaults):**
- `city` (str): City name for auto-appreciation lookup
- `down_payment_pct` (float): Default 20%
- `loan_tenure_years` (int): Default 20
- `interest_rate_pct` (float): Default 8.5%
- `planning_horizon_years` (int): Default 20
- `rent_escalation_pct` (float): Default 8%
- `appreciation_rate_pct` (float): Default auto from city data
- `down_payment_inv_return_pct` (float): Default 8%

**Returns:** Verdict, break-even year, yearly cost series, hidden costs, monthly snapshot, and an interactive HTML card.

### 2. `get_city_appreciation`
Returns NHB RESIDEX property appreciation data for a city (FY21-FY25).

### 3. `get_avg_rent_for_city`
Returns estimated average monthly rent for a city (1/2/3 BHK).

## Supported Cities
Mumbai, Pune, Bengaluru, Delhi, Hyderabad, Chennai, Kolkata, Ahmedabad, Jaipur, Lucknow, Kochi, Kanpur

City aliases supported: Bombay, Poona, Bangalore, Madras, Calcutta, Noida, Gurgaon, etc.

## Deploy to Render

1. Push this repo to GitHub
2. Connect the repo on [Render](https://render.com)
3. It auto-deploys using the Dockerfile
4. MCP endpoint: `https://your-app.onrender.com/mcp`

## JBIQ Partner Platform Integration

**Skill Name:** `ghar-ya-kiraya`

**Trigger Phrases:**
- ghar lena chahiye ya kiraya
- rent vs buy
- EMI vs kiraya
- should I buy a house
- rent or buy calculator

**MCP Endpoint:** `https://your-app.onrender.com/mcp`

## Data Sources
- Property appreciation: NHB RESIDEX HPI @ Assessment Prices, Q4 FY2024-25
- Average rents: Seeded market estimates for 12 cities
