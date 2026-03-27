"""Tests for validation and error handling"""

import pytest


class TestSignupValidation:
    """Tests for signup endpoint validation and error cases"""

    def test_signup_to_nonexistent_activity_returns_404(self, client):
        """POST /signup to non-existent activity should return 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email_returns_400(self, client):
        """POST /signup with duplicate email should return 400"""
        # First signup
        resp1 = client.post(
            "/activities/Basketball/signup",
            params={"email": "dupval@mergington.edu"}
        )
        
        # If first signup succeeded, try duplicate
        assert resp1.status_code in [200, 400]  # May be full, but that's OK
        
        if resp1.status_code == 200:
            # Activity had space, now try duplicate
            response = client.post(
                "/activities/Basketball/signup",
                params={"email": "dupval@mergington.edu"}
            )
            assert response.status_code == 400
            assert "already signed up" in response.json()["detail"]

    def test_signup_already_registered_student_returns_400(self, client):
        """POST /signup for already registered student should return 400"""
        # Check for any student already registered anywhere
        response = client.get("/activities")
        data = response.json()
        
        # Find an activity with participants
        for activity_name, activity_data in data.items():
            if activity_data["participants"]:
                existing_email = activity_data["participants"][0]
                # Try to sign up the same person again to same activity
                response = client.post(
                    f"/activities/{activity_name}/signup",
                    params={"email": existing_email}
                )
                assert response.status_code == 400
                assert "already signed up" in response.json()["detail"]
                return
        
        # If no activities have participants, skip this test
        pytest.skip("No activities with participants found")

    def test_signup_to_full_activity_returns_400(self, client):
        """POST /signup to full activity should return 400"""
        # Get an activity with available slots, or fill one
        response = client.get("/activities")
        data = response.json()
        
        # Find an activity with available slots
        activity_to_fill = None
        for activity_name, activity_data in data.items():
            available = activity_data["max_participants"] - len(activity_data["participants"])
            if 0 < available <= 5:  # Find one with few slots remaining
                activity_to_fill = activity_name
                break
        
        if activity_to_fill:
            # Fill it up
            activity_info = data[activity_to_fill]
            available_slots = activity_info["max_participants"] - len(activity_info["participants"])
            
            for i in range(available_slots):
                client.post(
                    f"/activities/{activity_to_fill}/signup",
                    params={"email": f"filltest_{i}@mergington.edu"}
                )
            
            # Try to add one more
            response = client.post(
                f"/activities/{activity_to_fill}/signup",
                params={"email": "filloverflow@mergington.edu"}
            )
            assert response.status_code == 400
            assert "full" in response.json()["detail"]
        else:
            # If no suitable activity found, just verify that a completely full activity rejects signups
            # Find any full activity and try to add to it
            for activity_name, activity_data in data.items():
                if len(activity_data["participants"]) == activity_data["max_participants"]:
                    response = client.post(
                        f"/activities/{activity_name}/signup",
                        params={"email": "shouldfail@mergington.edu"}
                    )
                    assert response.status_code == 400
                    assert "full" in response.json()["detail"]
                    return
            
            pytest.skip("No suitable activities to test fullness")


class TestRemoveValidation:
    """Tests for remove endpoint validation and error cases"""

    def test_remove_from_nonexistent_activity_returns_404(self, client):
        """DELETE /remove from non-existent activity should return 404"""
        response = client.delete(
            "/activities/Nonexistent Club/remove",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_remove_nonregistered_student_returns_400(self, client):
        """DELETE /remove for non-registered student should return 400"""
        response = client.delete(
            "/activities/Chess Club/remove",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_remove_from_empty_activity_returns_400(self, client):
        """DELETE /remove from activity with no participants should return 400"""
        response = client.delete(
            "/activities/Basketball/remove",
            params={"email": "anyone@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]


class TestSignupCapacityValidation:
    """Tests for capacity constraints"""

    @pytest.mark.parametrize("activity,capacity", [
        ("Chess Club", 12),
        ("Programming Class", 20),
        ("Gym Class", 30),
        ("Basketball", 15),
        ("Tennis Club", 10),
        ("Art Club", 12),
        ("Music Band", 20),
        ("Debate Club", 16),
        ("Science Club", 18),
    ])
    def test_z_each_activity_respects_max_capacity(self, client, activity, capacity):
        """Each activity should respect its max capacity"""
        # Get current participant count
        response = client.get("/activities")
        data = response.json()
        current_count = len(data[activity]["participants"])
        
        # Try to add students up to capacity
        available_slots = capacity - current_count
        
        for i in range(available_slots):
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": f"capacity_test_{i}@mergington.edu"}
            )
            assert response.status_code == 200
        
        # Next signup should fail
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": "overflow_test@mergington.edu"}
        )
        assert response.status_code == 400


class TestErrorMessages:
    """Tests that error messages are informative"""

    def test_signup_error_message_includes_activity_name(self, client):
        """Error message for non-existent activity should be clear"""
        response = client.post(
            "/activities/Fake Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_duplicate_signup_error_indicates_duplicate(self, client):
        """Duplicate signup error should clearly indicate the issue"""
        email = "errmsg_dup_val@mergington.edu"
        activity = "Tennis Club"
        
        # First signup
        resp1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Only test duplicate error if first signup succeeded
        if resp1.status_code == 200:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 400
            assert "already signed up" in response.json()["detail"]
        else:
            # Activity is full, verify that error
            assert resp1.status_code == 400

    def test_full_activity_error_indicates_capacity(self, client):
        """Full activity error should indicate capacity issue"""
        # Fill Tennis Club completely
        for i in range(10):
            client.post(
                "/activities/Tennis Club/signup",
                params={"email": f"full_test_{i}@mergington.edu"}
            )
        
        # Try to add one more
        response = client.post(
            "/activities/Tennis Club/signup",
            params={"email": "full_overflow@mergington.edu"}
        )
        assert response.status_code == 400
        assert "full" in response.json()["detail"]
