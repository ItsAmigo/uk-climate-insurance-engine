"""Smoke test — proves the package installs and imports cleanly."""

from __future__ import annotations


def test_package_imports() -> None:
    import climate_insurance

    assert climate_insurance.__version__


def test_subpackages_import() -> None:
    from climate_insurance import api, config, fairness, hazards, models
    from climate_insurance.data import loaders, sources

    for module in (api, config, fairness, hazards, models, loaders, sources):
        assert module is not None
