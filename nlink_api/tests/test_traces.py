"""Tests for trace sampling endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestTraceSingleEndpoint:
    """Tests for /api/v1/traces/single endpoint."""

    def test_trace_single_requires_start(self, test_client: TestClient) -> None:
        """Should require either start_title or start_page_id."""
        response = test_client.get("/api/v1/traces/single")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "start_title" in data["detail"] or "start_page_id" in data["detail"]

    @pytest.mark.integration
    def test_trace_single_by_page_id(self, test_client: TestClient) -> None:
        """Should trace from a page ID."""
        response = test_client.get(
            "/api/v1/traces/single",
            params={"start_page_id": 1, "n": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert "start_page_id" in data
        assert data["start_page_id"] == 1
        assert "terminal_type" in data
        assert data["terminal_type"] in ["HALT", "CYCLE", "MAX_STEPS"]
        assert "steps" in data
        assert "path" in data
        assert isinstance(data["path"], list)

    @pytest.mark.integration
    def test_trace_single_by_title(self, test_client: TestClient) -> None:
        """Should trace from a page title."""
        response = test_client.get(
            "/api/v1/traces/single",
            params={"start_title": "Massachusetts", "n": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert "start_page_id" in data
        assert "terminal_type" in data

    @pytest.mark.integration
    def test_trace_single_with_title_resolution(self, test_client: TestClient) -> None:
        """Should resolve titles when requested."""
        response = test_client.get(
            "/api/v1/traces/single",
            params={"start_page_id": 1, "n": 5, "resolve_titles": True}
        )

        assert response.status_code == 200
        data = response.json()
        # When resolve_titles is True, path_titles should be present
        if "path_titles" in data and data["path_titles"]:
            assert len(data["path_titles"]) == len(data["path"])

    @pytest.mark.integration
    def test_trace_single_cycle_detection(self, test_client: TestClient) -> None:
        """Should detect cycles in the trace."""
        # Our test data has Massachusetts(1)->Gulf(2)->Mass(1) cycle at N=5
        response = test_client.get(
            "/api/v1/traces/single",
            params={"start_page_id": 1, "n": 5, "max_steps": 100}
        )

        assert response.status_code == 200
        data = response.json()

        if data["terminal_type"] == "CYCLE":
            assert "cycle_start_index" in data
            assert "cycle_len" in data
            assert data["cycle_len"] >= 1

    @pytest.mark.integration
    def test_trace_single_invalid_page_id(self, test_client: TestClient) -> None:
        """Should handle invalid page ID gracefully."""
        response = test_client.get(
            "/api/v1/traces/single",
            params={"start_page_id": 99999, "n": 5}
        )

        # Could be 400 (bad request) or 200 with HALT terminal
        assert response.status_code in [200, 400]

    @pytest.mark.integration
    def test_trace_single_respects_max_steps(self, test_client: TestClient) -> None:
        """Should stop at max_steps if no cycle or halt found."""
        response = test_client.get(
            "/api/v1/traces/single",
            params={"start_page_id": 1, "n": 5, "max_steps": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["steps"] <= 10

    @pytest.mark.integration
    def test_trace_single_different_n_values(self, test_client: TestClient) -> None:
        """Should work with different N values."""
        for n in [1, 3, 5, 7]:
            response = test_client.get(
                "/api/v1/traces/single",
                params={"start_page_id": 1, "n": n}
            )
            assert response.status_code == 200


class TestTraceSampleEndpoint:
    """Tests for /api/v1/traces/sample endpoint."""

    @pytest.mark.integration
    def test_sample_traces_basic(self, test_client: TestClient) -> None:
        """Should sample traces successfully."""
        response = test_client.post(
            "/api/v1/traces/sample",
            json={"n": 5, "num_samples": 5}
        )

        assert response.status_code == 200
        data = response.json()

        # Could be sync response or task submission
        if "task_id" in data:
            # Background task was submitted
            assert "task_type" in data
            assert data["task_type"] == "trace_sample"
        else:
            # Sync response
            assert "n" in data
            assert "num_samples" in data
            assert "terminal_counts" in data

    @pytest.mark.integration
    def test_sample_traces_sync_for_small_requests(self, test_client: TestClient) -> None:
        """Small requests should run synchronously."""
        response = test_client.post(
            "/api/v1/traces/sample",
            json={"n": 5, "num_samples": 5, "seed": 42}
        )

        assert response.status_code == 200
        data = response.json()

        # With <=100 samples, should be sync
        assert "n" in data
        assert data["n"] == 5
        assert "terminal_counts" in data
        assert isinstance(data["terminal_counts"], dict)

    @pytest.mark.integration
    def test_sample_traces_includes_statistics(self, test_client: TestClient) -> None:
        """Should include statistical summaries."""
        response = test_client.post(
            "/api/v1/traces/sample",
            json={"n": 5, "num_samples": 5}
        )

        assert response.status_code == 200
        data = response.json()

        if "task_id" not in data:
            assert "avg_steps" in data
            assert "avg_path_len" in data

    @pytest.mark.integration
    def test_sample_traces_returns_top_cycles(self, test_client: TestClient) -> None:
        """Should return top cycles found."""
        response = test_client.post(
            "/api/v1/traces/sample",
            json={"n": 5, "num_samples": 10, "top_cycles_k": 5}
        )

        assert response.status_code == 200
        data = response.json()

        if "task_id" not in data:
            assert "top_cycles" in data
            assert isinstance(data["top_cycles"], list)

    def test_sample_traces_validation(self, test_client: TestClient) -> None:
        """Should validate request parameters."""
        # Invalid n value
        response = test_client.post(
            "/api/v1/traces/sample",
            json={"n": 0, "num_samples": 5}
        )
        assert response.status_code == 422

        # Invalid num_samples
        response = test_client.post(
            "/api/v1/traces/sample",
            json={"n": 5, "num_samples": 0}
        )
        assert response.status_code == 422

    @pytest.mark.integration
    def test_sample_traces_with_seed(self, test_client: TestClient) -> None:
        """Traces with same seed should be deterministic."""
        response1 = test_client.post(
            "/api/v1/traces/sample",
            json={"n": 5, "num_samples": 3, "seed": 12345}
        )
        response2 = test_client.post(
            "/api/v1/traces/sample",
            json={"n": 5, "num_samples": 3, "seed": 12345}
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # If both ran synchronously, results should be identical
        if "task_id" not in data1 and "task_id" not in data2:
            assert data1["terminal_counts"] == data2["terminal_counts"]


class TestTraceSampleTaskStatus:
    """Tests for trace sample task status endpoint."""

    def test_get_sample_task_not_found(self, test_client: TestClient) -> None:
        """Should return 404 for unknown task ID."""
        response = test_client.get("/api/v1/traces/sample/nonexistent-task-id")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestTraceSchemas:
    """Tests for trace Pydantic schemas."""

    def test_trace_single_request_defaults(self) -> None:
        """TraceSingleRequest should have sensible defaults."""
        from nlink_api.schemas.traces import TraceSingleRequest

        request = TraceSingleRequest()
        assert request.n == 5
        assert request.max_steps == 5000

    def test_trace_sample_request_defaults(self) -> None:
        """TraceSampleRequest should have sensible defaults."""
        from nlink_api.schemas.traces import TraceSampleRequest

        request = TraceSampleRequest()
        assert request.n == 5
        assert request.num_samples == 100
        assert request.seed == 0
        assert request.min_outdegree == 50

    def test_trace_sample_request_validation(self) -> None:
        """TraceSampleRequest should validate fields."""
        from nlink_api.schemas.traces import TraceSampleRequest
        from pydantic import ValidationError

        # Valid request
        request = TraceSampleRequest(n=3, num_samples=50)
        assert request.n == 3
        assert request.num_samples == 50

        # Invalid n (below minimum)
        with pytest.raises(ValidationError):
            TraceSampleRequest(n=0)

        # Invalid n (above maximum)
        with pytest.raises(ValidationError):
            TraceSampleRequest(n=200)

    def test_cycle_info_model(self) -> None:
        """CycleInfo should work correctly."""
        from nlink_api.schemas.traces import CycleInfo

        cycle = CycleInfo(
            cycle_ids=[1, 2],
            cycle_titles=["Page1", "Page2"],
            count=5,
            length=2
        )
        assert cycle.cycle_ids == [1, 2]
        assert cycle.count == 5
        assert cycle.length == 2
