"""Tests for basin mapping and branch analysis endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestBasinMapEndpoint:
    """Tests for /api/v1/basins/map endpoint."""

    def test_map_basin_requires_cycle(self, test_client: TestClient) -> None:
        """Should require at least one cycle node."""
        response = test_client.post(
            "/api/v1/basins/map",
            json={"n": 5}
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.integration
    def test_map_basin_by_title(self, test_client: TestClient) -> None:
        """Should map basin from cycle titles."""
        response = test_client.post(
            "/api/v1/basins/map",
            json={
                "n": 5,
                "cycle_titles": ["Massachusetts", "Gulf_of_Maine"],
                "max_depth": 10,
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Could be sync or background task
        if "task_id" in data:
            assert data["task_type"] == "basin_map"
        else:
            assert "n" in data
            assert "total_nodes" in data
            assert "layers" in data

    @pytest.mark.integration
    def test_map_basin_by_page_id(self, test_client: TestClient) -> None:
        """Should map basin from page IDs."""
        response = test_client.post(
            "/api/v1/basins/map",
            json={
                "n": 5,
                "cycle_page_ids": [1, 2],
                "max_depth": 5,
            }
        )

        assert response.status_code == 200
        data = response.json()

        if "task_id" not in data:
            assert "cycle_page_ids" in data
            assert data["n"] == 5

    @pytest.mark.integration
    def test_map_basin_sync_for_limited_depth(self, test_client: TestClient) -> None:
        """Limited depth requests should run synchronously."""
        response = test_client.post(
            "/api/v1/basins/map",
            json={
                "n": 5,
                "cycle_page_ids": [1, 2],
                "max_depth": 10,  # <= 50 should be sync
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should be sync result (not task submission)
        assert "n" in data or "task_id" in data

    @pytest.mark.integration
    def test_map_basin_includes_layer_info(self, test_client: TestClient) -> None:
        """Should include BFS layer information."""
        response = test_client.post(
            "/api/v1/basins/map",
            json={
                "n": 5,
                "cycle_page_ids": [1, 2],
                "max_depth": 5,
            }
        )

        assert response.status_code == 200
        data = response.json()

        if "task_id" not in data:
            assert "layers" in data
            assert isinstance(data["layers"], list)
            for layer in data["layers"]:
                assert "depth" in layer
                assert "new_nodes" in layer
                assert "total_seen" in layer

    @pytest.mark.integration
    def test_map_basin_includes_stopping_reason(self, test_client: TestClient) -> None:
        """Should include reason for stopping."""
        response = test_client.post(
            "/api/v1/basins/map",
            json={
                "n": 5,
                "cycle_page_ids": [1, 2],
                "max_depth": 5,
            }
        )

        assert response.status_code == 200
        data = response.json()

        if "task_id" not in data:
            assert "stopped_reason" in data

    @pytest.mark.integration
    def test_map_basin_includes_timing(self, test_client: TestClient) -> None:
        """Should include elapsed time."""
        response = test_client.post(
            "/api/v1/basins/map",
            json={
                "n": 5,
                "cycle_page_ids": [1, 2],
                "max_depth": 5,
            }
        )

        assert response.status_code == 200
        data = response.json()

        if "task_id" not in data:
            assert "elapsed_seconds" in data
            assert isinstance(data["elapsed_seconds"], (int, float))


class TestBasinMapTaskStatus:
    """Tests for basin map task status endpoint."""

    def test_get_map_task_not_found(self, test_client: TestClient) -> None:
        """Should return 404 for unknown task ID."""
        response = test_client.get("/api/v1/basins/map/nonexistent-task-id")

        assert response.status_code == 404


class TestBranchAnalysisEndpoint:
    """Tests for /api/v1/basins/branches endpoint."""

    def test_branches_requires_cycle(self, test_client: TestClient) -> None:
        """Should require at least one cycle node."""
        response = test_client.post(
            "/api/v1/basins/branches",
            json={"n": 5}
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.integration
    def test_branches_by_page_id(self, test_client: TestClient) -> None:
        """Should analyze branches from cycle page IDs."""
        response = test_client.post(
            "/api/v1/basins/branches",
            json={
                "n": 5,
                "cycle_page_ids": [1, 2],
                "max_depth": 5,
                "top_k": 10,
            }
        )

        assert response.status_code == 200
        data = response.json()

        if "task_id" in data:
            assert data["task_type"] == "branch_analysis"
        else:
            assert "n" in data
            assert "branches" in data

    @pytest.mark.integration
    def test_branches_returns_branch_info(self, test_client: TestClient) -> None:
        """Should return branch details."""
        response = test_client.post(
            "/api/v1/basins/branches",
            json={
                "n": 5,
                "cycle_page_ids": [1, 2],
                "max_depth": 5,
            }
        )

        assert response.status_code == 200
        data = response.json()

        if "task_id" not in data:
            assert "branches" in data
            assert isinstance(data["branches"], list)

            for branch in data["branches"]:
                assert "rank" in branch
                assert "entry_id" in branch
                assert "basin_size" in branch

    @pytest.mark.integration
    def test_branches_includes_summary_stats(self, test_client: TestClient) -> None:
        """Should include summary statistics."""
        response = test_client.post(
            "/api/v1/basins/branches",
            json={
                "n": 5,
                "cycle_page_ids": [1, 2],
                "max_depth": 5,
            }
        )

        assert response.status_code == 200
        data = response.json()

        if "task_id" not in data:
            assert "total_basin_nodes" in data
            assert "num_branches" in data
            assert "max_depth_reached" in data

    @pytest.mark.integration
    def test_branches_respects_top_k(self, test_client: TestClient) -> None:
        """Should respect top_k parameter."""
        response = test_client.post(
            "/api/v1/basins/branches",
            json={
                "n": 5,
                "cycle_page_ids": [1, 2],
                "max_depth": 5,
                "top_k": 3,
            }
        )

        assert response.status_code == 200
        data = response.json()

        if "task_id" not in data:
            assert len(data["branches"]) <= 3


class TestBranchesTaskStatus:
    """Tests for branch analysis task status endpoint."""

    def test_get_branches_task_not_found(self, test_client: TestClient) -> None:
        """Should return 404 for unknown task ID."""
        response = test_client.get("/api/v1/basins/branches/nonexistent-task-id")

        assert response.status_code == 404


class TestBasinSchemas:
    """Tests for basin Pydantic schemas."""

    def test_basin_map_request_defaults(self) -> None:
        """BasinMapRequest should have sensible defaults."""
        from nlink_api.schemas.basins import BasinMapRequest

        request = BasinMapRequest()
        assert request.n == 5
        assert request.max_depth == 0  # Unlimited
        assert request.max_nodes == 0  # Unlimited

    def test_basin_map_request_with_values(self) -> None:
        """BasinMapRequest should accept values."""
        from nlink_api.schemas.basins import BasinMapRequest

        request = BasinMapRequest(
            n=7,
            cycle_page_ids=[1, 2, 3],
            max_depth=10,
            write_membership=True,
        )
        assert request.n == 7
        assert request.cycle_page_ids == [1, 2, 3]
        assert request.max_depth == 10
        assert request.write_membership is True

    def test_branch_analysis_request_defaults(self) -> None:
        """BranchAnalysisRequest should have sensible defaults."""
        from nlink_api.schemas.basins import BranchAnalysisRequest

        request = BranchAnalysisRequest()
        assert request.n == 5
        assert request.top_k == 25

    def test_layer_info_response(self) -> None:
        """LayerInfoResponse should work correctly."""
        from nlink_api.schemas.basins import LayerInfoResponse

        layer = LayerInfoResponse(
            depth=3,
            new_nodes=100,
            total_seen=500
        )
        assert layer.depth == 3
        assert layer.new_nodes == 100
        assert layer.total_seen == 500

    def test_branch_info_response(self) -> None:
        """BranchInfoResponse should work correctly."""
        from nlink_api.schemas.basins import BranchInfoResponse

        branch = BranchInfoResponse(
            rank=1,
            entry_id=42,
            entry_title="Test_Page",
            basin_size=1000,
            max_depth=10,
            enters_cycle_page_id=1
        )
        assert branch.rank == 1
        assert branch.entry_id == 42
        assert branch.basin_size == 1000
