"""Shared API client for N-Link Basin Analysis visualization tools.

This module provides a reusable client for connecting to the N-Link API server.
Visualization tools can import this client to access page search, tracing,
basin mapping, and report generation endpoints.

Usage:
    from viz.api_client import NLinkAPIClient

    client = NLinkAPIClient("http://localhost:8000")
    if client.health_check():
        results = client.search_pages("Massachusetts")
        trace = client.trace_single(n=5, start_title="Massachusetts")
"""

from __future__ import annotations

from typing import Optional

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class NLinkAPIClient:
    """Client for N-Link Basin Analysis API.

    Provides methods for:
    - Health checking the API server
    - Searching pages by title
    - Looking up pages by ID or title
    - Tracing N-link paths
    - Submitting background tasks and polling for results

    Attributes:
        base_url: The API server base URL (e.g., "http://localhost:8000")
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        """Initialize the API client.

        Args:
            base_url: API server URL (default: http://localhost:8000)
            timeout: Request timeout in seconds (default: 30.0)
        """
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx library required for API client. "
                "Install with: pip install httpx"
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client (lazy initialization)."""
        if self._client is None:
            self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)
        return self._client

    def close(self) -> None:
        """Close the HTTP client connection."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "NLinkAPIClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    # =========================================================================
    # Health & Status
    # =========================================================================

    def health_check(self) -> bool:
        """Check if the API server is available.

        Returns:
            True if server responds with 200, False otherwise.
        """
        try:
            resp = self.client.get("/api/v1/health")
            return resp.status_code == 200
        except Exception:
            return False

    def get_status(self) -> Optional[dict]:
        """Get detailed API status including data source info.

        Returns:
            Status dict with keys like 'status', 'data_loaded', 'page_count', etc.
            None if request fails.
        """
        try:
            resp = self.client.get("/api/v1/status")
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception:
            return None

    # =========================================================================
    # Page Lookup
    # =========================================================================

    def search_pages(self, query: str, limit: int = 20) -> list[dict]:
        """Search for pages by title.

        Args:
            query: Search string (matches against page titles)
            limit: Maximum number of results (default: 20)

        Returns:
            List of dicts with 'page_id' and 'title' keys.
            Empty list if no matches or request fails.
        """
        try:
            resp = self.client.get(
                "/api/v1/data/pages/search",
                params={"q": query, "limit": limit}
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("results", [])
            return []
        except Exception as e:
            print(f"API search error: {e}")
            return []

    def get_page(self, page_id: int) -> Optional[dict]:
        """Get page information by ID.

        Args:
            page_id: Wikipedia page ID

        Returns:
            Dict with page info ('page_id', 'title', 'link_count', etc.)
            None if not found or request fails.
        """
        try:
            resp = self.client.get(f"/api/v1/data/pages/{page_id}")
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception:
            return None

    def get_page_by_title(self, title: str) -> Optional[dict]:
        """Get page information by title.

        Args:
            title: Wikipedia page title (exact match)

        Returns:
            Dict with page info ('page_id', 'title', 'link_count', etc.)
            None if not found or request fails.
        """
        try:
            resp = self.client.get(f"/api/v1/data/pages/by-title/{title}")
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception:
            return None

    # =========================================================================
    # Tracing
    # =========================================================================

    def trace_single(
        self,
        n: int,
        start_title: Optional[str] = None,
        start_page_id: Optional[int] = None,
        max_steps: int = 1000,
        resolve_titles: bool = True,
    ) -> Optional[dict]:
        """Trace a single N-link path from a starting page.

        Args:
            n: The N value (which link to follow at each step)
            start_title: Starting page title (use this OR start_page_id)
            start_page_id: Starting page ID (use this OR start_title)
            max_steps: Maximum steps before giving up (default: 1000)
            resolve_titles: Include page titles in response (default: True)

        Returns:
            Dict with trace results:
            - 'path': List of page IDs in the path
            - 'path_titles': List of page titles (if resolve_titles=True)
            - 'steps': Number of steps taken
            - 'terminal_type': 'CYCLE', 'DEAD_END', 'INSUFFICIENT_LINKS', etc.
            - 'cycle_start_index': Index where cycle begins (if CYCLE)
            - 'cycle_len': Length of terminal cycle (if CYCLE)
            - 'cycle_titles': Titles of cycle members (if CYCLE)

            None if request fails.
        """
        try:
            params = {"n": n, "max_steps": max_steps, "resolve_titles": resolve_titles}
            if start_title:
                params["start_title"] = start_title
            elif start_page_id is not None:
                params["start_page_id"] = start_page_id
            else:
                return None

            resp = self.client.get("/api/v1/traces/single", params=params)
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            print(f"API trace error: {e}")
            return None

    # =========================================================================
    # Background Tasks
    # =========================================================================

    def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get status of a background task.

        Args:
            task_id: The task ID returned when submitting an async operation

        Returns:
            Dict with task status:
            - 'task_id': The task ID
            - 'status': 'pending', 'running', 'completed', 'failed'
            - 'result': Task result (if completed)
            - 'error': Error message (if failed)
            - 'progress': Progress percentage (if available)

            None if task not found or request fails.
        """
        try:
            resp = self.client.get(f"/api/v1/tasks/{task_id}")
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception:
            return None

    def wait_for_task(
        self,
        task_id: str,
        poll_interval: float = 1.0,
        timeout: float = 300.0,
    ) -> Optional[dict]:
        """Wait for a background task to complete.

        Args:
            task_id: The task ID to wait for
            poll_interval: Seconds between status checks (default: 1.0)
            timeout: Maximum seconds to wait (default: 300.0)

        Returns:
            Final task status dict (with 'result' if completed).
            None if timeout or request fails.
        """
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            if status is None:
                return None

            if status.get("status") in ("completed", "failed"):
                return status

            time.sleep(poll_interval)

        return None  # Timeout

    # =========================================================================
    # Basin Operations
    # =========================================================================

    def map_basin(
        self,
        n: int,
        cycle_titles: list[str],
        max_depth: Optional[int] = None,
        background: bool = False,
    ) -> Optional[dict]:
        """Map a basin from its terminal cycle.

        Args:
            n: The N value for basin mapping
            cycle_titles: List of page titles forming the terminal cycle
            max_depth: Maximum depth to trace (optional)
            background: If True, run as background task

        Returns:
            If background=False: Dict with basin mapping results
            If background=True: Dict with 'task_id' for polling
            None if request fails.
        """
        try:
            payload = {
                "n": n,
                "cycle_titles": cycle_titles,
                "background": background,
            }
            if max_depth is not None:
                payload["max_depth"] = max_depth

            resp = self.client.post("/api/v1/basins/map", json=payload)
            if resp.status_code in (200, 202):
                return resp.json()
            return None
        except Exception as e:
            print(f"API basin map error: {e}")
            return None

    # =========================================================================
    # Reports
    # =========================================================================

    def generate_report(
        self,
        report_type: str,
        background: bool = True,
        **kwargs,
    ) -> Optional[dict]:
        """Generate a report.

        Args:
            report_type: One of 'trunkiness', 'human'
            background: If True, run as background task (default)
            **kwargs: Additional parameters for the report

        Returns:
            If background=False: Dict with report results
            If background=True: Dict with 'task_id' for polling
            None if request fails.
        """
        try:
            endpoint = f"/api/v1/reports/{report_type}"
            if background:
                endpoint += "/async"

            resp = self.client.post(endpoint, json=kwargs or {})
            if resp.status_code in (200, 202):
                return resp.json()
            return None
        except Exception as e:
            print(f"API report error: {e}")
            return None


def check_api_available(base_url: str = "http://localhost:8000") -> bool:
    """Quick check if the API server is available.

    Args:
        base_url: API server URL to check

    Returns:
        True if server is reachable and healthy, False otherwise.
    """
    if not HTTPX_AVAILABLE:
        return False
    try:
        client = NLinkAPIClient(base_url, timeout=5.0)
        return client.health_check()
    except Exception:
        return False
