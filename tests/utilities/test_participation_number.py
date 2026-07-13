import pandas as pd
import pytest

from fpm.utilities.participation_number import compute_participation_number


def test_participation_number_two_cell_value():
    df = pd.DataFrame({
        "u_norm": [1, 3], "mass_density": [1, 1], "volume": [1, 1],
    })
    # e_kin = [0.5, 4.5];  q = [0.1, 0.9];  sum(q^2 * vol) = 0.82
    # PN = 1 / (total_volume * sum(q^2 * vol)) = 1 / (2 * 0.82)
    assert compute_participation_number(df) == pytest.approx(1 / (2 * 0.82))