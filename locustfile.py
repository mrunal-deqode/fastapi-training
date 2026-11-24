import os

# from locust import HttpUser, StopUser, between, task
from locust import HttpUser, between, task
from locust.exception import StopUser


class RecruitmentUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        email = os.getenv("LOCUST_EMAIL")
        password = os.getenv("LOCUST_PASSWORD")

        if not email or not password:
            raise StopUser("Set LOCUST_EMAIL and LOCUST_PASSWORD first.")

        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
            name="/api/v1/auth/login",
        )

        if response.status_code != 200:
            raise StopUser("Candidate login failed. Check test credentials.")

        token = response.json().get("access_token")
        if not token:
            raise StopUser("Login response did not contain an access token.")

        self.client.headers.update(
            {"Authorization": f"Bearer {token}"}
        )
        self.job_id = None

    @task(3)
    def list_jobs(self):
        with self.client.get(
            "/api/v1/jobs",
            name="/api/v1/jobs",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status: {response.status_code}")
                return

            try:
                items = response.json().get("items", [])
                if items:
                    self.job_id = items[0].get("id")
                response.success()
            except (ValueError, AttributeError):
                response.failure("Invalid jobs response")

    @task(2)
    def job_details(self):
        if self.job_id is None:
            return

        with self.client.get(
            f"/api/v1/jobs/{self.job_id}",
            name="/api/v1/jobs/[job_id]",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status: {response.status_code}")
            else:
                response.success()

    @task(1)
    def my_applications(self):
        with self.client.get(
            "/api/v1/applications/my-applications",
            name="/api/v1/applications/my-applications",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status: {response.status_code}")
            else:
                response.success()
