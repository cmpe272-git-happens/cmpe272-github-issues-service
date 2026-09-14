# juilee
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OPENAPI_FILE = PROJECT_ROOT / "openapi.yaml"


def load_openapi():
    with OPENAPI_FILE.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def test_openapi_version_is_31():
    specification = load_openapi()

    assert specification["openapi"] == "3.1.0"


def test_required_api_routes_exist():
    specification = load_openapi()
    paths = specification["paths"]

    required_routes = {
        "/issues": {"get", "post"},
        "/issues/{number}": {"get", "patch"},
        "/issues/{number}/comments": {"get", "post"},
        "/webhook": {"post"},
        "/events": {"get"},
        "/healthz": {"get"},
    }

    for route, methods in required_routes.items():
        assert route in paths

        for method in methods:
            assert method in paths[route]


def test_reusable_schemas_exist():
    specification = load_openapi()
    schemas = specification["components"]["schemas"]

    assert "Issue" in schemas
    assert "Comment" in schemas
    assert "Error" in schemas
