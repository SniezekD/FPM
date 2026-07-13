import pandas as pd
import pytest

from fpm.utilities.tortuosity import compute_tortuosity


def test_tortuosity_ratio_of_total_to_streamwise_momentum():
    # uniform rho = vol = 1  ->  tortuosity = sum(u_norm) / sum(u_x) = 4 / 2 = 2
    df = pd.DataFrame({
        "u_norm": [2, 2], "u_x": [1, 1],
        "mass_density": [1, 1], "volume": [1, 1],
    })
    assert compute_tortuosity(df) == pytest.approx(2.0)
