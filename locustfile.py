import random
from locust import HttpUser, task, between

class PsychPlatformUser(HttpUser):
    wait_time = between(1, 5)  # Simulate user thinking time
    
    def on_start(self):
        """
        Executed when a simulated user starts.
        We'll register/login here.
        """
        self.username = f"load_test_user_{random.randint(1, 100000)}"
        self.password = "TestPass123!"
        
        # 1. Login
        # Since we use JWT, we need to capture the token
        response = self.client.post("/api/login/", json={
            "username": "admin", # Using admin for simplicity in this test
            "password": "Ballveer123@"
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}

    @task(3)
    def view_dashboard(self):
        """Simulate viewing the dashboard and current activities"""
        self.client.get("/api/activities/daily/current/", headers=self.headers)
        self.client.get("/api/phases/current/", headers=self.headers)

    @task(2)
    def view_profile(self):
        """Simulate checking the profile"""
        self.client.get("/api/users/profile/", headers=self.headers)

    @task(1)
    def list_notifications(self):
        """Simulate checking notifications"""
        self.client.get("/api/notifications/", headers=self.headers)

    @task(1)
    def fetch_questionnaires(self):
        """Simulate loading the questionnaire list"""
        self.client.get("/api/questionnaires/", headers=self.headers)
