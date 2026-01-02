"""Tests for data source endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestDataSourceEndpoint:
    """Tests for /api/v1/data/source endpoint."""

    def test_source_returns_info(self, test_client: TestClient) -> None:
        """Should return data source information."""
        response = test_client.get("/api/v1/data/source")

        assert response.status_code == 200
        data = response.json()
        assert "source" in data
        assert "nlink_sequences_path" in data
        assert "pages_path" in data

    def test_source_includes_existence_checks(self, test_client: TestClient) -> None:
        """Should indicate whether data files exist."""
        response = test_client.get("/api/v1/data/source")

        assert response.status_code == 200
        data = response.json()
        assert "nlink_sequences_exists" in data
        assert "pages_exists" in data
        assert isinstance(data["nlink_sequences_exists"], bool)
        assert isinstance(data["pages_exists"], bool)


class TestDataValidateEndpoint:
    """Tests for /api/v1/data/validate endpoint."""

    @pytest.mark.integration
    def test_validate_returns_result(self, test_client: TestClient) -> None:
        """Should return validation result."""
        response = test_client.post("/api/v1/data/validate")

        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert isinstance(data["valid"], bool)

    @pytest.mark.integration
    def test_validate_includes_errors_and_warnings(self, test_client: TestClient) -> None:
        """Should include errors and warnings lists."""
        response = test_client.post("/api/v1/data/validate")

        assert response.status_code == 200
        data = response.json()
        assert "errors" in data
        assert "warnings" in data
        assert isinstance(data["errors"], list)
        assert isinstance(data["warnings"], list)


class TestPageLookupEndpoints:
    """Tests for page lookup endpoints."""

    def test_get_page_by_id_found(self, test_client: TestClient) -> None:
        """Should return page info when found."""
        response = test_client.get("/api/v1/data/pages/1")

        assert response.status_code == 200
        data = response.json()
        assert "page_id" in data
        assert data["page_id"] == 1

    def test_get_page_by_id_not_found(self, test_client: TestClient) -> None:
        """Should return 404 when page not found."""
        response = test_client.get("/api/v1/data/pages/99999")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_get_page_by_id_includes_title(self, test_client: TestClient) -> None:
        """Should include page title."""
        response = test_client.get("/api/v1/data/pages/1")

        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert data["title"] == "Massachusetts"

    @pytest.mark.integration
    def test_search_pages_returns_results(self, test_client: TestClient) -> None:
        """Should return search results."""
        response = test_client.get("/api/v1/data/pages/search", params={"q": "mass"})

        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "count" in data
        assert data["query"] == "mass"

    def test_search_pages_empty_query_rejected(self, test_client: TestClient) -> None:
        """Should reject empty search query."""
        response = test_client.get("/api/v1/data/pages/search", params={"q": ""})

        assert response.status_code == 422  # Validation error

    @pytest.mark.integration
    def test_search_pages_respects_limit(self, test_client: TestClient) -> None:
        """Should respect limit parameter."""
        response = test_client.get(
            "/api/v1/data/pages/search",
            params={"q": "a", "limit": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 5


class TestDataSchemas:
    """Tests for data Pydantic schemas."""

    def test_data_source_info(self) -> None:
        """DataSourceInfo should work correctly."""
        from nlink_api.schemas.common import DataSourceInfo

        info = DataSourceInfo(
            source="local",
            nlink_sequences_path="/path/to/nlink.parquet",
            nlink_sequences_exists=True,
            pages_path="/path/to/pages.parquet",
            pages_exists=True,
        )
        assert info.source == "local"
        assert info.nlink_sequences_exists is True

    def test_validation_result(self) -> None:
        """ValidationResult should work correctly."""
        from nlink_api.schemas.common import ValidationResult

        result = ValidationResult(
            valid=True,
            errors=[],
            warnings=["Data is 30 days old"]
        )
        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1

    def test_error_response(self) -> None:
        """ErrorResponse should work correctly."""
        from nlink_api.schemas.common import ErrorResponse

        error = ErrorResponse(
            error="NotFound",
            detail="Page with ID 99999 not found"
        )
        assert error.error == "NotFound"
        assert "99999" in error.detail
