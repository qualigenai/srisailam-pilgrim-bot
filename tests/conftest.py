import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TEST_PHONE = "whatsapp:+910000000000"
TEST_PHONE_2 = "whatsapp:+910000000001"

@pytest.fixture(autouse=True)
def clear_sessions():
    from app.utils.session_store import sessions
    sessions.clear()
    yield
    sessions.clear()

@pytest.fixture
def test_phone():
    return TEST_PHONE

@pytest.fixture
def test_phone_2():
    return TEST_PHONE_2