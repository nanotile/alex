"""
Mock objects for testing Alex agents without AWS dependencies
"""

from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any, List, Optional
import json


class MockLiteLLM:
    """Mock LiteLLM model for testing agent logic without Bedrock"""

    def __init__(self, model_id="bedrock/test-model", response_text="Mock AI response"):
        self.model_id = model_id
        self.response_text = response_text
        self.call_count = 0
        self.last_messages = None

    async def complete(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mock completion response"""
        self.call_count += 1
        self.last_messages = messages

        return {
            "choices": [{
                "message": {
                    "content": self.response_text,
                    "role": "assistant"
                }
            }],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }

    def set_response(self, text: str):
        """Set the mock response text"""
        self.response_text = text


class MockDatabase:
    """Mock Database for testing without Aurora Data API"""

    def __init__(self):
        self.users = MockUsersModel()
        self.accounts = MockAccountsModel()
        self.positions = MockPositionsModel()
        self.instruments = MockInstrumentsModel()
        self.jobs = MockJobsModel()
        self._data = {
            'users': {},
            'accounts': {},
            'positions': {},
            'instruments': {},
            'jobs': {}
        }

    def setup_test_data(self):
        """Setup standard test data"""
        # Create test user
        user_id = self.users.create({
            'clerk_user_id': 'test_user_001',
            'email': 'test@example.com',
            'display_name': 'Test User',
            'preferences': {'risk_tolerance': 'moderate'}
        })

        # Create test account
        account_id = self.accounts.create({
            'user_id': user_id,
            'name': 'Test Retirement Account',
            'account_type': 'ira',
            'cash_balance': 5000.0
        })

        # Create test instrument
        instrument_id = self.instruments.create({
            'symbol': 'VTI',
            'name': 'Vanguard Total Stock Market ETF',
            'instrument_type': 'etf',
            'asset_class': 'equity',
            'current_price': 220.0
        })

        # Create test position
        self.positions.create({
            'account_id': account_id,
            'instrument_id': instrument_id,
            'symbol': 'VTI',
            'quantity': 100.0,
            'cost_basis': 20000.0
        })

        return user_id, account_id


class MockUsersModel:
    """Mock users model"""
    def __init__(self):
        self._data = {}
        self._counter = 1

    def create(self, data: Dict[str, Any]) -> str:
        user_id = f"user_{self._counter:03d}"
        self._counter += 1
        self._data[user_id] = {**data, 'id': user_id}
        return user_id

    def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._data.get(user_id)

    def find_by_clerk_id(self, clerk_id: str) -> Optional[Dict[str, Any]]:
        for user in self._data.values():
            if user.get('clerk_user_id') == clerk_id:
                return user
        return None


class MockAccountsModel:
    """Mock accounts model"""
    def __init__(self):
        self._data = {}
        self._counter = 1

    def create(self, data: Dict[str, Any]) -> str:
        account_id = f"acc_{self._counter:03d}"
        self._counter += 1
        self._data[account_id] = {**data, 'id': account_id}
        return account_id

    def find_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        return self._data.get(account_id)

    def find_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        return [acc for acc in self._data.values() if acc.get('user_id') == user_id]


class MockPositionsModel:
    """Mock positions model"""
    def __init__(self):
        self._data = {}
        self._counter = 1

    def create(self, data: Dict[str, Any]) -> str:
        position_id = f"pos_{self._counter:03d}"
        self._counter += 1
        self._data[position_id] = {**data, 'id': position_id}
        return position_id

    def find_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        return [pos for pos in self._data.values() if pos.get('account_id') == account_id]


class MockInstrumentsModel:
    """Mock instruments model"""
    def __init__(self):
        self._data = {}
        self._counter = 1

    def create(self, data: Dict[str, Any]) -> str:
        instrument_id = f"inst_{self._counter:03d}"
        self._counter += 1
        self._data[instrument_id] = {**data, 'id': instrument_id}
        return instrument_id

    def find_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        for inst in self._data.values():
            if inst.get('symbol') == symbol:
                return inst
        return None


class MockJobsModel:
    """Mock jobs model"""
    def __init__(self):
        self._data = {}
        self._counter = 1

    def create(self, data: Dict[str, Any]) -> str:
        job_id = f"job_{self._counter:03d}"
        self._counter += 1
        self._data[job_id] = {
            **data,
            'id': job_id,
            'status': data.get('status', 'pending')
        }
        return job_id

    def find_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._data.get(job_id)

    def update_status(self, job_id: str, status: str) -> bool:
        if job_id in self._data:
            self._data[job_id]['status'] = status
            return True
        return False

    def update_payload(self, job_id: str, field: str, payload: Dict[str, Any]) -> bool:
        if job_id in self._data:
            self._data[job_id][field] = payload
            return True
        return False


class MockSQS:
    """Mock SQS client for testing queue operations"""

    def __init__(self):
        self.messages = []
        self.sent_messages = []

    def send_message(self, QueueUrl: str, MessageBody: str) -> Dict[str, Any]:
        """Mock send_message"""
        message_id = f"msg_{len(self.sent_messages) + 1:03d}"
        self.sent_messages.append({
            'MessageId': message_id,
            'QueueUrl': QueueUrl,
            'Body': MessageBody
        })
        return {
            'MessageId': message_id,
            'MD5OfMessageBody': 'mock_md5'
        }

    def receive_message(self, QueueUrl: str, **kwargs) -> Dict[str, Any]:
        """Mock receive_message"""
        if self.messages:
            return {'Messages': [self.messages.pop(0)]}
        return {}


class MockLambda:
    """Mock Lambda client for testing agent invocations"""

    def __init__(self):
        self.invocations = []
        self.responses = {}

    def invoke(self, FunctionName: str, InvocationType: str, Payload: bytes) -> Dict[str, Any]:
        """Mock Lambda invocation"""
        payload = json.loads(Payload)

        self.invocations.append({
            'FunctionName': FunctionName,
            'InvocationType': InvocationType,
            'Payload': payload
        })

        # Return mock response
        response_payload = self.responses.get(FunctionName, {
            'statusCode': 200,
            'body': json.dumps({'success': True, 'message': 'Mock response'})
        })

        return {
            'StatusCode': 200,
            'Payload': MockPayload(json.dumps(response_payload))
        }

    def set_response(self, function_name: str, response: Dict[str, Any]):
        """Set mock response for a specific function"""
        self.responses[function_name] = response


class MockPayload:
    """Mock Lambda payload response"""
    def __init__(self, data: str):
        self._data = data

    def read(self) -> bytes:
        return self._data.encode()
