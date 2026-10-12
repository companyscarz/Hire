"""Small, server-side client for the documented Dokploy API.

Keep the API key in deployment secrets. Never pass a customer-supplied base URL,
API key, metrics URL, or provider identifier into this client.
"""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class DokployError(RuntimeError):
    """A safe-to-display Dokploy integration error."""


class DokployClient:
    """Minimal Dokploy API client with strict URL and timeout handling."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None, timeout: float = 8.0):
        self.base_url = (base_url or os.getenv("DOKPLOY_BASE_URL", "")).strip().rstrip("/")
        self.api_key = api_key if api_key is not None else os.getenv("DOKPLOY_API_KEY", "")
        self.timeout = float(timeout)

        parsed = urlsplit(self.base_url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise DokployError("Configure DOKPLOY_BASE_URL with a valid Dokploy URL.")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise DokployError("DOKPLOY_BASE_URL must not contain credentials, query parameters, or fragments.")
        if parsed.path not in {"", "/"}:
            raise DokployError("DOKPLOY_BASE_URL must be the Dokploy origin only, without a path prefix.")
        if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise DokployError("Dokploy API connections must use HTTPS.")
        if not self.api_key or len(self.api_key) > 4096:
            raise DokployError("Configure DOKPLOY_API_KEY in the server environment.")
        if self.timeout <= 0 or self.timeout > 30:
            raise DokployError("Dokploy API timeout must be between 0 and 30 seconds.")

    @staticmethod
    def customer_permissions(*, project_ids, environment_ids=(), service_ids=()):
        """Build least-privilege direct-UI permissions from trusted internal mappings.

        The IDs must come from Hire Cloud's database, never directly from a request.
        This helper does not create a user or grant permissions by itself.
        """
        def clean_ids(values, field):
            if isinstance(values, (str, bytes)):
                raise DokployError(f"{field} must be a collection of trusted IDs.")
            try:
                result = list(values)
            except TypeError as exc:
                raise DokployError(f"{field} must be a collection of trusted IDs.") from exc
            if any(not isinstance(value, str) or not value.strip() or len(value) > 160 for value in result):
                raise DokployError(f"{field} contains an invalid ID.")
            if len(set(result)) != len(result):
                raise DokployError(f"{field} contains duplicate IDs.")
            return result

        projects = clean_ids(project_ids, "project_ids")
        environments = clean_ids(environment_ids, "environment_ids")
        services = clean_ids(service_ids, "service_ids")
        if not projects:
            raise DokployError("Direct Dokploy access requires at least one explicitly mapped project.")
        return {
            "accessedProjects": projects,
            "accessedEnvironments": environments,
            "accessedServices": services,
            "accessedGitProviders": [],
            "accessedServers": [],
            "canCreateProjects": False,
            "canCreateServices": False,
            "canDeleteProjects": False,
            "canDeleteServices": False,
            "canAccessToDocker": False,
            "canAccessToTraefikFiles": False,
            "canAccessToAPI": False,
            "canAccessToSSHKeys": False,
            "canAccessToGitProviders": False,
            "canDeleteEnvironments": False,
            "canCreateEnvironments": False,
        }

    def _get(self, endpoint: str):
        # Endpoints are constants in this module, not request-derived values.
        if endpoint not in {"/user.getServerMetrics", "/user.all"}:
            raise DokployError("This Dokploy endpoint is not enabled in the client.")
        request = Request(
            self.base_url + "/api" + endpoint,
            headers={"x-api-key": self.api_key, "Accept": "application/json"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read(2 * 1024 * 1024 + 1)
                if len(body) > 2 * 1024 * 1024:
                    raise DokployError("Dokploy returned a response that is too large.")
                try:
                    return json.loads(body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise DokployError("Dokploy returned an invalid JSON response.") from exc
        except HTTPError as exc:
            # Do not echo response bodies or headers: they may contain sensitive details.
            if exc.code in {401, 403}:
                raise DokployError("Dokploy rejected the API credentials or permissions.") from None
            if exc.code == 404:
                raise DokployError("The requested Dokploy API endpoint was not found.") from None
            raise DokployError(f"Dokploy API request failed (HTTP {exc.code}).") from None
        except (URLError, TimeoutError, OSError) as exc:
            raise DokployError("Dokploy could not be reached. Check the configured URL and network.") from None

    def get_server_metrics(self):
        """Fetch host/server metrics using the documented user.getServerMetrics endpoint."""
        return self._get("/user.getServerMetrics")

    def list_users(self):
        """List Dokploy users; call only from a trusted operator workflow."""
        return self._get("/user.all")
