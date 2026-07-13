import pandas as pd
import pytest

from fpm.io.spec_reader import read_openfoam_spec, read_porous_medium_spec


def test_read_openfoam_spec_reads_csv(tmp_path):
    pd.DataFrame({"inlet_area": [2.0], "inlet_wall": ["left"]}).to_csv(
        tmp_path / "OF_spec.csv", index=False)
    df = read_openfoam_spec(tmp_path)
    assert df["inlet_area"][0] == 2.0
    assert df["inlet_wall"][0] == "left"


def test_read_openfoam_spec_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_openfoam_spec(tmp_path)


def test_read_porous_medium_spec_reads_from_constant_dir(tmp_path):
    constant = tmp_path / "constant"
    constant.mkdir()
    pd.DataFrame({"porosity": [0.7]}).to_csv(
        constant / "porous_medium_spec.csv", index=False)
    df = read_porous_medium_spec(tmp_path)
    assert df["porosity"][0] == 0.7


def test_read_porous_medium_spec_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_porous_medium_spec(tmp_path)
