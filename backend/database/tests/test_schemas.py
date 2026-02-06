"""
Tests for Pydantic schemas and validation
"""

import pytest
from decimal import Decimal
from pydantic import ValidationError
from src.schemas import (
    UserCreate,
    AccountCreate,
    PositionCreate,
    JobCreate,
    JobUpdate,
    JobStatus,
)


class TestUserCreate:
    """Test UserCreate schema validation"""

    def test_valid_user_create(self):
        """Test creating valid user schema"""
        user = UserCreate(
            clerk_user_id="clerk_123",
            display_name="Test User"
        )

        assert user.clerk_user_id == "clerk_123"
        assert user.display_name == "Test User"

    def test_user_create_with_retirement_fields(self):
        """Test user creation with retirement planning fields"""
        user = UserCreate(
            clerk_user_id="clerk_123",
            display_name="Test User",
            years_until_retirement=20,
            target_retirement_income=Decimal("80000.00"),
            asset_class_targets={"equity": 70, "fixed_income": 30},
            region_targets={"north_america": 60, "international": 40},
        )

        assert user.years_until_retirement == 20
        assert user.target_retirement_income == Decimal("80000.00")
        assert user.asset_class_targets["equity"] == 70

    def test_user_create_requires_clerk_id(self):
        """Test that clerk_user_id is required"""
        with pytest.raises(ValidationError):
            UserCreate(display_name="Test User")


class TestAccountCreate:
    """Test AccountCreate schema validation"""

    def test_valid_account_create(self):
        """Test creating valid account schema"""
        account = AccountCreate(
            account_name="My 401k",
            account_purpose="Retirement savings",
            cash_balance=Decimal("5000.00"),
        )

        assert account.account_name == "My 401k"
        assert account.account_purpose == "Retirement savings"
        assert account.cash_balance == Decimal("5000.00")

    def test_account_validates_cash_balance(self):
        """Test that negative cash balance is rejected"""
        with pytest.raises(ValidationError):
            AccountCreate(
                account_name="My Account",
                cash_balance=Decimal("-100.00"),
            )


class TestPositionCreate:
    """Test PositionCreate schema validation"""

    def test_valid_position_create(self):
        """Test creating valid position schema"""
        position = PositionCreate(
            account_id="acc_123",
            symbol="VTI",
            quantity=Decimal("100.5"),
        )

        assert position.account_id == "acc_123"
        assert position.symbol == "VTI"
        assert position.quantity == Decimal("100.5")

    def test_position_validates_quantity(self):
        """Test that zero/negative quantity is rejected"""
        with pytest.raises(ValidationError):
            PositionCreate(
                account_id="acc_123",
                symbol="VTI",
                quantity=Decimal("-10.0"),
            )


class TestJobCreate:
    """Test JobCreate schema validation"""

    def test_valid_job_create(self):
        """Test creating valid job schema"""
        job = JobCreate(
            clerk_user_id="clerk_123",
            job_type="portfolio_analysis",
            request_payload={"analysis_type": "full"}
        )

        assert job.clerk_user_id == "clerk_123"
        assert job.job_type == "portfolio_analysis"
        assert job.request_payload["analysis_type"] == "full"

    def test_job_create_optional_payload(self):
        """Test job creation without optional request_payload"""
        job = JobCreate(
            clerk_user_id="clerk_123",
            job_type="portfolio_analysis",
        )

        assert job.request_payload is None


class TestJobUpdate:
    """Test JobUpdate schema validation"""

    def test_valid_job_update(self):
        """Test creating valid job update schema"""
        update = JobUpdate(
            status="running"
        )

        assert update.status == "running"

    def test_job_update_with_result(self):
        """Test job update with result payload"""
        update = JobUpdate(
            status="completed",
            result_payload={"summary": "Analysis complete"}
        )

        assert update.result_payload is not None
        assert update.result_payload["summary"] == "Analysis complete"

    def test_job_update_with_error(self):
        """Test job update with error message"""
        update = JobUpdate(
            status="failed",
            error_message="Agent execution failed"
        )

        assert update.error_message == "Agent execution failed"

    def test_job_update_rejects_invalid_status(self):
        """Test that invalid status value is rejected"""
        with pytest.raises(ValidationError):
            JobUpdate(status="in_progress")  # Not a valid literal value


class TestJobStatus:
    """Test JobStatus literal type"""

    def test_job_status_values(self):
        """Test that all job status values are valid literals"""
        # JobStatus is Literal["pending", "running", "completed", "failed"]
        valid_statuses = ["pending", "running", "completed", "failed"]
        for status in valid_statuses:
            update = JobUpdate(status=status)
            assert update.status == status

    def test_job_status_in_schema(self):
        """Test using JobStatus in schema"""
        job = JobCreate(
            clerk_user_id="clerk_123",
            job_type="portfolio_analysis",
            request_payload={}
        )

        assert job.clerk_user_id == "clerk_123"
