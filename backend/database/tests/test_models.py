"""
Tests for database models and CRUD operations
"""

import pytest
from assertions import (
    assert_valid_portfolio_structure,
    assert_valid_job_structure
)


class TestUsersModel:
    """Test user model operations"""

    def test_create_user(self, mock_db, sample_user_data):
        """Test creating a new user"""
        user_id = mock_db.users.create(sample_user_data)

        assert user_id is not None
        assert isinstance(user_id, str)
        assert user_id.startswith("user_")

    def test_find_user_by_id(self, mock_db):
        """Test finding user by ID"""
        user = mock_db.users.find_by_id("user_001")

        assert user is not None
        assert user["id"] == "user_001"
        assert user["clerk_user_id"] == "test_user_001"
        assert user["email"] == "test@example.com"

    def test_find_user_by_clerk_id(self, mock_db):
        """Test finding user by Clerk ID"""
        user = mock_db.users.find_by_clerk_id("test_user_001")

        assert user is not None
        assert user["clerk_user_id"] == "test_user_001"
        assert "display_name" in user

    def test_find_nonexistent_user(self, mock_db):
        """Test that finding nonexistent user returns None"""
        user = mock_db.users.find_by_id("nonexistent")
        assert user is None

        user = mock_db.users.find_by_clerk_id("nonexistent")
        assert user is None


class TestAccountsModel:
    """Test account model operations"""

    def test_create_account(self, mock_db, sample_account_data):
        """Test creating a new account"""
        account_id = mock_db.accounts.create(sample_account_data)

        assert account_id is not None
        assert isinstance(account_id, str)
        assert account_id.startswith("acc_")

    def test_find_account_by_id(self, mock_db):
        """Test finding account by ID"""
        account = mock_db.accounts.find_by_id("acc_001")

        assert account is not None
        assert account["id"] == "acc_001"
        assert "name" in account
        assert "cash_balance" in account

    def test_find_accounts_by_user(self, mock_db):
        """Test finding all accounts for a user"""
        accounts = mock_db.accounts.find_by_user("user_001")

        assert isinstance(accounts, list)
        assert len(accounts) > 0
        assert all(acc["user_id"] == "user_001" for acc in accounts)

    def test_account_has_cash_balance(self, mock_db):
        """Test that account has cash balance"""
        account = mock_db.accounts.find_by_id("acc_001")

        assert "cash_balance" in account
        assert isinstance(account["cash_balance"], (int, float))
        assert account["cash_balance"] >= 0


class TestPositionsModel:
    """Test position model operations"""

    def test_create_position(self, mock_db):
        """Test creating a new position"""
        position_data = {
            "account_id": "acc_001",
            "instrument_id": "inst_001",
            "quantity": 50.0,
            "cost_basis": 5000.0
        }
        position_id = mock_db.positions.create(position_data)

        assert position_id is not None
        assert isinstance(position_id, str)
        assert position_id.startswith("pos_")

    def test_find_positions_by_account(self, mock_db):
        """Test finding all positions for an account"""
        positions = mock_db.positions.find_by_account("acc_001")

        assert isinstance(positions, list)
        assert len(positions) > 0
        assert all(pos["account_id"] == "acc_001" for pos in positions)

    def test_position_has_quantity(self, mock_db):
        """Test that position has quantity"""
        positions = mock_db.positions.find_by_account("acc_001")

        assert len(positions) > 0
        position = positions[0]
        assert "quantity" in position
        assert isinstance(position["quantity"], (int, float))


class TestInstrumentsModel:
    """Test instrument model operations"""

    def test_create_instrument(self, mock_db, sample_instrument_data):
        """Test creating a new instrument"""
        instrument_id = mock_db.instruments.create(sample_instrument_data)

        assert instrument_id is not None
        assert isinstance(instrument_id, str)
        assert instrument_id.startswith("inst_")

    def test_find_instrument_by_symbol(self, mock_db):
        """Test finding instrument by symbol"""
        instrument = mock_db.instruments.find_by_symbol("VTI")

        assert instrument is not None
        assert instrument["symbol"] == "VTI"
        assert "name" in instrument
        assert "current_price" in instrument

    def test_instrument_has_price(self, mock_db):
        """Test that instrument has price"""
        instrument = mock_db.instruments.find_by_symbol("VTI")

        assert "current_price" in instrument
        assert isinstance(instrument["current_price"], (int, float))
        assert instrument["current_price"] > 0


class TestJobsModel:
    """Test job model operations"""

    def test_create_job(self, mock_db, sample_job_data):
        """Test creating a new job"""
        job_id = mock_db.jobs.create(sample_job_data)

        assert job_id is not None
        assert isinstance(job_id, str)
        assert job_id.startswith("job_")

    def test_find_job_by_id(self, mock_db, sample_job_data):
        """Test finding job by ID"""
        job_id = mock_db.jobs.create(sample_job_data)
        job = mock_db.jobs.find_by_id(job_id)

        assert job is not None
        assert job["id"] == job_id
        assert_valid_job_structure(job)

    def test_update_job_status(self, mock_db, sample_job_data):
        """Test updating job status"""
        job_id = mock_db.jobs.create(sample_job_data)

        # Update to in_progress
        success = mock_db.jobs.update_status(job_id, "in_progress")
        assert success is True

        job = mock_db.jobs.find_by_id(job_id)
        assert job["status"] == "in_progress"

        # Update to completed
        success = mock_db.jobs.update_status(job_id, "completed")
        assert success is True

        job = mock_db.jobs.find_by_id(job_id)
        assert job["status"] == "completed"

    def test_update_job_payload(self, mock_db, sample_job_data):
        """Test updating job payload fields"""
        job_id = mock_db.jobs.create(sample_job_data)

        report_payload = {"analysis": "Test report content"}
        success = mock_db.jobs.update_payload(job_id, "report_payload", report_payload)
        assert success is True

        job = mock_db.jobs.find_by_id(job_id)
        assert "report_payload" in job
        assert job["report_payload"] == report_payload

    def test_job_status_values(self, mock_db, sample_job_data):
        """Test that job status can be set to all valid values"""
        valid_statuses = ["pending", "in_progress", "completed", "failed"]

        for status in valid_statuses:
            job_data = {**sample_job_data, "status": status}
            job_id = mock_db.jobs.create(job_data)
            job = mock_db.jobs.find_by_id(job_id)

            assert job["status"] == status


class TestDatabaseIntegration:
    """Test database integration scenarios"""

    def test_complete_portfolio_structure(self, mock_db):
        """Test retrieving complete portfolio with all relationships"""
        # Get user
        user = mock_db.users.find_by_clerk_id("test_user_001")
        assert user is not None

        # Get user's accounts
        accounts = mock_db.accounts.find_by_user(user["id"])
        assert len(accounts) > 0

        # Build portfolio structure
        portfolio = {"accounts": []}
        for account in accounts:
            account_data = {
                **account,
                "positions": []
            }

            # Get positions for this account
            positions = mock_db.positions.find_by_account(account["id"])
            for position in positions:
                # Get instrument for this position
                instrument = mock_db.instruments.find_by_symbol("VTI")
                if instrument:
                    position_data = {
                        **position,
                        "instrument": instrument
                    }
                    account_data["positions"].append(position_data)

            portfolio["accounts"].append(account_data)

        # Validate structure
        assert_valid_portfolio_structure(portfolio)

    def test_job_lifecycle(self, mock_db, sample_job_data):
        """Test complete job lifecycle"""
        # Create job
        job_id = mock_db.jobs.create(sample_job_data)
        job = mock_db.jobs.find_by_id(job_id)
        assert job["status"] == "pending"

        # Start processing
        mock_db.jobs.update_status(job_id, "in_progress")
        job = mock_db.jobs.find_by_id(job_id)
        assert job["status"] == "in_progress"

        # Add results
        mock_db.jobs.update_payload(job_id, "report_payload", {"analysis": "Test"})
        mock_db.jobs.update_payload(job_id, "charts_payload", {"chart1": {}})

        # Complete job
        mock_db.jobs.update_status(job_id, "completed")
        job = mock_db.jobs.find_by_id(job_id)

        assert job["status"] == "completed"
        assert "report_payload" in job
        assert "charts_payload" in job
