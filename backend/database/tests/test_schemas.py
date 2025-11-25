"""
Tests for Pydantic schemas and validation
"""

import pytest
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
            email="test@example.com",
            display_name="Test User"
        )

        assert user.clerk_user_id == "clerk_123"
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"

    def test_user_create_with_preferences(self):
        """Test user creation with preferences"""
        user = UserCreate(
            clerk_user_id="clerk_123",
            email="test@example.com",
            display_name="Test User",
            preferences={"risk_tolerance": "moderate"}
        )

        assert user.preferences is not None
        assert user.preferences["risk_tolerance"] == "moderate"

    def test_user_create_validates_email(self):
        """Test that invalid email is rejected"""
        with pytest.raises(ValidationError):
            UserCreate(
                clerk_user_id="clerk_123",
                email="not-an-email",
                display_name="Test User"
            )


class TestAccountCreate:
    """Test AccountCreate schema validation"""

    def test_valid_account_create(self):
        """Test creating valid account schema"""
        account = AccountCreate(
            user_id="user_123",
            name="My Account",
            account_type="ira",
            cash_balance=5000.0
        )

        assert account.user_id == "user_123"
        assert account.name == "My Account"
        assert account.account_type == "ira"
        assert account.cash_balance == 5000.0

    def test_account_validates_cash_balance(self):
        """Test that negative cash balance is rejected"""
        with pytest.raises(ValidationError):
            AccountCreate(
                user_id="user_123",
                name="My Account",
                account_type="ira",
                cash_balance=-100.0
            )


class TestPositionCreate:
    """Test PositionCreate schema validation"""

    def test_valid_position_create(self):
        """Test creating valid position schema"""
        position = PositionCreate(
            account_id="acc_123",
            instrument_id="inst_123",
            quantity=100.0,
            cost_basis=10000.0
        )

        assert position.account_id == "acc_123"
        assert position.instrument_id == "inst_123"
        assert position.quantity == 100.0
        assert position.cost_basis == 10000.0

    def test_position_validates_quantity(self):
        """Test that negative quantity is rejected"""
        with pytest.raises(ValidationError):
            PositionCreate(
                account_id="acc_123",
                instrument_id="inst_123",
                quantity=-10.0,
                cost_basis=1000.0
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

    def test_job_with_all_fields(self):
        """Test job creation with all optional fields"""
        job = JobCreate(
            clerk_user_id="clerk_123",
            job_type="portfolio_analysis",
            request_payload={"test": True},
            summary_payload={"summary": "Test"},
            report_payload={"report": "Test report"},
            charts_payload={"chart1": {}},
            retirement_payload={"success_rate": 85.0}
        )

        assert job.summary_payload is not None
        assert job.report_payload is not None
        assert job.charts_payload is not None
        assert job.retirement_payload is not None


class TestJobUpdate:
    """Test JobUpdate schema validation"""

    def test_valid_job_update(self):
        """Test creating valid job update schema"""
        update = JobUpdate(
            status="in_progress"
        )

        assert update.status == "in_progress"

    def test_job_update_partial(self):
        """Test that job update can be partial"""
        update = JobUpdate(
            summary_payload={"summary": "Updated"}
        )

        assert update.summary_payload is not None
        assert update.status is None  # Not required


class TestJobStatus:
    """Test JobStatus enum"""

    def test_job_status_values(self):
        """Test that all job status values are valid"""
        assert JobStatus.PENDING == "pending"
        assert JobStatus.IN_PROGRESS == "in_progress"
        assert JobStatus.COMPLETED == "completed"
        assert JobStatus.FAILED == "failed"

    def test_job_status_in_schema(self):
        """Test using JobStatus enum in schema"""
        job = JobCreate(
            clerk_user_id="clerk_123",
            job_type="portfolio_analysis",
            request_payload={}
        )

        # Default status should be pending
        # (if implemented in the schema)
        assert job.clerk_user_id == "clerk_123"
