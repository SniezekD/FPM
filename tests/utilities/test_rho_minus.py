import pandas as pd
import pytest

from fpm.utilities.rho_minus import compute_rho_minus


def test_rho_minus_volume_fraction_of_backflow():
    # cells with u_x < 0 are indices 0 and 2 -> volume 1 + 2 = 3 of total 6
    df = pd.DataFrame({"u_x": [-1, 2, -3, 4], "volume": [1, 1, 2, 2]})
    assert compute_rho_minus(df) == pytest.approx(0.5)


def test_rho_minus_is_zero_without_backflow():
    df = pd.DataFrame({"u_x": [1, 2, 3], "volume": [1, 1, 1]})
    assert compute_rho_minus(df) == 0.0


def test_raises_value_error():
    df = pd.DataFrame({"u_x": [1, 2, 3], "volume": [1, 1, 1]})
    with pytest.raises(ValueError):
        compute_rho_minus(df, streamwise_axis=None)
