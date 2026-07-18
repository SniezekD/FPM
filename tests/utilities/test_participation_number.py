import pandas as pd
import pytest

from fpm.utilities.participation_number import compute_participation_number


def test_participation_number_two_uniform_cells():
    df = pd.DataFrame({
        "u_norm": [1, 3], "mass_density": [1, 1], "volume": [1, 1],
    })
    # e_kin = [0.5, 4.5];  q = [0.1, 0.9];  sum(q^2 * vol) = 0.82
    # PN = 1 / (total_volume * sum(q^2 * vol)) = 1 / (2 * 0.82)
    assert compute_participation_number(df) == pytest.approx(1 / (2 * 0.82))


def test_participation_number_two_nonuniform_cells():
    df = pd.DataFrame({
        "u_norm": [1, 3], "mass_density": [1, 1], "volume": [11, 1],
    })
    # total e_kin: 0.5 * ((1 * 1 * 11) + (9 * 1 * 1)) = 10
    # total volume: 11 + 1 = 12
    # q: 1 * 1**2 / (2 * 10) = 1/20, 1 * 3**2 / (2 * 10) = 9/20
    # q**2: 1/400, 81/400
    # particiation number: 1 / (12 * (1/400 * 11 + 81/400 * 1)) = 
    #                    = 1 / (12 * (11/400 + 81/400))
    #                    = 1 / (12 * 92/400)
    #                    = 1 / (12 * 92/400)
    #                    = 1 / (1104/400)
    #                    = 1 / 2.76 
    #                    = 0.362318841
    assert compute_participation_number(df) == pytest.approx(0.362318841)
