"""The planted biases exist and are measurably large; if these fail, the
lab is demonstrating weighting against a panel that never needed it."""

import numpy as np

import config


def test_panel_demographics_diverge_from_census(shop):
    panelists = shop.panelists()
    census = shop.census_margins()
    initial = panelists[panelists["joined_month"] == 1]
    ai_panel = np.zeros(12)
    for _, r in initial.iterrows():
        a = config.AGE_BANDS.index(r["age_band"])
        i = config.INCOME_BANDS.index(r["income_band"])
        ai_panel[a * 3 + i] += 1
    ai_panel /= ai_panel.sum()
    cz = census[census["margin"] == "age_income"].copy()
    ai_pop = np.zeros(12)
    for _, r in cz.iterrows():
        a = config.AGE_BANDS.index(r["age_band"])
        i = config.INCOME_BANDS.index(r["income_band"])
        ai_pop[a * 3 + i] = r["population"]
    ai_pop /= ai_pop.sum()

    assert np.abs(ai_panel - ai_pop).max() > 0.02, "no visible composition skew"
    young_high = config.AGE_BANDS.index("18-29") * 3 + config.INCOME_BANDS.index("high")
    old_low = config.AGE_BANDS.index("60+") * 3 + config.INCOME_BANDS.index("low")
    over = ai_panel[young_high] / ai_pop[young_high]
    under = ai_panel[old_low] / ai_pop[old_low]
    assert over / under > 1.5, "recruitment skew gradient missing"


def test_attrition_thins_the_panel(shop):
    panelists = shop.panelists()
    initial = panelists[panelists["joined_month"] == 1]
    still = (initial["left_month"] == 0).sum()
    frac_left = 1.0 - still / len(initial)
    assert 0.15 < frac_left < 0.50, f"attrition out of band: {frac_left:.2%}"
