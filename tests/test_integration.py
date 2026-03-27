"""Integration tests - multi-step scenarios and workflows"""


class TestMultipleActivitiesWorkflow:
    """Tests for students managing multiple activity registrations"""

    def test_student_can_signup_for_multiple_activities(self, client):
        """A student should be able to sign up for multiple different activities"""
        email = "multistudy@mergington.edu"
        activities = ["Basketball", "Art Club", "Science Club"]
        
        # Sign up for multiple activities
        for activity in activities:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all signups are recorded
        response = client.get("/activities")
        data = response.json()
        
        for activity in activities:
            assert email in data[activity]["participants"]

    def test_student_can_remove_one_activity_while_keeping_others(self, client):
        """Removing from one activity should not affect other signups"""
        email = "multimanage@mergington.edu"
        activities = ["Basketball", "Tennis Club", "Debate Club"]
        
        # Sign up for multiple activities
        for activity in activities:
            client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
        
        # Remove from one activity
        client.delete(
            "/activities/Tennis Club/remove",
            params={"email": email}
        )
        
        # Verify other signups are still there
        response = client.get("/activities")
        data = response.json()
        
        assert email not in data["Tennis Club"]["participants"]
        assert email in data["Basketball"]["participants"]
        assert email in data["Debate Club"]["participants"]


class TestCapacityEdgeCases:
    """Tests for capacity management edge cases"""

    def test_exactly_fill_activity_then_fail_to_add_one_more(self, client):
        """Adding one student at a time up to capacity should work, then fail"""
        activity = "Art Club"  # max 12 participants
        
        # Get current count
        response = client.get("/activities")
        data = response.json()
        current_count = len(data[activity]["participants"])
        
        # Add students one at a time until full
        for i in range(12 - current_count):
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": f"art_student_{i}@mergington.edu"}
            )
            assert response.status_code == 200, f"Failed at student {i}"
        
        # Verify activity is now full
        response = client.get("/activities")
        data = response.json()
        assert len(data[activity]["participants"]) == 12
        
        # Try to add one more (should fail)
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": "art_overflow@mergington.edu"}
        )
        assert response.status_code == 400

    def test_remove_creates_space_for_new_signup(self, client):
        """Removing a participant should free up space for new signup"""
        activity = "Music Band"  # max 20 participants
        
        # Fill it up
        for i in range(20):
            client.post(
                f"/activities/{activity}/signup",
                params={"email": f"musician_{i}@mergington.edu"}
            )
        
        # Verify it's full
        response = client.get("/activities")
        data = response.json()
        assert len(data[activity]["participants"]) == 20
        
        # Remove one
        client.delete(
            f"/activities/{activity}/remove",
            params={"email": "musician_0@mergington.edu"}
        )
        
        # Verify we can now add a new one
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": "newmusician@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Verify final state
        response = client.get("/activities")
        data = response.json()
        assert len(data[activity]["participants"]) == 20
        assert "musician_0@mergington.edu" not in data[activity]["participants"]
        assert "newmusician@mergington.edu" in data[activity]["participants"]


class TestComplexScenarios:
    """Tests for complex real-world scenarios"""

    def test_multiple_students_signup_and_some_remove(self, client):
        """Complex scenario: many students sign up and some remove"""
        activity = "Science Club"
        
        # Multiple students sign up
        emails = [f"scientist_{i}@mergington.edu" for i in range(5)]
        for email in emails:
            client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
        
        # Some students change their minds
        remove_emails = [emails[1], emails[3]]
        for email in remove_emails:
            client.delete(
                f"/activities/{activity}/remove",
                params={"email": email}
            )
        
        # Verify final state
        response = client.get("/activities")
        data = response.json()
        
        for email in emails:
            if email in remove_emails:
                assert email not in data[activity]["participants"]
            else:
                assert email in data[activity]["participants"]

    def test_concurrent_activities_maintaining_separate_state(self, client):
        """Different activities should maintain independent participant lists"""
        student = "versatile@mergington.edu"
        
        # Sign up for 3 activities
        activity1 = "Chess Club"
        activity2 = "Programming Class"
        activity3 = "Gym Class"
        
        client.post(f"/activities/{activity1}/signup", params={"email": student})
        client.post(f"/activities/{activity2}/signup", params={"email": student})
        client.post(f"/activities/{activity3}/signup", params={"email": student})
        
        # Remove from one
        client.delete(f"/activities/{activity2}/remove", params={"email": student})
        
        # Verify independent state
        response = client.get("/activities")
        data = response.json()
        
        assert student in data[activity1]["participants"]
        assert student not in data[activity2]["participants"]
        assert student in data[activity3]["participants"]

    def test_activity_state_transitions(self, client):
        """Test activity transitions: empty -> partial -> full -> partial"""
        activity = "Debate Club"  # max 16
        
        # Stage 1: Empty (verify initial state - may have existing participants)
        response = client.get("/activities")
        data = response.json()
        initial_count = len(data[activity]["participants"])
        
        # Stage 2: Add many students (partial fill)
        new_students = []
        for i in range(10):
            email = f"debater_{i}@mergington.edu"
            new_students.append(email)
            client.post(f"/activities/{activity}/signup", params={"email": email})
        
        # Stage 3: Verify many students added
        response = client.get("/activities")
        data = response.json()
        assert len(data[activity]["participants"]) == initial_count + 10
        
        # Stage 4: Remove some
        for email in new_students[:5]:
            client.delete(f"/activities/{activity}/remove", params={"email": email})
        
        # Stage 5: Verify correct removal
        response = client.get("/activities")
        data = response.json()
        final_count = len(data[activity]["participants"])
        assert final_count == initial_count + 5
        
        # Remove all new students
        for email in new_students[5:]:
            client.delete(f"/activities/{activity}/remove", params={"email": email})
        
        # Stage 6: Verify back to initial state
        response = client.get("/activities")
        data = response.json()
        assert len(data[activity]["participants"]) == initial_count
