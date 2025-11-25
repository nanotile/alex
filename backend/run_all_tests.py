#!/usr/bin/env python3
"""
Run all backend tests with coverage reporting

This script runs pytest for all agent directories and generates
coverage reports. Use this during development to ensure all tests pass.

Usage:
    cd backend
    uv run run_all_tests.py

Options:
    --fast          Skip coverage reporting for faster execution
    --agent NAME    Run tests for specific agent only
    --verbose       Show detailed test output
"""

import subprocess
import sys
import argparse
from pathlib import Path
from typing import List, Dict


# Agent directories to test
AGENT_DIRS = [
    "database",
    "planner",
    "tagger",
    "reporter",
    "charter",
    "retirement"
]


def run_tests_for_agent(
    agent_dir: str,
    verbose: bool = False,
    with_coverage: bool = True
) -> tuple[bool, str]:
    """
    Run pytest for a specific agent

    Args:
        agent_dir: Directory name of the agent
        verbose: Show detailed output
        with_coverage: Include coverage reporting

    Returns:
        Tuple of (success, output_message)
    """
    print(f"\n{'='*60}")
    print(f"Testing: {agent_dir}")
    print('='*60)

    agent_path = Path(__file__).parent / agent_dir

    # Check if tests directory exists
    tests_path = agent_path / "tests"
    if not tests_path.exists():
        print(f"⚠️  No tests directory found, skipping...")
        return True, "No tests"

    # Build pytest command
    cmd = ["uv", "run", "pytest", "tests/"]

    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    if with_coverage:
        cmd.extend([
            "--cov=src",
            "--cov=.",
            "--cov-report=term-missing",
            f"--cov-report=html:coverage_html"
        ])

    # Run tests
    result = subprocess.run(
        cmd,
        cwd=agent_path,
        capture_output=not verbose,
        text=True
    )

    if result.returncode == 0:
        print(f"✅ All tests passed for {agent_dir}")
        return True, "Passed"
    else:
        print(f"❌ Tests failed for {agent_dir}")
        if not verbose and result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return False, "Failed"


def main():
    """Run all tests"""
    parser = argparse.ArgumentParser(description="Run Alex backend tests")
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip coverage reporting for faster execution"
    )
    parser.add_argument(
        "--agent",
        type=str,
        help="Run tests for specific agent only"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed test output"
    )

    args = parser.parse_args()

    print("🧪 Alex Backend Test Suite")
    print("="*60)

    # Determine which agents to test
    agents_to_test = [args.agent] if args.agent else AGENT_DIRS

    # Validate agent name
    if args.agent and args.agent not in AGENT_DIRS:
        print(f"❌ Unknown agent: {args.agent}")
        print(f"Available agents: {', '.join(AGENT_DIRS)}")
        return 1

    # Run tests
    results: Dict[str, tuple[bool, str]] = {}
    for agent in agents_to_test:
        success, message = run_tests_for_agent(
            agent,
            verbose=args.verbose,
            with_coverage=not args.fast
        )
        results[agent] = (success, message)

    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print('='*60)

    for agent, (passed, message) in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{agent:20} {status:12} ({message})")

    # Overall result
    all_passed = all(passed for passed, _ in results.values())

    if all_passed:
        print(f"\n{'='*60}")
        print("✅ All tests passed!")
        print('='*60)
        return 0
    else:
        print(f"\n{'='*60}")
        print("❌ Some tests failed")
        print('='*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
