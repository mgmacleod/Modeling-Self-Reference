"""Tests for health and status endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for /api/v1/health endpoint."""

    def test_health_returns_ok(self, test_client: TestClient) -> None:
        """Health check should return status ok."""
        response = test_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_is_fast(self, test_client: TestClient) -> None:
        """Health check should be fast (< 100ms)."""
        import time

        start = time.perf_counter()
        response = test_client.get("/api/v1/health")
        elapsed = time.perf_counter() - start

        assert response.status_code == 200
        assert elapsed < 0.1  # Should complete in under 100ms


class TestStatusEndpoint:
    """Tests for /api/v1/status endpoint."""

    def test_status_returns_ok(self, test_client: TestClient) -> None:
        """Status endpoint should return status ok."""
        response = test_client.get("/api/v1/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_status_includes_version(self, test_client: TestClient) -> None:
        """Status should include API version."""
        response = test_client.get("/api/v1/status")

        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)

    def test_status_includes_timestamp(self, test_client: TestClient) -> None:
        """Status should include timestamp."""
        response = test_client.get("/api/v1/status")

        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data

    def test_status_includes_data_info(self, test_client: TestClient) -> None:
        """Status should include data source information."""
        response = test_client.get("/api/v1/status")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "source" in data["data"]

    def test_status_includes_task_counts(self, test_client: TestClient) -> None:
        """Status should include task counts."""
        response = test_client.get("/api/v1/status")

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data["tasks"]
        assert "running" in data["tasks"]
        assert "pending" in data["tasks"]
        assert "completed" in data["tasks"]
        assert "failed" in data["tasks"]

    def test_status_includes_system_info(self, test_client: TestClient) -> None:
        """Status should include system information."""
        response = test_client.get("/api/v1/status")

        assert response.status_code == 200
        data = response.json()
        assert "system" in data
        assert "python_version" in data["system"]
        assert "platform" in data["system"]

    def test_status_includes_config(self, test_client: TestClient) -> None:
        """Status should include configuration info."""
        response = test_client.get("/api/v1/status")

        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert "max_workers" in data["config"]
