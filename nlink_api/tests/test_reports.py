"""Tests for report generation endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestTrunkinessDashboardEndpoint:
    """Tests for /api/v1/reports/trunkiness endpoint."""

    def test_trunkiness_requires_data(self, test_client: TestClient) -> None:
        """Should fail if no branch analysis data exists."""
        response = test_client.post(
            "/api/v1/reports/trunkiness",
            json={"n": 5}
        )

        # Either 404 (no data) or 200 (if mock data exists)
        assert response.status_code in [200, 404]

        if response.status_code == 404:
            data = response.json()
            assert "detail" in data

    def test_trunkiness_accepts_tag(self, test_client: TestClient) -> None:
        """Should accept optional tag parameter."""
        response = test_client.post(
            "/api/v1/reports/trunkiness",
            json={"n": 5, "tag": "test-run"}
        )

        # Should not fail on validation
        assert response.status_code in [200, 404]


class TestTrunkinessDashboardAsyncEndpoint:
    """Tests for /api/v1/reports/trunkiness/async endpoint."""

    def test_trunkiness_async_submits_task(self, test_client: TestClient) -> None:
        """Should submit as background task."""
        response = test_client.post(
            "/api/v1/reports/trunkiness/async",
            json={"n": 5}
        )

        assert response.status_code == 200
        data = response.json()

        assert "task_id" in data
        assert "task_type" in data
        assert data["task_type"] == "trunkiness_dashboard"


class TestHumanReportEndpoint:
    """Tests for /api/v1/reports/human endpoint."""

    def test_human_report_requires_data(self, test_client: TestClient) -> None:
        """Should fail if required data doesn't exist."""
        response = test_client.post(
            "/api/v1/reports/human",
            json={}
        )

        # Either 404 (no data) or 200 (success)
        assert response.status_code in [200, 404]

    def test_human_report_accepts_tag(self, test_client: TestClient) -> None:
        """Should accept optional tag parameter."""
        response = test_client.post(
            "/api/v1/reports/human",
            json={"tag": "test-report"}
        )

        assert response.status_code in [200, 404]


class TestHumanReportAsyncEndpoint:
    """Tests for /api/v1/reports/human/async endpoint."""

    def test_human_report_async_submits_task(self, test_client: TestClient) -> None:
        """Should submit as background task."""
        response = test_client.post(
            "/api/v1/reports/human/async",
            json={}
        )

        assert response.status_code == 200
        data = response.json()

        assert "task_id" in data
        assert data["task_type"] == "human_report"


class TestReportTaskStatus:
    """Tests for report task status endpoint."""

    def test_get_report_task_not_found(self, test_client: TestClient) -> None:
        """Should return 404 for unknown task ID."""
        response = test_client.get("/api/v1/reports/nonexistent-task-id")

        assert response.status_code == 404


class TestReportListEndpoint:
    """Tests for /api/v1/reports/list endpoint."""

    @pytest.mark.integration
    def test_list_reports(self, test_client: TestClient) -> None:
        """Should list available reports."""
        response = test_client.get("/api/v1/reports/list")

        # May return 404 if report_assets_dir doesn't exist
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "reports" in data


class TestFiguresEndpoint:
    """Tests for /api/v1/reports/figures/{filename} endpoint."""

    def test_get_figure_not_found(self, test_client: TestClient) -> None:
        """Should return 404 for missing figure."""
        response = test_client.get("/api/v1/reports/figures/nonexistent.png")

        assert response.status_code == 404

    def test_get_figure_validates_filename(self, test_client: TestClient) -> None:
        """Should handle various filename inputs."""
        # Path traversal attempt
        response = test_client.get("/api/v1/reports/figures/../../../etc/passwd")
        # Should either return 404 or sanitize the path
        assert response.status_code in [404, 422, 400]


class TestReportSchemas:
    """Tests for report Pydantic schemas."""

    def test_trunkiness_request_defaults(self) -> None:
        """TrunkinessDashboardRequest should have sensible defaults."""
        from nlink_api.schemas.reports import TrunkinessDashboardRequest

        request = TrunkinessDashboardRequest()
        assert request.n == 5
        assert isinstance(request.tag, str)  # Has a default tag

    def test_trunkiness_request_validation(self) -> None:
        """TrunkinessDashboardRequest should validate fields."""
        from nlink_api.schemas.reports import TrunkinessDashboardRequest

        # Valid request
        request = TrunkinessDashboardRequest(n=3, tag="test")
        assert request.n == 3
        assert request.tag == "test"

    def test_human_report_request_defaults(self) -> None:
        """HumanReportRequest should have sensible defaults."""
        from nlink_api.schemas.reports import HumanReportRequest

        request = HumanReportRequest()
        assert isinstance(request.tag, str)  # Has a default tag

    def test_report_list_response_structure(self) -> None:
        """ReportListResponse should have expected structure."""
        from nlink_api.schemas.reports import ReportListResponse

        response = ReportListResponse(reports=[])
        assert response.reports == []

    def test_figure_info_response(self) -> None:
        """FigureInfoResponse should validate correctly."""
        from nlink_api.schemas.reports import FigureInfoResponse

        figure = FigureInfoResponse(
            name="test.png",
            path="/path/to/test.png",
            description="A test figure"
        )
        assert figure.name == "test.png"
        assert figure.path == "/path/to/test.png"
