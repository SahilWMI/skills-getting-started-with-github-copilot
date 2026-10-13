from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


TEST_ACTIVITIES = {
    "Chess Club": {
        "description": "Play chess",
        "schedule": "Mondays",
        "max_participants": 3,
        "participants": ["existing@example.com", "other@example.com"],
    },
    "Art Workshop": {
        "description": "Make art",
        "schedule": "Tuesdays",
        "max_participants": 2,
        "participants": [],
    },
}


@pytest.fixture

def activities(monkeypatch):
    isolated_activities = deepcopy(TEST_ACTIVITIES)
    monkeypatch.setattr(app_module, "activities", isolated_activities)
    return isolated_activities


@pytest.fixture

def client():
    return TestClient(app_module.app)


def test_get_activities_returns_current_activities(client, activities):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activities


def test_signup_adds_participant(client, activities):
    response = client.post(
        "/activities/Art%20Workshop/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up student@example.com for Art Workshop"
    }
    assert "student@example.com" in activities["Art Workshop"]["participants"]


def test_signup_rejects_duplicate_without_mutating_participants(client, activities):
    participants_before = activities["Chess Club"]["participants"].copy()

    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert activities["Chess Club"]["participants"] == participants_before


def test_signup_returns_not_found_for_unknown_activity(client, activities):
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant_and_keeps_others(client, activities):
    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered existing@example.com from Chess Club"
    }
    assert activities["Chess Club"]["participants"] == ["other@example.com"]


def test_unregister_returns_not_found_for_unknown_activity(client, activities):
    response = client.delete(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_not_found_for_unregistered_email(client, activities):
    participants_before = activities["Chess Club"]["participants"].copy()

    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert activities["Chess Club"]["participants"] == participants_before
