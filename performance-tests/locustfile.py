from locust import HttpUser, between, task


class CapitalQualityApiUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_ranking_all(self):
        self.client.get("/ranking", name="/ranking")

    @task(2)
    def get_ranking_europe(self):
        self.client.get("/ranking?continent=Europe", name="/ranking?continent=Europe")

    @task(2)
    def get_ranking_asia(self):
        self.client.get("/ranking?continent=Asia", name="/ranking?continent=Asia")

    @task(1)
    def get_cities(self):
        self.client.get("/cities", name="/cities")

    @task(1)
    def get_health(self):
        self.client.get("/health", name="/health")

    @task(1)
    def get_city_history(self):
        # Przykładowe ID. Jeśli nie istnieje, zmień na ID miasta z Twojej bazy.
        self.client.get("/cities/1/history?limit=20", name="/cities/{id}/history")
