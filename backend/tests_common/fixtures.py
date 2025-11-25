"""
Shared test data fixtures for Alex backend tests
"""

from typing import Dict, Any, List
from datetime import datetime, timezone


SAMPLE_USER_PREFS = {
    "risk_tolerance": "moderate",
    "retirement_age": 65,
    "current_age": 45,
    "annual_expenses": 60000,
    "savings_rate": 15,
}


SAMPLE_INSTRUMENTS = {
    "VTI": {
        "symbol": "VTI",
        "name": "Vanguard Total Stock Market ETF",
        "instrument_type": "etf",
        "asset_class": "equity",
        "current_price": 220.0,
        "expense_ratio": 0.03,
        "regions": [
            {"name": "North America", "percentage": 100.0}
        ],
        "sectors": [
            {"name": "Technology", "percentage": 30.0},
            {"name": "Healthcare", "percentage": 15.0},
            {"name": "Financial", "percentage": 12.0},
        ]
    },
    "BND": {
        "symbol": "BND",
        "name": "Vanguard Total Bond Market ETF",
        "instrument_type": "etf",
        "asset_class": "bond",
        "current_price": 75.0,
        "expense_ratio": 0.04,
        "regions": [
            {"name": "North America", "percentage": 100.0}
        ]
    },
    "VXUS": {
        "symbol": "VXUS",
        "name": "Vanguard Total International Stock ETF",
        "instrument_type": "etf",
        "asset_class": "equity",
        "current_price": 60.0,
        "expense_ratio": 0.07,
        "regions": [
            {"name": "Europe", "percentage": 40.0},
            {"name": "Asia", "percentage": 35.0},
            {"name": "Other", "percentage": 25.0}
        ]
    }
}


SAMPLE_PORTFOLIO = {
    "accounts": [
        {
            "id": "acc_001",
            "name": "Retirement Account",
            "account_type": "ira",
            "cash_balance": 5000.0,
            "positions": [
                {
                    "id": "pos_001",
                    "symbol": "VTI",
                    "quantity": 100.0,
                    "cost_basis": 20000.0,
                    "instrument": SAMPLE_INSTRUMENTS["VTI"]
                },
                {
                    "id": "pos_002",
                    "symbol": "BND",
                    "quantity": 200.0,
                    "cost_basis": 14000.0,
                    "instrument": SAMPLE_INSTRUMENTS["BND"]
                }
            ]
        },
        {
            "id": "acc_002",
            "name": "Taxable Account",
            "account_type": "taxable",
            "cash_balance": 2000.0,
            "positions": [
                {
                    "id": "pos_003",
                    "symbol": "VXUS",
                    "quantity": 50.0,
                    "cost_basis": 2800.0,
                    "instrument": SAMPLE_INSTRUMENTS["VXUS"]
                }
            ]
        }
    ]
}


SAMPLE_JOB = {
    "id": "job_001",
    "clerk_user_id": "test_user_001",
    "job_type": "portfolio_analysis",
    "status": "pending",
    "request_payload": {
        "analysis_type": "comprehensive",
        "requested_at": datetime.now(timezone.utc).isoformat()
    },
    "created_at": datetime.now(timezone.utc).isoformat(),
}


def create_test_user(
    clerk_id: str = "test_user_001",
    email: str = "test@example.com",
    display_name: str = "Test User"
) -> Dict[str, Any]:
    """Create a test user dictionary"""
    return {
        "id": "user_001",
        "clerk_user_id": clerk_id,
        "email": email,
        "display_name": display_name,
        "preferences": SAMPLE_USER_PREFS.copy(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }


def create_test_portfolio(
    num_accounts: int = 2,
    positions_per_account: int = 2
) -> Dict[str, Any]:
    """Create a test portfolio with specified structure"""
    accounts = []

    for i in range(num_accounts):
        account = {
            "id": f"acc_{i+1:03d}",
            "name": f"Account {i+1}",
            "account_type": "ira" if i == 0 else "taxable",
            "cash_balance": 5000.0 * (i + 1),
            "positions": []
        }

        symbols = list(SAMPLE_INSTRUMENTS.keys())
        for j in range(min(positions_per_account, len(symbols))):
            symbol = symbols[j % len(symbols)]
            account["positions"].append({
                "id": f"pos_{i}_{j:03d}",
                "symbol": symbol,
                "quantity": 100.0 * (j + 1),
                "cost_basis": 10000.0 * (j + 1),
                "instrument": SAMPLE_INSTRUMENTS[symbol].copy()
            })

        accounts.append(account)

    return {"accounts": accounts}


def create_test_job(
    job_id: str = "job_001",
    clerk_user_id: str = "test_user_001",
    job_type: str = "portfolio_analysis",
    status: str = "pending"
) -> Dict[str, Any]:
    """Create a test job dictionary"""
    return {
        "id": job_id,
        "clerk_user_id": clerk_user_id,
        "job_type": job_type,
        "status": status,
        "request_payload": {
            "analysis_type": "comprehensive",
            "test_run": True
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }


# Sample market insights for testing
SAMPLE_MARKET_INSIGHTS = """
Market Analysis Summary:
- VTI: Total market exposure with strong performance across sectors
- BND: Stable bond allocation providing portfolio ballast
- VXUS: International diversification with exposure to developed and emerging markets

Current market conditions favor a balanced approach with moderate risk tolerance.
"""


# Sample agent responses
SAMPLE_REPORT_OUTPUT = """
Portfolio Analysis Report

Your portfolio demonstrates good diversification across asset classes with
a total value of approximately $45,000. The allocation shows:

- 60% in domestic equities (VTI)
- 25% in bonds (BND)
- 15% in international equities (VXUS)

This balanced approach aligns well with a moderate risk tolerance and
a 20-year time horizon to retirement.

Key Strengths:
- Appropriate equity/bond balance for your age
- Low-cost index fund approach
- Geographic diversification

Recommendations:
- Consider increasing international allocation to 20-25%
- Maintain current savings rate
- Review allocation annually
"""


SAMPLE_CHART_DATA = {
    "asset_allocation": {
        "title": "Asset Allocation",
        "type": "pie",
        "data": [
            {"name": "US Equities", "value": 60},
            {"name": "Bonds", "value": 25},
            {"name": "International", "value": 15}
        ]
    },
    "performance": {
        "title": "Portfolio Performance",
        "type": "line",
        "data": [
            {"date": "2024-01", "value": 40000},
            {"date": "2024-02", "value": 41500},
            {"date": "2024-03", "value": 43000},
            {"date": "2024-04", "value": 45000}
        ]
    }
}


SAMPLE_RETIREMENT_PROJECTION = {
    "success_rate": 85.5,
    "projected_value": 1250000,
    "years_to_retirement": 20,
    "monthly_income": 5200,
    "scenarios": [
        {"percentile": 10, "value": 800000},
        {"percentile": 50, "value": 1250000},
        {"percentile": 90, "value": 1800000}
    ]
}
