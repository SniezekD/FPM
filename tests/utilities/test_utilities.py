import numpy as np
import pandas as pd
import pytest

from fpm.utilities.utils import (
    standard_err,
    calculate_inlet_flow_rate,
    create_runner_file,
)


def test_standard_err_known_values():
    # two columns, each an arithmetic sequence with a known standard error
    result = standard_err([[2, 10], [4, 20], [6, 30]])
    assert result == pytest.approx([2 / np.sqrt(3), 10 / np.sqrt(3)])


@pytest.mark.parametrize("wall, u_value, area, expected", [
    ("left",  "uniform (0.5 0 0)", 2.0, 1.0),   # streamwise component = x
    ("up",    "uniform (0 0.3 0)", 4.0, 1.2),   # streamwise component = y
    ("front", "uniform (0 0 0.2)", 5.0, 1.0),   # streamwise component = z
])
def test_calculate_inlet_flow_rate(wall, u_value, area, expected):
    spec = pd.DataFrame({
        "inlet_area": [area],
        "inlet_wall": [wall],
        "inlet_u_value": [u_value],
    })
    assert calculate_inlet_flow_rate(spec) == pytest.approx(expected)


def test_create_runner_file_renders_and_writes(tmp_path, monkeypatch):
    # stub run_cmd so the test doesn't actually shell out to `chmod`
    monkeypatch.setattr("fpm.utilities.utils.run_cmd", lambda *a, **k: None)
    (tmp_path / "tpl.jinja").write_text("echo {{ msg }}")
    out = create_runner_file(
        runner_name="run.sh",
        runner_path=tmp_path / "out",
        templates_dir_path=tmp_path,
        template_name="tpl.jinja",
        var_dict={"msg": "hello"},
    )
    assert out.name == "run.sh"
    assert out.read_text(encoding="utf-8") == "echo hello"
