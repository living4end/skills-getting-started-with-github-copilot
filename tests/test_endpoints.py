"""Tests for API endpoints - happy path scenarios"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self, client):
        """GET /activities should return 200 OK"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """GET /activities should return a dictionary of activities"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)

    def test_get_activities_has_all_activities(self, client):
        """GET /activities should include all 9 activities"""
        response = client.get("/activities")
        data = response.json()
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class",
            "Basketball", "Tennis Club", "Art Club",
            "Music Band", "Debate Club", "Science Club"
        ]
        for activity in expected_activities:
            assert activity in data

    def test_get_activities_includes_activity_details(self, client):
        """Each activity should have required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_index(self, client):
        """GET / should redirect to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_valid_student_returns_200(self, client):
        """POST /signup with valid data should return 200"""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "alice@mergington.edu"}
        )
        assert response.status_code == 200

    def test_signup_valid_student_returns_success_message(self, client):
        """POST /signup should return success message"""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "msg_test_alice@mergington.edu"}
        )
        data = response.json()
        assert "message" in data
        assert "msg_test_alice@mergington.edu" in data["message"]
        assert "Basketball" in data["message"]

    def test_signup_adds_student_to_participants(self, client):
        """POST /signup should add email to participants list"""
        # First signup
        client.post(
            "/activities/Basketball/signup",
            params={"email": "addtest_bob@mergington.edu"}
        )
        
        # Verify student is in participants
        response = client.get("/activities")
        data = response.json()
        assert "addtest_bob@mergington.edu" in data["Basketball"]["participants"]

    def test_signup_multiple_students_to_same_activity(self, client):
        """Multiple students should be able to sign up for same activity"""
        students = ["multi_student1@mergington.edu", "multi_student2@mergington.edu", "multi_student3@mergington.edu"]
        
        for email in students:
            response = client.post(
                "/activities/Tennis Club/signup",
                params={"email": email}
            )
            assert response.status_code == 200

        # Verify all students are registered
        response = client.get("/activities")
        data = response.json()
        for email in students:
            assert email in data["Tennis Club"]["participants"]


class TestRemoveEndpoint:
    """Tests for DELETE /activities/{activity_name}/remove endpoint"""

    def test_remove_existing_participant_returns_200(self, client):
        """DELETE /remove for existing participant should return 200"""
        response = client.delete(
            "/activities/Chess Club/remove",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200

    def test_remove_existing_participant_returns_success_message(self, client):
        """DELETE /remove should return confirmation message"""
        # First add a participant we can remove
        client.post(
            "/activities/Basketball/signup",
            params={"email": "msg_remove_test@mergington.edu"}
        )
        
        response = client.delete(
            "/activities/Basketball/remove",
            params={"email": "msg_remove_test@mergington.edu"}
        )
        data = response.json()
        assert "message" in data
        assert "msg_remove_test@mergington.edu" in data["message"]
        assert "Basketball" in data["message"]

    def test_remove_deletes_participant_from_activity(self, client):
        """DELETE /remove should remove email from participants list"""
        # Verify student is initially registered
        response = client.get("/activities")
        data = response.json()
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        
        # Remove student
        client.delete(
            "/activities/Chess Club/remove",
            params={"email": "daniel@mergington.edu"}
        )
        
        # Verify student is no longer registered
        response = client.get("/activities")
        data = response.json()
        assert "daniel@mergington.edu" not in data["Chess Club"]["participants"]

    def test_remove_multiple_participants_sequentially(self, client):
        """Multiple participants can be removed from an activity"""
        # Get initial participants
        response = client.get("/activities")
        initial_count = len(response.json()["Programming Class"]["participants"])
        
        # Remove first participant
        client.delete(
            "/activities/Programming Class/remove",
            params={"email": "emma@mergington.edu"}
        )
        
        # Verify count decreased
        response = client.get("/activities")
        assert len(response.json()["Programming Class"]["participants"]) == initial_count - 1
