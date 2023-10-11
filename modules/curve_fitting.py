from scipy.optimize import curve_fit
from scipy.stats import t

from modules.constants import *


def fit_curve(data, model):
    x_data = np.array(data[CONC])
    y_data = np.array(data[STATS][AVERAGE_SIGNAL])
    df = count_dps(data) - 1

    try:
        popt, pcov = curve_fit(model, x_data, y_data)
        kd = popt[0]

        if model == hill_equation:
            df -= 1
            nH = popt[1]
            conf_int_low, conf_int_hi, std_dev, std_err, conf_int_low_nH, conf_int_hi_nH, std_dev_nh, std_err_nh = calculate_statistics_from_fit_nh(
                kd,
                nH,
                pcov,
                df)
            return {KD: {PARAMETER: kd, CONF_INT_LOWER: conf_int_low, CONF_INT_UPPER: conf_int_hi,
                         STD_DEV: std_dev, STD_ERR: std_err},
                    NH: {PARAMETER: nH, CONF_INT_LOWER: conf_int_low_nH, CONF_INT_UPPER: conf_int_hi_nH,
                         STD_DEV: std_dev_nh, STD_ERR: std_err_nh}}

        conf_int_low, conf_int_hi, std_dev, std_err = calculate_statistics_from_fit(kd, np.sqrt(np.diag(pcov))[0], df)
        return {KD: {PARAMETER: kd, CONF_INT_LOWER: conf_int_low, CONF_INT_UPPER: conf_int_hi,
                     STD_DEV: std_dev, STD_ERR: std_err}}
    except RuntimeError:
        return {KD: {PARAMETER: 999, CONF_INT_LOWER: 999, CONF_INT_UPPER: 999,
                     STD_DEV: 999, STD_ERR: 999},
                NH: {PARAMETER: 999, CONF_INT_LOWER: 999, CONF_INT_UPPER: 999,
                     STD_DEV: 999, STD_ERR: 999}}


def count_dps(data):
    total = 0
    for _, values in data[SIGNAL_VALUES].items():
        total = len(values)
    return total


def calculate_statistics_from_fit_nh(kd, nH, pcov, df):
    perr = np.sqrt(np.diag(pcov))
    conf_int_low, conf_int_hi, std_dev, std_err = calculate_statistics_from_fit(kd, perr[0], df)
    conf_int_low_nH, conf_int_hi_nH, std_dev_nh, std_err_nh = calculate_statistics_from_fit(nH, perr[1], df)
    return conf_int_low, conf_int_hi, std_dev, std_err, conf_int_low_nH, conf_int_hi_nH, std_dev_nh, std_err_nh


def calculate_statistics_from_fit(param, perr, df):
    alpha = 0.05
    tcrit = t.ppf((1 - alpha / 2), df)
    conf_int = param + np.array([-1, 1]) * tcrit * perr
    std_dev = np.sqrt(df) * ((conf_int[1] - conf_int[0]) / (2 * tcrit))
    std_err = std_dev / np.sqrt(df)

    return conf_int[0], conf_int[1], std_dev, std_err
