from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

import pytest


def _load_release_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "release.py"
    spec = spec_from_file_location("release_module", module_path)
    module = module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_commit_detects_conventional_and_breaking():
    release = _load_release_module()

    cc_type, desc, breaking = release.parse_commit("feat(ui)!: add new menu", "")
    assert cc_type == "feat"
    assert desc == "add new menu"
    assert breaking is True

    cc_type, desc, breaking = release.parse_commit("misc update", "BREAKING CHANGE: api")
    assert cc_type == "other"
    assert desc == "misc update"
    assert breaking is True


def test_determine_bump_priority_major_minor_patch():
    release = _load_release_module()
    commits = [
        release.Commit("a" * 40, "fix: patch", "", "fix", "patch", False),
        release.Commit("b" * 40, "feat: feature", "", "feat", "feature", False),
        release.Commit("c" * 40, "refactor!: break", "", "refactor", "break", True),
    ]

    assert release.determine_bump(commits, "auto") == "major"


def test_bump_version_variants_and_invalid():
    release = _load_release_module()

    assert release.bump_version("1.2.3", "major") == "2.0.0"
    assert release.bump_version("1.2.3", "minor") == "1.3.0"
    assert release.bump_version("1.2.3", "patch") == "1.2.4"
    with pytest.raises(RuntimeError):
        release.bump_version("1.2", "patch")
