"""Financial engine for Rent vs Buy comparison."""

from core.city_lookup import get_avg_appreciation, get_city_info
from core.rent_lookup import get_avg_rent

# Shared default constants
DEFAULT_INTEREST_RATE = 8.5
DEFAULT_TENURE_YEARS = 20
DEFAULT_RENT_ESCALATION = 8.0
DEFAULT_STAMP_DUTY_PCT = 6.0
DEFAULT_MAINTENANCE_MONTHLY = 3000
DEFAULT_PROPERTY_TAX_YEARLY = 8000
DEFAULT_REGISTRATION_FEE = 30000
DEFAULT_INV_RETURN = 8.0


def format_inr(amount: float) -> str:
    """Format amount in Indian notation: 12.5L or 1.2Cr."""
    abs_amt = abs(amount)
    sign = "-" if amount < 0 else ""
    if abs_amt >= 1_00_00_000:
        return f"{sign}{abs_amt / 1_00_00_000:.1f}Cr"
    if abs_amt >= 1_00_000:
        return f"{sign}{abs_amt / 1_00_000:.1f}L"
    if abs_amt >= 1000:
        return f"{sign}{abs_amt / 1000:.0f}K"
    return f"{sign}{abs_amt:.0f}"


def format_inr_comma(amount: int) -> str:
    """Format with Indian comma system: 12,50,000."""
    if amount < 0:
        return "-" + format_inr_comma(-amount)
    s = str(int(amount))
    if len(s) <= 3:
        return s
    last3 = s[-3:]
    rest = s[:-3]
    parts = []
    while rest:
        parts.append(rest[-2:] if len(rest) >= 2 else rest)
        rest = rest[:-2]
    parts.reverse()
    return ",".join(parts) + "," + last3


def compute_emi(principal: float, annual_rate_pct: float, tenure_years: int) -> float:
    """Compute monthly EMI using standard formula."""
    if principal <= 0 or tenure_years <= 0:
        return 0.0
    if annual_rate_pct <= 0:
        return principal / (tenure_years * 12)
    r = annual_rate_pct / 100 / 12
    n = tenure_years * 12
    emi = principal * r * (1 + r) ** n / ((1 + r) ** n - 1)
    return round(emi, 0)


def compute_rent_vs_buy(
    city: str = "",
    property_price: int = 0,
    monthly_rent: int = 0,
    down_payment_pct: float = 20.0,
    loan_tenure_years: int = 20,
    interest_rate_pct: float = 8.5,
    planning_horizon_years: int = 20,
    rent_escalation_pct: float = 8.0,
    down_payment_inv_return_pct: float = 8.0,
    stamp_duty_pct: float = 6.0,
    registration_fee: int = 30000,
    monthly_maintenance: int = 3000,
    property_tax_per_year: int = 8000,
    appreciation_rate_pct: float = 0.0,
) -> dict:
    """Run the full rent vs buy comparison and return structured result."""

    # Resolve appreciation rate
    if appreciation_rate_pct <= 0 and city:
        appreciation_rate_pct = get_avg_appreciation(city)
    if appreciation_rate_pct <= 0:
        appreciation_rate_pct = 7.5  # national fallback

    # Cap down payment
    if down_payment_pct > 100:
        down_payment_pct = 100.0
    if down_payment_pct < 0:
        down_payment_pct = 0.0

    down_payment = property_price * down_payment_pct / 100
    loan_amount = property_price - down_payment
    stamp_duty = property_price * stamp_duty_pct / 100

    emi = compute_emi(loan_amount, interest_rate_pct, loan_tenure_years)

    # Flag low down payment
    low_dp_warning = None
    if down_payment_pct < 10 and down_payment_pct > 0:
        low_dp_warning = "Down payment is below 10% — banks usually prefer at least 20%."

    # Year-by-year simulation
    yearly_series = []
    cum_buy_outflow = stamp_duty + registration_fee + down_payment  # total cash out for buying
    cum_rent = 0.0
    break_even_year = None

    appr_rate = appreciation_rate_pct / 100
    rent_esc = rent_escalation_pct / 100
    inv_rate = down_payment_inv_return_pct / 100

    for year in range(1, planning_horizon_years + 1):
        # Buy: annual outflow
        if year <= loan_tenure_years:
            buy_annual = emi * 12
        else:
            buy_annual = 0
        buy_annual += monthly_maintenance * 12 + property_tax_per_year
        cum_buy_outflow += buy_annual

        # Appreciation gain (asset value minus original price)
        property_value = property_price * (1 + appr_rate) ** year
        appreciation_gain = property_value - property_price

        # Net buy cost = total cash out - appreciation gained
        net_buy_cost = cum_buy_outflow - appreciation_gain

        # Rent: annual cost with escalation
        rent_this_year_monthly = monthly_rent * (1 + rent_esc) ** (year - 1)
        rent_annual = rent_this_year_monthly * 12
        cum_rent += rent_annual

        # Invest scenario: down payment compounding
        invest_corpus = down_payment * (1 + inv_rate) ** year
        invest_gain = invest_corpus - down_payment
        net_rent_invest = cum_rent - invest_gain

        # Check break-even
        if break_even_year is None and net_buy_cost < cum_rent:
            break_even_year = year

        yearly_series.append({
            "year": year,
            "monthly_rent_that_year": round(rent_this_year_monthly),
            "cumulative_rent_cost": round(cum_rent),
            "cumulative_buy_cost": round(net_buy_cost),
            "invest_corpus_gain": round(invest_gain),
            "net_rent_invest_cost": round(net_rent_invest),
            "property_value": round(property_value),
            "better": "BUY" if net_buy_cost < cum_rent else "RENT",
        })

    # Final year values
    final = yearly_series[-1] if yearly_series else {}
    total_rent = final.get("cumulative_rent_cost", 0)
    total_buy = final.get("cumulative_buy_cost", 0)
    net_delta = total_rent - total_buy  # positive = buying is better

    # Total interest paid over loan tenure
    effective_tenure = min(loan_tenure_years, planning_horizon_years)
    total_interest = (emi * effective_tenure * 12) - loan_amount if loan_amount > 0 else 0

    # Verdict
    if break_even_year is not None and break_even_year <= planning_horizon_years:
        verdict = "BUY"
        verdict_text = (
            f"{city or 'This property'} mein ghar khareedna {planning_horizon_years} saal mein financially better hai. "
            f"Break-even year {break_even_year} mein aa jaata hai."
        )
    else:
        verdict = "RENT"
        verdict_text = (
            f"{planning_horizon_years} saal ke horizon mein, kiraya dena financially better lag raha hai. "
            f"Buying ka break-even nahi aa raha is timeframe mein."
        )

    # Monthly snapshot
    monthly_snapshot = {
        "current_rent": monthly_rent,
        "emi": round(emi),
        "monthly_delta": round(emi - monthly_rent),
        "stamp_duty": round(stamp_duty),
        "registration": registration_fee,
        "maintenance": monthly_maintenance,
        "property_tax_monthly": round(property_tax_per_year / 12),
        "total_buy_monthly": round(emi + monthly_maintenance + property_tax_per_year / 12),
        "rent_year_5": round(monthly_rent * (1 + rent_esc) ** 4) if planning_horizon_years >= 5 else None,
        "rent_year_10": round(monthly_rent * (1 + rent_esc) ** 9) if planning_horizon_years >= 10 else None,
    }

    # Hidden costs
    hidden_costs = {
        "buying": [
            {"label": "Stamp Duty", "value": f"₹{format_inr_comma(round(stamp_duty))} ({stamp_duty_pct}%)"},
            {"label": "Registration Fee", "value": f"₹{format_inr_comma(registration_fee)}"},
            {"label": "Total Interest Paid", "value": f"₹{format_inr(max(0, total_interest))}"},
            {"label": "Maintenance ({} yrs)".format(planning_horizon_years), "value": f"₹{format_inr(monthly_maintenance * 12 * planning_horizon_years)}"},
            {"label": "Property Tax ({} yrs)".format(planning_horizon_years), "value": f"₹{format_inr(property_tax_per_year * planning_horizon_years)}"},
            {"label": "Section 80C Benefit", "value": "Up to ₹1.5L/yr on principal (check with CA)"},
        ],
        "renting": [
            {"label": "Security Deposit Locked", "value": f"₹{format_inr_comma(monthly_rent * 3)}"},
            {"label": "Broker Fee (every 2 yrs)", "value": f"₹{format_inr_comma(monthly_rent)}"},
            {"label": "Moving Costs", "value": "~₹10,000"},
            {"label": "No Equity Built", "value": "—"},
            {"label": "No Tax Deduction", "value": "—"},
        ],
    }

    # City appreciation data
    city_appreciation = None
    if city:
        city_info = get_city_info(city)
        if city_info:
            city_appreciation = {
                "city": city_info["city"],
                "avg_5yr_pct": city_info["avg_5yr_pct"],
                "yearly_data": city_info["appreciation"],
                "national_avg_pct": city_info["national_avg_pct"],
                "source": city_info["source"],
            }

    # All inputs used (for slider state restoration)
    inputs_used = {
        "city": city,
        "property_price": property_price,
        "monthly_rent": monthly_rent,
        "down_payment_pct": down_payment_pct,
        "loan_tenure_years": loan_tenure_years,
        "interest_rate_pct": interest_rate_pct,
        "planning_horizon_years": planning_horizon_years,
        "rent_escalation_pct": rent_escalation_pct,
        "down_payment_inv_return_pct": down_payment_inv_return_pct,
        "appreciation_rate_pct": appreciation_rate_pct,
        "stamp_duty_pct": stamp_duty_pct,
        "registration_fee": registration_fee,
        "monthly_maintenance": monthly_maintenance,
        "property_tax_per_year": property_tax_per_year,
    }

    return {
        "verdict": verdict,
        "verdict_text": verdict_text,
        "breakeven_year": break_even_year,
        "emi": round(emi),
        "monthly_delta": round(emi - monthly_rent),
        "yearly_series": yearly_series,
        "horizon_summary": {
            "total_rent_paid": round(total_rent),
            "total_buy_cost": round(total_buy),
            "net_delta": round(net_delta),
            "property_value_at_horizon": round(property_price * (1 + appr_rate) ** planning_horizon_years),
            "invest_corpus_at_horizon": round(down_payment * (1 + inv_rate) ** planning_horizon_years),
        },
        "monthly_snapshot": monthly_snapshot,
        "hidden_costs": hidden_costs,
        "city_appreciation": city_appreciation,
        "inputs_used": inputs_used,
        "assumptions": {
            "loan_tenure": f"{loan_tenure_years} years",
            "interest_rate": f"{interest_rate_pct}%",
            "rent_escalation": f"{rent_escalation_pct}% per year",
            "property_appreciation": f"{appreciation_rate_pct}% per year",
            "down_payment_inv_return": f"{down_payment_inv_return_pct}% per year",
            "stamp_duty": f"{stamp_duty_pct}%",
        },
        "low_dp_warning": low_dp_warning,
    }


def compute_quick_verdict(
    city: str,
    property_price: int,
    monthly_rent: int = 0,
    down_payment_pct: float = 20.0,
) -> dict:
    """Fast verdict — just EMI + break-even scan. No yearly series, no HTML. <5ms."""

    # Auto-fetch rent if not provided
    rent_source = "user_provided"
    rent_value = monthly_rent
    if rent_value <= 0:
        rent_data = get_avg_rent(city)
        if rent_data and "avg_monthly_rent" in rent_data:
            rent_value = rent_data["avg_monthly_rent"]
            rent_source = "city_average"
        else:
            return {"error": "Could not determine rent", "tip": "Please provide monthly_rent or use a supported city"}

    # Resolve appreciation
    appr_pct = get_avg_appreciation(city) if city else 7.5
    if appr_pct <= 0:
        appr_pct = 7.5

    # Cap down payment
    dp_pct = max(0.0, min(100.0, down_payment_pct))
    down_payment = property_price * dp_pct / 100
    loan_amount = property_price - down_payment

    # EMI
    emi = compute_emi(loan_amount, DEFAULT_INTEREST_RATE, DEFAULT_TENURE_YEARS)

    # Quick break-even scan
    stamp_duty = property_price * DEFAULT_STAMP_DUTY_PCT / 100
    cum_buy = stamp_duty + DEFAULT_REGISTRATION_FEE + down_payment
    cum_rent = 0.0
    appr_rate = appr_pct / 100
    rent_esc = DEFAULT_RENT_ESCALATION / 100
    breakeven_year = None

    for year in range(1, 26):
        # Buy: annual outflow
        buy_annual = (emi * 12 if year <= DEFAULT_TENURE_YEARS else 0) + DEFAULT_MAINTENANCE_MONTHLY * 12 + DEFAULT_PROPERTY_TAX_YEARLY
        cum_buy += buy_annual
        net_buy = cum_buy - (property_price * (1 + appr_rate) ** year - property_price)

        # Rent: annual cost
        rent_monthly = rent_value * (1 + rent_esc) ** (year - 1)
        cum_rent += rent_monthly * 12

        if breakeven_year is None and net_buy < cum_rent:
            breakeven_year = year
            break

    verdict = "BUY" if breakeven_year is not None and breakeven_year <= 20 else "RENT"
    monthly_delta = round(emi - rent_value)

    # Voice summaries
    price_fmt = format_inr(property_price)
    emi_fmt = format_inr(emi)
    delta_fmt = format_inr(abs(monthly_delta))

    if verdict == "BUY":
        voice_hi = (
            f"{city} mein ₹{price_fmt} ke ghar ke liye: EMI hogi ~₹{emi_fmt} — "
            f"abhi ke kiraye se ₹{delta_fmt} zyada. "
            f"Lekin year {breakeven_year} ke baad buying financially better ho jaata hai."
        )
        voice_en = (
            f"For a ₹{price_fmt} home in {city}: EMI will be ~₹{emi_fmt} — "
            f"₹{delta_fmt} more than your current rent. "
            f"But from year {breakeven_year}, buying becomes financially better."
        )
    else:
        voice_hi = (
            f"{city} mein ₹{price_fmt} ke ghar ke liye: EMI hogi ~₹{emi_fmt} — "
            f"abhi ke kiraye se ₹{delta_fmt} zyada. "
            f"20 saal ke horizon mein renting financially better lag raha hai."
        )
        voice_en = (
            f"For a ₹{price_fmt} home in {city}: EMI will be ~₹{emi_fmt} — "
            f"₹{delta_fmt} more than your current rent. "
            f"Within a 20-year horizon, renting looks financially better."
        )

    return {
        "verdict": verdict,
        "breakeven_year": breakeven_year,
        "emi": round(emi),
        "monthly_delta": monthly_delta,
        "rent_used": rent_value,
        "rent_source": rent_source,
        "down_payment_amount": round(down_payment),
        "city": city,
        "appreciation_pct": appr_pct,
        "voice_summary_hi": voice_hi,
        "voice_summary_en": voice_en,
    }
