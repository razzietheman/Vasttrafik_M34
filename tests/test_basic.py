"""Static checks for package metadata and structure."""
from __future__ import annotations

import ast
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
COMPONENT = PROJECT_ROOT / "custom_components" / "vasttrafik_m34"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_manifest():
    """Manifest is consistent with a HACS custom integration."""
    manifest = _json(COMPONENT / "manifest.json")
    assert manifest["domain"] == "vasttrafik_m34"
    assert manifest["name"] == "Västtrafik M34"
    assert manifest["version"] == "2.0.5"
    assert manifest["config_flow"] is True
    assert manifest["quality_scale"] == "bronze"
    assert manifest["requirements"] == []


def test_hacs_metadata():
    """HACS metadata matches the minimum supported Home Assistant version."""
    hacs = _json(PROJECT_ROOT / "hacs.json")
    assert hacs["country"] == "SE"
    assert hacs["homeassistant"] == "2024.11.0"


def test_strings_and_translations():
    """All config flow steps have texts in both language files."""
    steps = {"user", "station", "select_station", "reauth_confirm"}
    for path in (COMPONENT / "strings.json", COMPONENT / "translations" / "sv.json"):
        data = _json(path)
        assert steps <= set(data["config"]["step"])
        assert "reauth_successful" in data["config"]["abort"]
        assert "init" in data["options"]["step"]
        for step in steps:
            assert "data_description" in data["config"]["step"][step]


def test_required_files():
    """Every file needed by HACS/hassfest is present."""
    required = [
        "__init__.py",
        "config_flow.py",
        "const.py",
        "coordinator.py",
        "sensor.py",
        "manifest.json",
        "strings.json",
        "translations/sv.json",
        "quality_scale.yaml",
    ]
    for name in required:
        assert (COMPONENT / name).is_file(), name
    assert (PROJECT_ROOT / "README.md").is_file()
    assert (PROJECT_ROOT / "LICENSE").is_file()


def test_python_sources_parse():
    """All Python files parse with the supported Python version."""
    files = sorted(COMPONENT.rglob("*.py")) + sorted(
        (PROJECT_ROOT / "tests").rglob("*.py")
    )
    assert files
    for path in files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_v4_api_parameter_names():
    """The coordinator uses the documented Västtrafik v4 parameter names."""
    source = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    assert '"maxDeparturesPerLineAndDirection": max_per_line' in source
    assert '"limit": 50' in source
    assert '"maxDeparturesPerLine"' not in source
