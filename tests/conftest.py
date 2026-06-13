import pytest
from backend.app import app
from backend.auth import get_current_user
from backend.models import User


@pytest.fixture(autouse=True)
def setup_dependency_overrides():
    # Provide a mock User with doctor role so that all role-based validations pass during testing
    mock_user = User(id=999, username="doctor", role="doctor")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.clear()
