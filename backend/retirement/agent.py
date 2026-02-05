"""
Retirement Specialist Agent - provides retirement planning analysis and projections.
"""

import os
import json
import logging
import random
from typing import Dict, Any
from datetime import datetime

# No tools needed - simplified agent
from agents.extensions.models.litellm_model import LitellmModel

logger = logging.getLogger()

# Context removed - no longer needed without tools


def calculate_portfolio_value(portfolio_data: Dict[str, Any]) -> float:
    """Calculate current portfolio value."""
    total_value = 0.0

    for account in portfolio_data.get("accounts", []):
        cash = float(account.get("cash_balance", 0))
        total_value += cash

        for position in account.get("positions", []):
            quantity = float(position.get("quantity", 0))
            instrument = position.get("instrument", {})
            price = float(instrument.get("current_price", 100))
            total_value += quantity * price

    return total_value


def calculate_asset_allocation(portfolio_data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate asset allocation percentages."""
    total_equity = 0.0
    total_bonds = 0.0
    total_real_estate = 0.0
    total_commodities = 0.0
    total_cash = 0.0
    total_value = 0.0

    for account in portfolio_data.get("accounts", []):
        cash = float(account.get("cash_balance", 0))
        total_cash += cash
        total_value += cash

        for position in account.get("positions", []):
            quantity = float(position.get("quantity", 0))
            instrument = position.get("instrument", {})
            price = float(instrument.get("current_price", 100))
            value = quantity * price
            total_value += value

            # Get asset class allocation
            asset_allocation = instrument.get("allocation_asset_class", {})
            if asset_allocation:
                total_equity += value * asset_allocation.get("equity", 0) / 100
                total_bonds += value * asset_allocation.get("fixed_income", 0) / 100
                total_real_estate += value * asset_allocation.get("real_estate", 0) / 100
                total_commodities += value * asset_allocation.get("commodities", 0) / 100

    if total_value == 0:
        return {"equity": 0, "bonds": 0, "real_estate": 0, "commodities": 0, "cash": 0}

    return {
        "equity": total_equity / total_value,
        "bonds": total_bonds / total_value,
        "real_estate": total_real_estate / total_value,
        "commodities": total_commodities / total_value,
        "cash": total_cash / total_value,
    }


def run_monte_carlo_simulation(
    current_value: float,
    years_until_retirement: int,
    target_annual_income: float,
    asset_allocation: Dict[str, float],
    annual_contribution: float = 10000,
    num_simulations: int = 1000,
) -> Dict[str, Any]:
    """Run Monte Carlo simulation for retirement planning."""

    # Historical return parameters (annualized)
    equity_return_mean = 0.07
    equity_return_std = 0.18
    bond_return_mean = 0.04
    bond_return_std = 0.05
    real_estate_return_mean = 0.06
    real_estate_return_std = 0.12

    def _portfolio_return(alloc):
        return (
            alloc["equity"] * random.gauss(equity_return_mean, equity_return_std)
            + alloc["bonds"] * random.gauss(bond_return_mean, bond_return_std)
            + alloc["real_estate"] * random.gauss(real_estate_return_mean, real_estate_return_std)
            + alloc["cash"] * 0.02
        )

    successful_scenarios = 0
    final_values = []
    years_lasted = []
    retirement_values = []  # Value at retirement for each sim

    retirement_years = 30

    for _ in range(num_simulations):
        portfolio_value = current_value

        # Accumulation phase
        for _ in range(years_until_retirement):
            portfolio_value = portfolio_value * (1 + _portfolio_return(asset_allocation))
            portfolio_value += annual_contribution

        retirement_values.append(max(0, portfolio_value))

        # Retirement phase
        annual_withdrawal = target_annual_income
        years_income_lasted = 0

        for year in range(retirement_years):
            if portfolio_value <= 0:
                break
            annual_withdrawal *= 1.03  # Inflation adjustment
            portfolio_value = portfolio_value * (1 + _portfolio_return(asset_allocation)) - annual_withdrawal
            if portfolio_value > 0:
                years_income_lasted += 1

        final_values.append(max(0, portfolio_value))
        years_lasted.append(years_income_lasted)

        if years_income_lasted >= retirement_years:
            successful_scenarios += 1

    # Calculate statistics
    final_values.sort()
    retirement_values.sort()
    success_rate = (successful_scenarios / num_simulations) * 100

    # Percentile indices
    p10 = num_simulations // 10
    p25 = num_simulations // 4
    p50 = num_simulations // 2
    p75 = 3 * num_simulations // 4
    p90 = 9 * num_simulations // 10

    # Expected value at retirement (deterministic)
    expected_return = (
        asset_allocation["equity"] * equity_return_mean
        + asset_allocation["bonds"] * bond_return_mean
        + asset_allocation["real_estate"] * real_estate_return_mean
        + asset_allocation["cash"] * 0.02
    )
    expected_value_at_retirement = current_value
    for _ in range(years_until_retirement):
        expected_value_at_retirement *= 1 + expected_return
        expected_value_at_retirement += annual_contribution

    # --- "What-if" scenarios ---
    # Delay retirement by 2 years
    delay_success = 0
    for _ in range(num_simulations):
        pv = current_value
        for _ in range(years_until_retirement + 2):
            pv = pv * (1 + _portfolio_return(asset_allocation)) + annual_contribution
        aw = target_annual_income
        lasted = 0
        for yr in range(retirement_years):
            if pv <= 0:
                break
            aw *= 1.03
            pv = pv * (1 + _portfolio_return(asset_allocation)) - aw
            if pv > 0:
                lasted += 1
        if lasted >= retirement_years:
            delay_success += 1
    delay_success_rate = round((delay_success / num_simulations) * 100, 1)

    # Increase contributions by $5K/year
    bump_final = []
    for _ in range(num_simulations):
        pv = current_value
        for _ in range(years_until_retirement):
            pv = pv * (1 + _portfolio_return(asset_allocation)) + (annual_contribution + 5000)
        bump_final.append(pv)
    bump_final.sort()
    bump_median = bump_final[num_simulations // 2]

    return {
        "success_rate": round(success_rate, 1),
        "median_final_value": round(final_values[p50], 2),
        "percentile_10": round(final_values[p10], 2),
        "percentile_25": round(final_values[p25], 2),
        "percentile_75": round(final_values[p75], 2),
        "percentile_90": round(final_values[p90], 2),
        "average_years_lasted": round(sum(years_lasted) / len(years_lasted), 1),
        "expected_value_at_retirement": round(expected_value_at_retirement, 2),
        "retirement_value_p25": round(retirement_values[p25], 2),
        "retirement_value_median": round(retirement_values[p50], 2),
        "retirement_value_p75": round(retirement_values[p75], 2),
        # What-if results
        "whatif_delay_2yr_success_rate": delay_success_rate,
        "whatif_extra_5k_median_retirement": round(bump_median, 2),
        "annual_contribution": annual_contribution,
    }


def generate_projections(
    current_value: float,
    years_until_retirement: int,
    asset_allocation: Dict[str, float],
    current_age: int,
) -> list:
    """Generate simplified retirement projections."""

    # Expected returns
    expected_return = (
        asset_allocation["equity"] * 0.07
        + asset_allocation["bonds"] * 0.04
        + asset_allocation["real_estate"] * 0.06
        + asset_allocation["cash"] * 0.02
    )

    projections = []
    portfolio_value = current_value

    # Only show key milestones (every 5 years)
    milestone_years = list(range(0, years_until_retirement + 31, 5))

    for year in milestone_years:
        age = current_age + year

        if year <= years_until_retirement:
            # Calculate accumulation
            for _ in range(min(5, year)):
                portfolio_value *= 1 + expected_return
                portfolio_value += 10000
            phase = "accumulation"
            annual_income = 0
        else:
            # Calculate retirement withdrawals
            withdrawal_rate = 0.04
            annual_income = portfolio_value * withdrawal_rate
            years_in_retirement = min(5, year - years_until_retirement)
            for _ in range(years_in_retirement):
                portfolio_value = portfolio_value * (1 + expected_return) - annual_income
            phase = "retirement"

        if portfolio_value > 0:
            projections.append(
                {
                    "year": year,
                    "age": age,
                    "portfolio_value": round(portfolio_value, 2),
                    "annual_income": round(annual_income, 2),
                    "phase": phase,
                }
            )

    return projections


# Tool removed - analysis is now saved directly in lambda_handler


def create_agent(
    job_id: str, portfolio_data: Dict[str, Any], user_preferences: Dict[str, Any], db=None
):
    """Create the retirement agent with tools and context."""

    # Get model configuration
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    # Set region for LiteLLM Bedrock calls
    bedrock_region = os.getenv("BEDROCK_REGION", "us-west-2")
    os.environ["AWS_REGION_NAME"] = bedrock_region

    model = LitellmModel(model=f"bedrock/{model_id}")

    # Extract user preferences
    years_until_retirement = user_preferences.get("years_until_retirement", 30)
    target_income = user_preferences.get("target_retirement_income", 80000)
    current_age = user_preferences.get("current_age", 40)

    # Calculate portfolio metrics
    portfolio_value = calculate_portfolio_value(portfolio_data)
    allocation = calculate_asset_allocation(portfolio_data)

    # Estimate annual contribution from portfolio growth rate (rough heuristic)
    # If portfolio value > 0 and years > 0, assume ~3% of value as annual contribution
    annual_contribution = max(10000, portfolio_value * 0.03) if portfolio_value > 0 else 10000

    # Run Monte Carlo simulation
    monte_carlo = run_monte_carlo_simulation(
        portfolio_value, years_until_retirement, target_income, allocation,
        annual_contribution=annual_contribution, num_simulations=1000,
    )

    # Generate projections
    projections = generate_projections(
        portfolio_value, years_until_retirement, allocation, current_age
    )

    # No context needed anymore - simplified agent

    # No tools needed - agent will return analysis as final output
    tools = []

    # Format comprehensive context for the agent
    task = f"""
# Portfolio Analysis Context

## Current Situation
- Portfolio Value: ${portfolio_value:,.0f}
- Asset Allocation: {", ".join([f"{k.title()}: {v:.0%}" for k, v in allocation.items() if v > 0])}
- Years to Retirement: {years_until_retirement}
- Target Annual Income: ${target_income:,.0f}
- Current Age: {current_age}
- Estimated Annual Contribution: ${annual_contribution:,.0f}

## Monte Carlo Simulation Results ({monte_carlo.get('annual_contribution', annual_contribution):,.0f}/yr contributions, 1,000 scenarios)
- Success Rate: {monte_carlo["success_rate"]}% (probability of sustaining retirement income for 30 years)
- Expected Portfolio Value at Retirement: ${monte_carlo["expected_value_at_retirement"]:,.0f}
- 10th Percentile Outcome: ${monte_carlo["percentile_10"]:,.0f} (worst case)
- Median Final Value: ${monte_carlo["median_final_value"]:,.0f}
- 90th Percentile Outcome: ${monte_carlo["percentile_90"]:,.0f} (best case)
- Average Years Portfolio Lasts: {monte_carlo["average_years_lasted"]} years

## Three Scenario Narratives

### Conservative Scenario (25th Percentile)
- Portfolio at Retirement: ${monte_carlo["retirement_value_p25"]:,.0f}
- Final Value After 30-Year Retirement: ${monte_carlo["percentile_25"]:,.0f}
- Interpretation: In a below-average market, your portfolio reaches ${monte_carlo["retirement_value_p25"]:,.0f} at retirement with ${monte_carlo["percentile_25"]:,.0f} remaining after 30 years of withdrawals.

### Base Scenario (Median)
- Portfolio at Retirement: ${monte_carlo["retirement_value_median"]:,.0f}
- Final Value After 30-Year Retirement: ${monte_carlo["median_final_value"]:,.0f}
- Interpretation: Under typical market conditions, your portfolio grows to ${monte_carlo["retirement_value_median"]:,.0f} by retirement with ${monte_carlo["median_final_value"]:,.0f} remaining.

### Optimistic Scenario (75th Percentile)
- Portfolio at Retirement: ${monte_carlo["retirement_value_p75"]:,.0f}
- Final Value After 30-Year Retirement: ${monte_carlo["percentile_75"]:,.0f}
- Interpretation: In a strong market, your portfolio reaches ${monte_carlo["retirement_value_p75"]:,.0f} at retirement with ${monte_carlo["percentile_75"]:,.0f} remaining — a comfortable surplus.

## What-If Recommendations
- Delay retirement by 2 years → success rate changes from {monte_carlo["success_rate"]}% to {monte_carlo["whatif_delay_2yr_success_rate"]}%
- Increase contributions by $5,000/year → median portfolio at retirement changes from ${monte_carlo["retirement_value_median"]:,.0f} to ${monte_carlo["whatif_extra_5k_median_retirement"]:,.0f} (+${monte_carlo["whatif_extra_5k_median_retirement"] - monte_carlo["retirement_value_median"]:,.0f})

## Key Projections (Milestones)
"""

    for proj in projections[:6]:
        if proj["phase"] == "accumulation":
            task += f"- Age {proj['age']}: ${proj['portfolio_value']:,.0f} (building wealth)\n"
        else:
            task += f"- Age {proj['age']}: ${proj['portfolio_value']:,.0f} (annual income: ${proj['annual_income']:,.0f})\n"

    sequence_risk_note = ""
    if monte_carlo["success_rate"] < 80:
        sequence_risk_note = """
## ⚠ Sequence-of-Returns Risk Warning
With a success rate below 80%, your portfolio is vulnerable to sequence-of-returns risk:
poor market returns in the first few years of retirement can permanently deplete your
portfolio even if average returns recover later. Consider building a 2-3 year cash buffer
before retiring and using a dynamic withdrawal strategy (reduce withdrawals after down years).
"""

    task += f"""
{sequence_risk_note}
## Risk Factors to Consider
- Sequence of returns risk (poor returns early in retirement)
- Inflation impact (3% assumed)
- Healthcare costs in retirement
- Longevity risk (living beyond 30 years)
- Market volatility (equity standard deviation: 18%)

## Safe Withdrawal Rate Analysis
- 4% Rule: ${portfolio_value * 0.04:,.0f} initial annual income
- Target Income: ${target_income:,.0f}
- Gap: ${target_income - (portfolio_value * 0.04):,.0f}

Your task: Analyze this retirement readiness data and provide a comprehensive retirement analysis including:
1. Clear assessment of retirement readiness with the three scenarios (Conservative, Base, Optimistic)
2. Present each scenario as a narrative the reader can picture
3. Include the "What-If" recommendations with specific numbers
4. If success rate < 80%, emphasize sequence-of-returns risk and mitigation strategies
5. Specific recommendations to improve success rate
6. Risk mitigation strategies
7. Action items with timeline

Provide your analysis in clear markdown format with specific numbers and actionable recommendations.
"""

    return model, tools, task
