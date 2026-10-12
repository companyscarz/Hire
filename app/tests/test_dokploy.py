"""Tests for the safe Dokploy API client wrapper."""
import json
from urllib.error import HTTPError, URLError

import pytest

from hire_cloud.dokploy import DokployClient, DokployError


def test_client_requires_valid_base_url():
    with pytest.raises(DokployError):
        DokployClient(base_url="", api_key="test")
    with pytest.raises(DokployError):
        DokployClient(base_url="http://example.com", api_key="test")
    with pytest.raises(DokployError):
        DokployClient(base_url="https://user:pass@example.com", api_key="test")


def test_client_requires_api_key():
    with pytest.raises(DokployError):
        DokployClient(base_url="https://dokploy.example.com", api_key="")


def test_server_metrics_uses_api_key_header_and_parses_json(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            captured["limit"] = limit
            return json.dumps({"cpu": 2, "memory": 1024}).encode()

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["key"] = request.get_header("X-api-key")
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("hire_cloud.dokploy.urlopen", fake_urlopen)
    client = DokployClient("https://dokploy.example.com", "secret-test-key", timeout=3)
    assert client.get_server_metrics() == {"cpu": 2, "memory": 1024}
    assert captured["url"] == "https://dokploy.example.com/api/user.getServerMetrics"
    assert captured["key"] == "secret-test-key"
    assert captured["timeout"] == 3


def test_only_allowlisted_endpoints_can_be_called():
    client = DokployClient("https://dokploy.example.com", "test")
    with pytest.raises(DokployError):
        client._get("/arbitrary.endpoint")


def test_auth_errors_are_sanitized(monkeypatch):
    def fake_urlopen(request, timeout):
        raise HTTPError(request.full_url, 403, "Forbidden", {}, None)

    monkeypatch.setattr("hire_cloud.dokploy.urlopen", fake_urlopen)
    client = DokployClient("https://dokploy.example.com", "test")
    with pytest.raises(DokployError, match="credentials or permissions"):
        client.get_server_metrics()


def test_network_errors_are_sanitized(monkeypatch):
    def fake_urlopen(request, timeout):
        raise URLError("private network detail")

    monkeypatch.setattr("hire_cloud.dokploy.urlopen", fake_urlopen)
    client = DokployClient("https://dokploy.example.com", "test")
    with pytest.raises(DokployError, match="could not be reached") as error:
        client.get_server_metrics()
    assert "private network detail" not in str(error.value)


def test_invalid_json_is_rejected(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            return b"not-json"

    monkeypatch.setattr("hire_cloud.dokploy.urlopen", lambda request, timeout: FakeResponse())
    client = DokployClient("https://dokploy.example.com", "test")
    with pytest.raises(DokployError, match="invalid JSON"):
        client.get_server_metrics()



def test_client_rejects_base_url_path_prefix():
    with pytest.raises(DokployError, match="origin only"):
        DokployClient(base_url="https://dokploy.example.com/proxy", api_key="test")


def test_customer_permissions_are_least_privilege_and_project_scoped():
    permissions = DokployClient.customer_permissions(
        project_ids=["project-123"],
        environment_ids=["environment-456"],
        service_ids=["service-789"],
    )
    assert permissions["accessedProjects"] == ["project-123"]
    assert permissions["accessedEnvironments"] == ["environment-456"]
    assert permissions["accessedServices"] == ["service-789"]
    assert permissions["accessedServers"] == []
    assert permissions["accessedGitProviders"] == []
    assert all(value is False for key, value in permissions.items() if key.startswith("can"))


@pytest.mark.parametrize("project_ids", [[], None, "project-123", [""], ["project-123", "project-123"]])
def test_customer_permissions_require_valid_explicit_project_mapping(project_ids):
    with pytest.raises(DokployError):
        DokployClient.customer_permissions(project_ids=project_ids)


def test_customer_permissions_rejects_invalid_environment_and_service_ids():
    with pytest.raises(DokployError):
        DokployClient.customer_permissions(project_ids=["p1"], environment_ids=[None])
    with pytest.raises(DokployError):
        DokployClient.customer_permissions(project_ids=["p1"], service_ids=["x" * 161])
