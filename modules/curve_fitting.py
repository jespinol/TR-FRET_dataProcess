from scipy.optimize import curve_fit
from scipy.stats import t

from modules.constants import *


def fit_curve(data, model, remove_index=0):
    x_data = np.array(data[CONC])
    y_data = np.array(data[STATS][AVERAGE_SIGNAL])
    df = count_dps(data) - 1

    # Check if there are data points left
    if remove_index < len(x_data):
        # Remove the specified data point
        x_data = np.delete(x_data, remove_index)
        y_data = np.delete(y_data, remove_index)

        try:
            popt, pcov = curve_fit(model, x_data, y_data)
            kd = popt[0]

            if model == hill_equation:
                df -= 1
                nH = popt[1]
                conf_int_low, conf_int_hi, std_dev, std_err, conf_int_low_nH, conf_int_hi_nH, std_dev_nh, std_err_nh \
                    = calculate_statistics_from_fit_nh(
                    kd,
                    nH,
                    pcov,
                    df)
                result_dict = {KD: {PARAMETER: kd, CONF_INT_LOWER: conf_int_low, CONF_INT_UPPER: conf_int_hi,
                                    STD_DEV: std_dev, STD_ERR: std_err},
                               NH: {PARAMETER: nH, CONF_INT_LOWER: conf_int_low_nH, CONF_INT_UPPER: conf_int_hi_nH,
                                    STD_DEV: std_dev_nh, STD_ERR: std_err_nh}}
            else:
                conf_int_low, conf_int_hi, std_dev, std_err = calculate_statistics_from_fit(kd,
                                                                                            np.sqrt(np.diag(pcov))[0],
                                                                                            df)
                result_dict = {KD: {PARAMETER: kd, CONF_INT_LOWER: conf_int_low, CONF_INT_UPPER: conf_int_hi,
                                    STD_DEV: std_dev, STD_ERR: std_err}}

        except RuntimeError:
            result_dict = {KD: {PARAMETER: 999, CONF_INT_LOWER: 999, CONF_INT_UPPER: 999,
                                STD_DEV: 999, STD_ERR: 999},
                           NH: {PARAMETER: 999, CONF_INT_LOWER: 999, CONF_INT_UPPER: 999,
                                STD_DEV: 999, STD_ERR: 999}}
            # Call the function again with the next data point to be removed
            result_dict = fit_curve(data, model, remove_index + 1)
    else:
        # No data points left, return a default result
        result_dict = {KD: {PARAMETER: 999, CONF_INT_LOWER: 999, CONF_INT_UPPER: 999,
                            STD_DEV: 999, STD_ERR: 999},
                       NH: {PARAMETER: 999, CONF_INT_LOWER: 999, CONF_INT_UPPER: 999,
                            STD_DEV: 999, STD_ERR: 999}}

    return result_dict


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
    print(df)
    print(tcrit)
    std_dev = np.sqrt(df) * ((conf_int[1] - conf_int[0]) / (2 * tcrit))
    std_err = std_dev / np.sqrt(df)

    return conf_int[0], conf_int[1], std_dev, std_err
