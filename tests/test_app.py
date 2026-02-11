"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create a test client
client = TestClient(app)


class TestActivityEndpoints:
    """Test suite for activity-related endpoints"""

    def test_root_redirect(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]

    def test_get_activities(self):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Check that activities exist
        assert len(activities) > 0
        
        # Check structure of activities
        assert "Chess Club" in activities
        chess_club = activities["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club

    def test_get_activities_contains_expected_activities(self):
        """Test that expected activities are present"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Soccer Club",
            "Art Class",
            "Drama Club",
            "Debate Team",
            "Science Club"
        ]
        
        for activity in expected_activities:
            assert activity in activities


class TestSignupEndpoint:
    """Test suite for signup endpoint"""

    def test_signup_for_activity(self):
        """Test signing up for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_duplicate(self):
        """Test that duplicate signups are prevented"""
        # First signup
        client.post(
            "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
        )
        
        # Try to signup again with same email
        response = client.post(
            "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_adds_participant_to_activity(self):
        """Test that signup actually adds participant to activity"""
        email = "newparticipant@mergington.edu"
        
        # Get initial count
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()["Programming Class"]["participants"].copy()
        initial_count = len(initial_participants)
        
        # Sign up
        response = client.post(
            f"/activities/Programming%20Class/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant was added
        final_response = client.get("/activities")
        final_participants = final_response.json()["Programming Class"]["participants"]
        assert len(final_participants) == initial_count + 1
        assert email in final_participants


class TestUnregisterEndpoint:
    """Test suite for unregister endpoint"""

    def test_unregister_from_activity(self):
        """Test unregistering from an activity"""
        email = "unregister@mergington.edu"
        
        # First sign up
        client.post(
            f"/activities/Art%20Class/signup?email={email}"
        )
        
        # Then unregister
        response = client.delete(
            f"/activities/Art%20Class/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_nonexistent_activity(self):
        """Test unregister from non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_nonexistent_participant(self):
        """Test unregister for non-existent participant"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found" in data["detail"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes participant"""
        email = "removetest@mergington.edu"
        
        # Sign up
        client.post(
            f"/activities/Drama%20Club/signup?email={email}"
        )
        
        # Get count before unregister
        before_response = client.get("/activities")
        before_count = len(before_response.json()["Drama Club"]["participants"])
        
        # Unregister
        response = client.delete(
            f"/activities/Drama%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        after_response = client.get("/activities")
        after_participants = after_response.json()["Drama Club"]["participants"]
        assert len(after_participants) == before_count - 1
        assert email not in after_participants
