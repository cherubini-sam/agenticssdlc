"""Integration tests for the FastAPI app health, auth middleware, task CRUD, agents status."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealthEndpoints:
    def test_health_returns_200(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_liveness_returns_200(self, client: TestClient) -> None:
        resp = client.get("/liveness")
        assert resp.status_code == 200

    def test_readiness_returns_200(self, client: TestClient) -> None:
        resp = client.get("/readiness")
        assert resp.status_code in (200, 503)


class TestAuthMiddleware:
    def test_missing_api_key_returns_401(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/task",
            json={"content": "Hello"},
        )
        assert resp.status_code == 401

    def test_wrong_api_key_returns_403(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/task",
            json={"content": "Hello"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 403

    def test_correct_api_key_passes(self, client: TestClient, mock_manager) -> None:
        resp = client.post(
            "/api/v1/task",
            json={"content": "What is 2+2?"},
            headers={"X-API-Key": "test-key-123"},
        )
        assert resp.status_code == 200

    def test_health_bypasses_auth(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_metrics_bypasses_auth(self, client: TestClient) -> None:
        resp = client.get("/metrics")
        # 200 if prometheus is mounted, 404 otherwise -- either way, no 401/403
        assert resp.status_code not in (401, 403)


class TestTaskEndpoint:
    def test_post_task_success(self, client: TestClient, mock_manager) -> None:
        resp = client.post(
            "/api/v1/task",
            json={"content": "Explain async/await in Python"},
            headers={"X-API-Key": "test-key-123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("completed", "failed", "success")
        assert "result" in data
        assert "confidence" in data
        assert "latency_ms" in data
        assert isinstance(data["agent_trace"], list)

    def test_post_task_empty_content_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/task",
            json={"content": ""},
            headers={"X-API-Key": "test-key-123"},
        )
        assert resp.status_code == 422

    def test_get_task_returns_404(self, client: TestClient) -> None:
        resp = client.get(
            "/api/v1/task/nonexistent-id",
            headers={"X-API-Key": "test-key-123"},
        )
        assert resp.status_code == 404


class TestAgentsEndpoint:
    def test_agents_status_returns_six_agents(self, client: TestClient) -> None:
        resp = client.get(
            "/api/v1/agents/status",
            headers={"X-API-Key": "test-key-123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["agents"]) == 6
