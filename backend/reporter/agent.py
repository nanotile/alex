"""
Report Writer Agent - generates portfolio analysis narratives.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from agents import function_tool, RunContextWrapper
from agents.extensions.models.litellm_model import LitellmModel

logger = logging.getLogger()


@dataclass
class ReporterContext:
    """Context for the Reporter agent"""

    job_id: str
    portfolio_data: Dict[str, Any]
    user_data: Dict[str, Any]
    db: Optional[Any] = None  # Database connection (optional for testing)
    fundamentals: Optional[Dict[str, Dict[str, Any]]] = None  # {symbol: fundamentals_dict}
    economic_data: Optional[Dict[str, Dict[str, Any]]] = None  # {series_id: indicator_dict}


def calculate_portfolio_metrics(portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate basic portfolio metrics."""
    metrics = {
        "total_value": 0,
        "cash_balance": 0,
        "num_accounts": len(portfolio_data.get("accounts", [])),
        "num_positions": 0,
        "unique_symbols": set(),
    }

    for account in portfolio_data.get("accounts", []):
        metrics["cash_balance"] += float(account.get("cash_balance", 0))
        positions = account.get("positions", [])
        metrics["num_positions"] += len(positions)

        for position in positions:
            symbol = position.get("symbol")
            if symbol:
                metrics["unique_symbols"].add(symbol)

            # Calculate value if we have price
            instrument = position.get("instrument", {})
            if instrument.get("current_price"):
                value = float(position.get("quantity", 0)) * float(instrument["current_price"])
                metrics["total_value"] += value

    metrics["total_value"] += metrics["cash_balance"]
    metrics["unique_symbols"] = len(metrics["unique_symbols"])

    return metrics


def format_portfolio_for_analysis(portfolio_data: Dict[str, Any], user_data: Dict[str, Any]) -> str:
    """Format portfolio data for agent analysis."""
    metrics = calculate_portfolio_metrics(portfolio_data)

    lines = [
        f"Portfolio Overview:",
        f"- {metrics['num_accounts']} accounts",
        f"- {metrics['num_positions']} total positions",
        f"- {metrics['unique_symbols']} unique holdings",
        f"- ${metrics['cash_balance']:,.2f} in cash",
        f"- ${metrics['total_value']:,.2f} total value" if metrics["total_value"] > 0 else "",
        "",
        "Account Details:",
    ]

    for account in portfolio_data.get("accounts", []):
        name = account.get("name", "Unknown")
        cash = float(account.get("cash_balance", 0))
        lines.append(f"\n{name} (${cash:,.2f} cash):")

        for position in account.get("positions", []):
            symbol = position.get("symbol")
            quantity = float(position.get("quantity", 0))
            instrument = position.get("instrument", {})
            name = instrument.get("name", "")

            # Include allocation info if available
            allocations = []
            if instrument.get("asset_class"):
                allocations.append(f"Asset: {instrument['asset_class']}")
            if instrument.get("regions"):
                regions = ", ".join(
                    [f"{r['name']} {r['percentage']}%" for r in instrument["regions"][:2]]
                )
                allocations.append(f"Regions: {regions}")

            alloc_str = f" ({', '.join(allocations)})" if allocations else ""
            lines.append(f"  - {symbol}: {quantity:,.2f} shares{alloc_str}")

    # Add user context
    lines.extend(
        [
            "",
            "User Profile:",
            f"- Years to retirement: {user_data.get('years_until_retirement', 'Not specified')}",
            f"- Target retirement income: ${user_data.get('target_retirement_income', 0):,.0f}/year",
        ]
    )

    return "\n".join(lines)


# update_report tool removed - report is now saved directly in lambda_handler


@function_tool
async def get_market_insights(
    wrapper: RunContextWrapper[ReporterContext], symbols: List[str]
) -> str:
    """
    Retrieve market insights from S3 Vectors knowledge base.

    Args:
        wrapper: Context wrapper with job_id and database
        symbols: List of symbols to get insights for

    Returns:
        Relevant market context and insights
    """
    try:
        import boto3

        # Get account ID
        sts = boto3.client("sts")
        account_id = sts.get_caller_identity()["Account"]
        bucket = f"alex-vectors-{account_id}"

        # Get embeddings using Bedrock Titan
        bedrock_region = os.getenv("BEDROCK_REGION", os.getenv("DEFAULT_AWS_REGION", "us-east-1"))
        bedrock_embedding_model = os.getenv("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")
        bedrock = boto3.client("bedrock-runtime", region_name=bedrock_region)
        query = f"market analysis {' '.join(symbols[:5])}" if symbols else "market outlook"

        response = bedrock.invoke_model(
            modelId=bedrock_embedding_model,
            contentType="application/json",
            body=json.dumps({"inputText": query}),
        )

        result = json.loads(response["body"].read())
        embedding = result.get("embedding", [])

        # Search vectors
        s3v = boto3.client("s3vectors", region_name=bedrock_region)
        response = s3v.query_vectors(
            vectorBucketName=bucket,
            indexName="financial-research",
            queryVector={"float32": embedding},
            topK=3,
            returnMetadata=True,
        )

        # Format insights
        insights = []
        for vector in response.get("vectors", []):
            metadata = vector.get("metadata", {})
            text = metadata.get("text", "")[:200]
            if text:
                company = metadata.get("company_name", "")
                prefix = f"{company}: " if company else "- "
                insights.append(f"{prefix}{text}...")

        if insights:
            return "Market Insights:\n" + "\n".join(insights)
        else:
            return "Market insights unavailable - proceeding with standard analysis."

    except Exception as e:
        logger.warning(f"Reporter: Could not retrieve market insights: {e}")
        return "Market insights unavailable - proceeding with standard analysis."


def format_fundamentals_for_analysis(fundamentals: Dict[str, Dict[str, Any]]) -> str:
    """Format fundamentals data into a readable block for the LLM prompt."""
    if not fundamentals:
        return "No fundamental data available for this portfolio."

    lines = []
    for symbol, data in fundamentals.items():
        parts = [f"  {symbol}:"]

        company = data.get("company_name")
        if company:
            parts.append(f"    Company: {company}")

        sector = data.get("sector")
        industry = data.get("industry")
        if sector or industry:
            parts.append(f"    Sector/Industry: {sector or 'N/A'} / {industry or 'N/A'}")

        market_cap = data.get("market_cap")
        if market_cap:
            if market_cap >= 1_000_000_000_000:
                cap_str = f"${market_cap / 1_000_000_000_000:.1f}T"
            elif market_cap >= 1_000_000_000:
                cap_str = f"${market_cap / 1_000_000_000:.1f}B"
            else:
                cap_str = f"${market_cap / 1_000_000:.0f}M"
            parts.append(f"    Market Cap: {cap_str}")

        pe = data.get("pe_ratio")
        pb = data.get("pb_ratio")
        if pe or pb:
            val_parts = []
            if pe:
                val_parts.append(f"PE {float(pe):.1f}")
            if pb:
                val_parts.append(f"PB {float(pb):.1f}")
            parts.append(f"    Valuation: {', '.join(val_parts)}")

        div_yield = data.get("dividend_yield")
        if div_yield:
            parts.append(f"    Dividend Yield: {float(div_yield) * 100:.2f}%")

        roe = data.get("roe")
        if roe:
            parts.append(f"    ROE: {float(roe) * 100:.1f}%")

        d2e = data.get("debt_to_equity")
        if d2e:
            parts.append(f"    Debt/Equity: {float(d2e):.2f}")

        eps = data.get("eps")
        if eps:
            parts.append(f"    EPS (TTM): ${float(eps):.2f}")

        beta = data.get("beta")
        if beta:
            parts.append(f"    Beta: {float(beta):.2f}")

        high = data.get("fifty_two_week_high")
        low = data.get("fifty_two_week_low")
        if high and low:
            parts.append(f"    52-Week Range: ${float(low):.2f} - ${float(high):.2f}")

        lines.append("\n".join(parts))

    return "\n".join(lines)


def format_economic_context(economic_data: Dict[str, Dict[str, Any]]) -> str:
    """Format FRED economic indicators into a readable block for the LLM prompt."""
    if not economic_data:
        return "No economic indicator data available."

    def fmt_val(series_id: str, data: Dict) -> str:
        """Format a single indicator value with previous comparison."""
        val = data.get("latest_value")
        prev = data.get("previous_value")
        if val is None:
            return "N/A"
        try:
            val = float(val)
        except (ValueError, TypeError):
            return "N/A"

        val_str = f"{val:,.2f}%" if data.get("units") == "Percent" else f"{val:,.1f}"

        if prev is not None:
            try:
                prev = float(prev)
                prev_str = f"{prev:,.2f}%" if data.get("units") == "Percent" else f"{prev:,.1f}"
                val_str += f" (prev: {prev_str})"
            except (ValueError, TypeError):
                pass

        return val_str

    lines = ["Economic Environment (from FRED):"]

    # Interest Rates
    rate_ids = ["FEDFUNDS", "DGS10", "DGS2", "T10Y2Y"]
    rate_data = {sid: economic_data[sid] for sid in rate_ids if sid in economic_data}
    if rate_data:
        lines.append("  Interest Rates:")
        for sid in rate_ids:
            if sid in rate_data:
                d = rate_data[sid]
                name = d.get("series_name", sid)
                val_str = fmt_val(sid, d)
                extra = ""
                # Flag inverted yield curve
                if sid == "T10Y2Y":
                    try:
                        v = float(d.get("latest_value", 0))
                        if v < 0:
                            extra = " [INVERTED]"
                    except (ValueError, TypeError):
                        pass
                lines.append(f"    {name}: {val_str}{extra}")

    # Inflation & Employment
    macro_ids = ["CPIAUCSL", "UNRATE"]
    macro_data = {sid: economic_data[sid] for sid in macro_ids if sid in economic_data}
    if macro_data:
        lines.append("  Inflation & Employment:")
        for sid in macro_ids:
            if sid in macro_data:
                d = macro_data[sid]
                name = d.get("series_name", sid)
                lines.append(f"    {name}: {fmt_val(sid, d)}")

    # Market & Growth
    growth_ids = ["VIXCLS", "GDP"]
    growth_data = {sid: economic_data[sid] for sid in growth_ids if sid in economic_data}
    if growth_data:
        lines.append("  Market & Growth:")
        for sid in growth_ids:
            if sid in growth_data:
                d = growth_data[sid]
                name = d.get("series_name", sid)
                val_str = fmt_val(sid, d)
                if sid == "GDP":
                    # Format GDP in billions
                    try:
                        v = float(d.get("latest_value", 0))
                        prev = d.get("previous_value")
                        val_str = f"${v:,.1f}B"
                        if prev is not None:
                            val_str += f" (prev: ${float(prev):,.1f}B)"
                    except (ValueError, TypeError):
                        pass
                lines.append(f"    {name}: {val_str}")

    return "\n".join(lines)


def create_agent(job_id: str, portfolio_data: Dict[str, Any], user_data: Dict[str, Any],
                 db=None, fundamentals: Dict[str, Dict[str, Any]] = None,
                 economic_data: Dict[str, Dict[str, Any]] = None):
    """Create the reporter agent with tools and context."""

    # Get model configuration
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    # Set region for LiteLLM Bedrock calls
    bedrock_region = os.getenv("BEDROCK_REGION", "us-west-2")
    logger.info(f"DEBUG: BEDROCK_REGION from env = {bedrock_region}")
    os.environ["AWS_REGION_NAME"] = bedrock_region
    logger.info(f"DEBUG: Set AWS_REGION_NAME to {bedrock_region}")

    model = LitellmModel(model=f"bedrock/{model_id}")

    # Create context
    context = ReporterContext(
        job_id=job_id, portfolio_data=portfolio_data, user_data=user_data,
        db=db, fundamentals=fundamentals, economic_data=economic_data
    )

    # Tools - only get_market_insights now, report saved in lambda_handler
    tools = [get_market_insights]

    # Format portfolio for analysis
    portfolio_summary = format_portfolio_for_analysis(portfolio_data, user_data)

    # Format fundamentals for analysis
    fundamentals_section = format_fundamentals_for_analysis(fundamentals or {})

    # Format economic indicators
    economic_section = format_economic_context(economic_data or {})

    # Create task
    task = f"""Analyze this investment portfolio and write a comprehensive report.

{portfolio_summary}

Fundamental Data (from Financial Modeling Prep):
{fundamentals_section}

{economic_section}

Your task:
1. First, get market insights for the top holdings using get_market_insights()
2. Analyze the portfolio's current state, strengths, and weaknesses
3. Use the fundamental data above to provide specific valuation analysis
4. Use economic indicators to contextualize portfolio risks — note yield curve status, inflation trends, rate environment impact on fixed income vs equities
5. Generate a detailed, professional analysis report in markdown format

The report should include:
- Executive Summary
- Portfolio Composition Analysis (with valuation metrics from fundamentals)
- Economic Environment (summarize current rate, inflation, and growth conditions)
- Risk Assessment (use beta, debt/equity data, and VIX level)
- Diversification Analysis (use sector/industry data)
- Retirement Readiness (based on user goals)
- Recommendations (informed by valuations, yield, growth metrics, and macro environment)
- Market Context (from insights)

Provide your complete analysis as the final output in clear markdown format.
Make the report informative yet accessible to a retail investor."""

    return model, tools, task, context
