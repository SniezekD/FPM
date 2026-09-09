import os
import pathlib

import pandas as pd
import pytest

from fpm.postprocessing import CasePostProcessor, GeometryPostProcessor


def _write_specs(case_dir):
    """Write the porous-medium and OpenFOAM specs a case needs to construct."""
    case_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "porosity": [0.5],
        "x_min": [0.0], "x_max": [1.0],
        "y_min": [0.0], "y_max": [1.0],
        "z_min": [0.0], "z_max": [1.0],
    }).to_csv(case_dir.parent / "porous_medium_spec.csv", index=False)
    pd.DataFrame({
        "inlet_wall": ["left"],
        "inlet_u_value": ["uniform (0.001 0 0)"],
        "inlet_area": [1.0],
        "streamwise_axis": ["x"],
    }).to_csv(case_dir / "OF_spec.csv", index=False)


def _metrics_row(**overrides):
    row = {
        "porosity": 0.5,
        "tortuosity": 1.25,
        "participation_number": 0.8,
        "rho_minus": 0.1,
        "inlet_flow_rate": 0.001,
        "streamwise_axis": "x",
    }
    row.update(overrides)
    return row


def _make_case(tmp_path, with_fields=True, cache_row=_metrics_row):
    """Build a case dir with specs, an optional dummy field archive and cache."""
    case_dir = tmp_path / "geometry_000" / "velocity_1.00000e-03"
    _write_specs(case_dir)
    if with_fields:
        # Content is irrelevant: the guards only stat this file, never read it.
        (case_dir / "fields_1.vtk.gz").write_bytes(b"")
    return case_dir


def test_valid_cache_is_loaded(tmp_path):
    case_dir = _make_case(tmp_path)
    pd.DataFrame([_metrics_row()]).to_csv(
        case_dir / "case_flow_params.csv", index=False
    )
    case = CasePostProcessor(case_dir)
    loaded = case._load_cached_metrics()
    assert loaded is not None
    assert set(loaded) == set(CasePostProcessor.METRIC_KEYS)
    assert loaded["rho_minus"] == pytest.approx(0.1)


def test_missing_cache_returns_none(tmp_path):
    case_dir = _make_case(tmp_path)
    assert CasePostProcessor(case_dir)._load_cached_metrics() is None


def test_stale_cache_is_rejected(tmp_path):
    case_dir = _make_case(tmp_path)
    cache = case_dir / "case_flow_params.csv"
    pd.DataFrame([_metrics_row()]).to_csv(cache, index=False)
    # Make the field archive newer than the cache -> stale.
    newer = cache.stat().st_mtime + 100
    os.utime(case_dir / "fields_1.vtk.gz", (newer, newer))
    assert CasePostProcessor(case_dir)._load_cached_metrics() is None


def test_wrong_schema_is_rejected(tmp_path):
    case_dir = _make_case(tmp_path)
    cache = case_dir / "case_flow_params.csv"
    pd.DataFrame([{"foo": 1, "bar": 2}]).to_csv(cache, index=False)
    # Keep the cache newer than the field archive so only the schema differs.
    older = cache.stat().st_mtime - 100
    os.utime(case_dir / "fields_1.vtk.gz", (older, older))
    assert CasePostProcessor(case_dir)._load_cached_metrics() is None


def test_empty_cache_is_rejected(tmp_path):
    case_dir = _make_case(tmp_path)
    cache = case_dir / "case_flow_params.csv"
    pd.DataFrame(columns=CasePostProcessor.METRIC_KEYS).to_csv(cache, index=False)
    older = cache.stat().st_mtime - 100
    os.utime(case_dir / "fields_1.vtk.gz", (older, older))
    assert CasePostProcessor(case_dir)._load_cached_metrics() is None


def test_metrics_uses_cache_without_reading_vtk(tmp_path, monkeypatch):
    case_dir = _make_case(tmp_path)
    pd.DataFrame([_metrics_row(tortuosity=1.5)]).to_csv(
        case_dir / "case_flow_params.csv", index=False
    )

    def _boom(*_args, **_kwargs):
        raise AssertionError("VTK should not be read on a cache hit")

    monkeypatch.setattr("fpm.postprocessing.read_vtk", _boom)
    case = CasePostProcessor(case_dir)
    assert case.metrics["tortuosity"] == pytest.approx(1.5)


def test_overwrite_bypasses_cache(tmp_path, monkeypatch):
    case_dir = _make_case(tmp_path)
    pd.DataFrame([_metrics_row()]).to_csv(
        case_dir / "case_flow_params.csv", index=False
    )

    def _sentinel(_self):
        raise RuntimeError("recomputed from VTK")

    monkeypatch.setattr(CasePostProcessor, "read_case_fields", _sentinel)
    case = CasePostProcessor(case_dir, overwrite=True)
    with pytest.raises(RuntimeError, match="recomputed from VTK"):
        _ = case.metrics


def test_geometry_cascade_writes_case_and_geometry_csvs(tmp_path):
    geom_dir = tmp_path / "geometry_007"
    for velocity in ("1.00000e-03", "2.00000e-03"):
        case_dir = geom_dir / f"velocity_{velocity}"
        _write_specs(case_dir)
        (case_dir / "fields_1.vtk.gz").write_bytes(b"")
        pd.DataFrame([_metrics_row()]).to_csv(
            case_dir / "case_flow_params.csv", index=False
        )

    geom = GeometryPostProcessor(geom_dir)
    out = geom.to_csv()
    assert out.name == "geom_007_flow_params.csv"
    assert len(geom.results_df) == 2
    assert (geom.results_df["geometry_id"] == 7).all()
    for velocity in ("1.00000e-03", "2.00000e-03"):
        assert (geom_dir / f"velocity_{velocity}" / "case_flow_params.csv").exists()


def test_parse_geometry_id():
    assert GeometryPostProcessor._parse_geometry_id(
        pathlib.Path("geometry_042")
    ) == 42
    with pytest.raises(ValueError):
        GeometryPostProcessor._parse_geometry_id(
            pathlib.Path("no_number_here")
        )
