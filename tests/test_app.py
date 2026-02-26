"""
Tests for the Mergington High School API.
"""
import copy
import pytest
from fastapi.testclient import TestClient

import app as app_module
from app import app

INITIAL_ACTIVITIES = None


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the activities dict to its original state before each test."""
    global INITIAL_ACTIVITIES
    if INITIAL_ACTIVITIES is None:
        INITIAL_ACTIVITIES = copy.deepcopy(app_module.activities)
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(INITIAL_ACTIVITIES))
    yield


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_200(client):
    response = client.get("/activities")
    assert response.status_code == 200


def test_get_activities_returns_dict(client):
    response = client.get("/activities")
    data = response.json()
    assert isinstance(data, dict)


def test_get_activities_contains_expected_activities(client):
    response = client.get("/activities")
    data = response.json()
    expected = [
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Soccer Team",
        "Swimming Club",
        "Art Club",
        "Drama Club",
        "Debate Team",
        "Science Club",
    ]
    for activity in expected:
        assert activity in data


def test_activity_has_required_fields(client):
    response = client.get("/activities")
    data = response.json()
    chess = data["Chess Club"]
    assert "description" in chess
    assert "schedule" in chess
    assert "max_participants" in chess
    assert "participants" in chess


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )
    assert response.status_code == 200
    assert "newstudent@mergington.edu" in response.json()["message"]


def test_signup_adds_participant(client):
    email = "newstudent@mergington.edu"
    client.post("/activities/Chess Club/signup", params={"email": email})
    response = client.get("/activities")
    participants = response.json()["Chess Club"]["participants"]
    assert email in participants


def test_signup_nonexistent_activity_returns_404(client):
    response = client.post(
        "/activities/Underwater Basket Weaving/signup",
        params={"email": "student@mergington.edu"},
    )
    assert response.status_code == 404


def test_signup_duplicate_returns_400(client):
    # michael@mergington.edu is already in Chess Club by default
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 400


def test_signup_when_activity_full(client):
    """Sign up exactly max_participants students; the next signup should fail."""
    activity_name = "Chess Club"
    max_participants = INITIAL_ACTIVITIES[activity_name]["max_participants"]
    existing = set(INITIAL_ACTIVITIES[activity_name]["participants"])
    # Fill remaining slots
    extra_added = 0
    for i in range(max_participants):
        email = f"filler{i}@mergington.edu"
        if email not in existing:
            client.post(f"/activities/{activity_name}/signup", params={"email": email})
            extra_added += 1
        current = client.get("/activities").json()[activity_name]["participants"]
        if len(current) >= max_participants:
            break

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "overflow@mergington.edu"},
    )
    # Full capacity should return 400
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_success(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 200
    assert "michael@mergington.edu" in response.json()["message"]


def test_unregister_removes_participant(client):
    email = "michael@mergington.edu"
    client.delete("/activities/Chess Club/signup", params={"email": email})
    response = client.get("/activities")
    participants = response.json()["Chess Club"]["participants"]
    assert email not in participants


def test_unregister_nonexistent_activity_returns_404(client):
    response = client.delete(
        "/activities/Nonexistent Club/signup",
        params={"email": "student@mergington.edu"},
    )
    assert response.status_code == 404


def test_unregister_not_enrolled_returns_404(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "notmember@mergington.edu"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET / redirect
# ---------------------------------------------------------------------------

def test_root_redirect(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (301, 302, 307, 308)
    assert "/static/index.html" in response.headers["location"]
