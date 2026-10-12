from pathlib import Path
import json
import tomllib


APP_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = APP_DIR.parent


def test_nixpacks_starts_through_migration_first_entrypoint():
    config = tomllib.loads((REPO_DIR / "nixpacks.toml").read_text())
    script = (APP_DIR / "start_hire_cloud.sh").read_text()

    assert config["providers"] == ["python"]
    assert "start_hire_cloud.sh" in config["start"]["cmd"]
    assert script.index("db upgrade --directory migrations") < script.index("exec gunicorn")
    assert "0.0.0.0:${PORT:-8000}" in script


def test_pwa_manifest_and_service_worker_versions_stay_in_sync():
    manifest = json.loads((APP_DIR / "hire_cloud/static/manifest.webmanifest").read_text())
    service_worker = (APP_DIR / "hire_cloud/static/js/service-worker.js").read_text()

    assert manifest["start_url"] == "/"
    assert manifest["scope"] == "/"
    assert manifest["display"] == "standalone"
    assert {item["sizes"] for item in manifest["icons"]} >= {"192x192", "512x512"}
    assert "hire-cloud-shell-v3" in service_worker
    for icon in manifest["icons"]:
        assert icon["src"] in service_worker

    templates = APP_DIR / "hire_cloud/templates"
    for name in ("index.html", "auth.html", "workspace.html", "token_action.html"):
        page = (templates / name).read_text()
        assert "manifest.webmanifest" in page
        assert "v='20261012.1'" in page
    assert "manifest.webmanifest?v=20261012.1" in service_worker
