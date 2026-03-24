"""Local test script — runs the calculator and opens the HTML card in browser."""

import json
import os
import sys
import tempfile
import webbrowser

sys.path.insert(0, os.path.dirname(__file__))

from core.calculator import compute_rent_vs_buy, format_inr


def test_calculator():
    """Run a sample calculation and print results."""
    print("=" * 60)
    print("Ghar Ya Kiraya — Local Test")
    print("=" * 60)

    result = compute_rent_vs_buy(
        city="Pune",
        property_price=5200000,
        monthly_rent=18000,
        down_payment_pct=20,
        loan_tenure_years=20,
        interest_rate_pct=8.5,
        planning_horizon_years=20,
        rent_escalation_pct=8,
        down_payment_inv_return_pct=8,
    )

    print(f"\nVerdict: {result['verdict']}")
    print(f"Break-even Year: {result['breakeven_year']}")
    print(f"EMI: ₹{format_inr(result['emi'])}")
    print(f"EMI - Rent: ₹{format_inr(result['monthly_delta'])}/mo")
    print(f"\nHorizon Summary ({result['inputs_used']['planning_horizon_years']} years):")
    hs = result['horizon_summary']
    print(f"  Total Rent Paid: ₹{format_inr(hs['total_rent_paid'])}")
    print(f"  Total Buy Cost:  ₹{format_inr(hs['total_buy_cost'])}")
    print(f"  Net Delta:       ₹{format_inr(hs['net_delta'])} {'(buying better)' if hs['net_delta'] > 0 else '(renting better)'}")
    print(f"  Property Value:  ₹{format_inr(hs['property_value_at_horizon'])}")

    print(f"\nCity Appreciation ({result['city_appreciation']['city']}):")
    for fy, pct in result['city_appreciation']['yearly_data'].items():
        print(f"  {fy}: {pct}%")
    print(f"  5yr Avg: {result['city_appreciation']['avg_5yr_pct']}%")

    return result


def open_card_in_browser(result):
    """Inject result into card.html and open in browser."""
    card_path = os.path.join(os.path.dirname(__file__), "ui", "card.html")
    with open(card_path, "r") as f:
        template = f.read()

    data_json = json.dumps(result, ensure_ascii=False)
    html = template.replace("/*__DATA_PLACEHOLDER__*/", data_json)

    # Write to temp file and open
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as tmp:
        tmp.write(html)
        tmp_path = tmp.name

    print(f"\nOpening card in browser: {tmp_path}")
    webbrowser.open("file://" + tmp_path)


if __name__ == "__main__":
    result = test_calculator()
    open_card_in_browser(result)
    print("\nDone! Check your browser for the interactive card.")
