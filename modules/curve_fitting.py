import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import t

from modules.constants import *


def simple_model_equation(lt, kd):
    return lt / (kd + lt)


def quadratic_model_equation(lt, kd, rt=1):
    rl = ((rt + lt + kd) - np.sqrt(((rt + lt + kd) ** 2) - (4 * rt * lt))) / 2
    return (lt - rl) / (kd + (lt - rl))


def fit_curve(data, dataset_info, model):
    x_data = np.array(data[CONC])
    y_data = np.array(data[STATS][AVERAGE_SIGNAL])
    df = dataset_info[NUM_REPEATS]

    popt, pcov = curve_fit(model, x_data, y_data)
    kd = popt[0]

    conf_int_low, conf_int_hi, std_dev, std_err = calculate_statistics_from_fit(kd, pcov, df)

    return {KD: kd, CONF_INT_LOWER: conf_int_low, CONF_INT_UPPER: conf_int_hi, STD_DEV: std_dev, STD_ERR: std_err}


def calculate_statistics_from_fit(kd, pcov, df):
    perr = np.sqrt(np.diag(pcov))
    se_a = perr[0]
    alpha = 0.05
    tcrit = t.ppf((1 - alpha / 2), df)
    conf_int = kd + np.array([-1, 1]) * tcrit * se_a
    std_dev = np.sqrt(df) * ((conf_int[1] - conf_int[0]) / (2 * tcrit))
    std_err = std_dev / np.sqrt(df)

    return conf_int[0], conf_int[1], std_dev, std_err