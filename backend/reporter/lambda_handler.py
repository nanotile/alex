"""
Report Writer Agent Lambda Handler
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from agents import Agent, Runner, trace
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from litellm.exceptions import RateLimitError
from judge import evaluate

GUARD_AGAINST_SCORE = 0.6  # Reject reports scoring below 60%

try:
    from dotenv import load_dotenv

    load_dotenv(override=True)
except ImportError:
    pass

# Import database package
from src import Database

from templates import REPORTER_INSTRUCTIONS
from agent import create_agent, ReporterContext
from observability import observe

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@retry(
    retry=retry_if_exception_type(RateLimitError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    before_sleep=lambda retry_state: logger.info(
        f"Reporter: Rate limit hit, retrying in {retry_state.next_action.sleep} seconds..."
    ),
)
async def run_reporter_agent(
    job_id: str,
    portfolio_data: Dict[str, Any],
    user_data: Dict[str, Any],
    db=None,
    observability=None,
    fundamentals: Dict[str, Any] = None,
    economic_data: Dict[str, Any] = None,
    technical_data: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Run the reporter agent to generate analysis."""

    # Create agent with tools and context
    model, tools, task, context = create_agent(job_id, portfolio_data, user_data, db, fundamentals, economic_data, technical_data)

    # Run agent with context
    with trace("Reporter Agent"):
        agent = Agent[ReporterContext](  # Specify the context type
            name="Report Writer", instructions=REPORTER_INSTRUCTIONS, model=model, tools=tools
        )

        result = await Runner.run(
            agent,
            input=task,
            context=context,  # Pass the context
            max_turns=10,
        )

        response = result.final_output
        score = None

        if observability:
            with observability.start_as_current_span(name="judge") as span:
                evaluation = await evaluate(REPORTER_INSTRUCTIONS, task, response)
                score = evaluation.score / 100
                comment = evaluation.feedback
                span.score(name="Judge", value=score, data_type="NUMERIC", comment=comment)
                observation = f"Score: {score} - Feedback: {comment}"
                observability.create_event(name="Judge Event", status_message=observation)
                logger.info(f"Reporter: First attempt score: {score}")

                if score < GUARD_AGAINST_SCORE:
                    logger.warning(f"Reporter: Score {score} below threshold {GUARD_AGAINST_SCORE}, retrying agent")

                    # Retry: run the agent again
                    retry_result = await Runner.run(
                        agent,
                        input=task,
                        context=context,
                        max_turns=10,
                    )
                    retry_response = retry_result.final_output

                    retry_evaluation = await evaluate(REPORTER_INSTRUCTIONS, task, retry_response)
                    retry_score = retry_evaluation.score / 100
                    retry_comment = retry_evaluation.feedback
                    logger.info(f"Reporter: Retry score: {retry_score} (first was {score})")

                    span.score(name="Judge Retry", value=retry_score, data_type="NUMERIC", comment=retry_comment)
                    observability.create_event(
                        name="Judge Retry Event",
                        status_message=f"Retry Score: {retry_score} - Feedback: {retry_comment}",
                    )

                    # Keep the better of the two attempts
                    if retry_score >= score:
                        response = retry_response
                        score = retry_score
                        logger.info(f"Reporter: Using retry response (score {retry_score})")
                    else:
                        logger.info(f"Reporter: Keeping first response (score {score} > retry {retry_score})")

        # Save the report to database
        report_payload = {
            "content": response,
            "generated_at": datetime.utcnow().isoformat(),
            "agent": "reporter",
            "quality_score": score,
        }

        success = db.jobs.update_report(job_id, report_payload)

        if not success:
            logger.error(f"Failed to save report for job {job_id}")

        return {
            "success": success,
            "message": "Report generated and stored"
            if success
            else "Report generated but failed to save",
            "final_output": result.final_output,
        }


def lambda_handler(event, context):
    """
    Lambda handler expecting job_id, portfolio_data, and user_data in event.

    Expected event:
    {
        "job_id": "uuid",
        "portfolio_data": {...},
        "user_data": {...}
    }
    """
    # Wrap entire handler with observability context
    with observe() as observability:
        try:
            logger.info(f"Reporter Lambda invoked with event: {json.dumps(event)[:500]}")

            # Parse event
            if isinstance(event, str):
                event = json.loads(event)

            job_id = event.get("job_id")
            if not job_id:
                return {"statusCode": 400, "body": json.dumps({"error": "job_id is required"})}

            # Initialize database
            db = Database()

            portfolio_data = event.get("portfolio_data")
            if not portfolio_data:
                # Try to load from database
                try:
                    job = db.jobs.find_by_id(job_id)
                    if job:
                        user_id = job["clerk_user_id"]

                        if observability:
                            observability.create_event(
                                name="Reporter Started!", status_message="OK"
                            )
                        user = db.users.find_by_clerk_id(user_id)
                        accounts = db.accounts.find_by_user(user_id)

                        portfolio_data = {"user_id": user_id, "job_id": job_id, "accounts": []}

                        for account in accounts:
                            positions = db.positions.find_by_account(account["id"])
                            account_data = {
                                "id": account["id"],
                                "name": account["account_name"],
                                "type": account.get("account_type", "investment"),
                                "cash_balance": float(account.get("cash_balance", 0)),
                                "positions": [],
                            }

                            for position in positions:
                                instrument = db.instruments.find_by_symbol(position["symbol"])
                                if instrument:
                                    account_data["positions"].append(
                                        {
                                            "symbol": position["symbol"],
                                            "quantity": float(position["quantity"]),
                                            "instrument": instrument,
                                        }
                                    )

                            portfolio_data["accounts"].append(account_data)
                    else:
                        return {
                            "statusCode": 404,
                            "body": json.dumps({"error": f"Job {job_id} not found"}),
                        }
                except Exception as e:
                    logger.error(f"Could not load portfolio from database: {e}")
                    return {
                        "statusCode": 400,
                        "body": json.dumps({"error": "No portfolio data provided"}),
                    }

            user_data = event.get("user_data", {})
            if not user_data:
                # Try to load from database
                try:
                    job = db.jobs.find_by_id(job_id)
                    if job and job.get("clerk_user_id"):
                        status = f"Job ID: {job_id} Clerk User ID: {job['clerk_user_id']}"
                        if observability:
                            observability.create_event(
                                name="Reporter about to run", status_message=status
                            )
                        user = db.users.find_by_clerk_id(job["clerk_user_id"])
                        if user:
                            user_data = {
                                "years_until_retirement": user.get("years_until_retirement", 30),
                                "target_retirement_income": float(
                                    user.get("target_retirement_income", 80000)
                                ),
                            }
                        else:
                            user_data = {
                                "years_until_retirement": 30,
                                "target_retirement_income": 80000,
                            }
                except Exception as e:
                    logger.warning(f"Could not load user data: {e}. Using defaults.")
                    user_data = {"years_until_retirement": 30, "target_retirement_income": 80000}

            # Load fundamentals from DB (populated by Planner's FMP fetch)
            fundamentals = {}
            try:
                symbols = set()
                for account in portfolio_data.get("accounts", []):
                    for position in account.get("positions", []):
                        if position.get("symbol"):
                            symbols.add(position["symbol"])
                if symbols:
                    records = db.fundamentals.find_by_symbols(list(symbols))
                    fundamentals = {r["symbol"]: r for r in records}
                    logger.info(f"Reporter: Loaded fundamentals for {len(fundamentals)} symbols")
            except Exception as e:
                logger.warning(f"Reporter: Could not load fundamentals: {e}")

            # Load economic indicators from DB (populated by Planner's FRED fetch)
            economic_data = {}
            try:
                indicators = db.economic_indicators.find_all()
                economic_data = {r["series_id"]: r for r in indicators}
                logger.info(f"Reporter: Loaded {len(economic_data)} economic indicators")
            except Exception as e:
                logger.warning(f"Reporter: Could not load economic indicators: {e}")

            # Load technical indicators from DB (populated by Planner's pandas-ta computation)
            technical_data = {}
            try:
                if symbols:
                    records = db.technical_indicators.find_by_symbols(list(symbols))
                    for r in records:
                        ind = r.get("indicators")
                        if isinstance(ind, str):
                            import json as _json
                            ind = _json.loads(ind)
                        technical_data[r["symbol"]] = ind
                    logger.info(f"Reporter: Loaded technical indicators for {len(technical_data)} symbols")
            except Exception as e:
                logger.warning(f"Reporter: Could not load technical indicators: {e}")

            # Run the agent
            result = asyncio.run(
                run_reporter_agent(job_id, portfolio_data, user_data, db, observability, fundamentals, economic_data, technical_data)
            )

            logger.info(f"Reporter completed for job {job_id}")

            return {"statusCode": 200, "body": json.dumps(result)}

        except Exception as e:
            logger.error(f"Error in reporter: {e}", exc_info=True)
            return {"statusCode": 500, "body": json.dumps({"success": False, "error": str(e)})}


# For local testing
if __name__ == "__main__":
    test_event = {
        "job_id": "550e8400-e29b-41d4-a716-446655440002",
        "portfolio_data": {
            "accounts": [
                {
                    "name": "401(k)",
                    "cash_balance": 5000,
                    "positions": [
                        {
                            "symbol": "SPY",
                            "quantity": 100,
                            "instrument": {
                                "name": "SPDR S&P 500 ETF",
                                "current_price": 450,
                                "asset_class": "equity",
                            },
                        }
                    ],
                }
            ]
        },
        "user_data": {"years_until_retirement": 25, "target_retirement_income": 75000},
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
