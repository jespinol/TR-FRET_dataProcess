import os
import csv
import numpy as np  # need to install
from scipy.optimize import curve_fit  # need to install
from scipy.stats import t
import pandas as pd  # need to install

DEFAULT_PATH = "/Users/jespinol/Downloads/TR-FRET/trfret_data"
PATH = "path to file(s)"
DEFAULT_MAX_CONC = 10
MAX_CONC = "maximum concentration in µM"
DEFAULT_DIL_FACTOR = 2
DIL_FACTOR = "dilution factor"

NUM_REPEATS = "number of replicates"
NUM_DATAPOINTS = "number of datapoints per replicate"

CONC = "concentrations in nM"
LOG_CONC = "log(concentrations)"
SIGNAL_VALUES = "signal"
STATS = "statistics"
AVERAGE_SIGNAL = "average signal"
STD_DEV = "standard deviation"
STD_ERR = "standard error"

SIMPLE = "simple two-state binding model"
QUADRATIC = "quadratic binding model"
KD = 'binding constant'
SIMPLE_FIT = "statistics of simple fit model"
QUADRATIC_FIT = "statistics of quadratic fit model"
CONF_INT = "confidence interval"
CONF_INT_LOWER = "ci lower bound"
CONF_INT_UPPER = "ci upper bound"
STD_DEV_FIT = "standard deviation"
STD_ERR_FIT = "standard error"

DATAFRAME_FORMAT = [LOG_CONC, SIGNAL_VALUES, STATS]


def main():
    print(
        "Program assumes ONE set of donor+ and donor- per file and ONE well without acceptor (which is at the last position)")
    dataset_info = get_dataset_info()
    raw_signal = open_and_parse_dataset(dataset_info[PATH])

    corrected_signal = {SIGNAL_VALUES: process_signal(raw_signal)}
    normalized_signal = {SIGNAL_VALUES: normalize_signal(corrected_signal)}

    dataset_info[NUM_REPEATS] = len(corrected_signal[SIGNAL_VALUES])
    dataset_info[NUM_DATAPOINTS] = len(next(iter(corrected_signal[SIGNAL_VALUES].values())))
    corrected_signal[CONC] = normalized_signal[CONC] = calculate_concentrations(dataset_info)
    corrected_signal[LOG_CONC] = normalized_signal[LOG_CONC] = convert_conc_log(corrected_signal[CONC])

    if dataset_info[NUM_REPEATS] > 1:
        corrected_signal[STATS] = calculate_statistics(corrected_signal)
        normalized_signal[STATS] = calculate_statistics(normalized_signal)


def get_dataset_info():
    output = {PATH: input("Enter path (or press enter for default): ") or DEFAULT_PATH,
              MAX_CONC: 0,
              DIL_FACTOR: 0}

    while True:
        try:
            output[MAX_CONC] = int(
                input("Enter [max] in mM (or press enter for default): ") or DEFAULT_MAX_CONC)
            break
        except ValueError:
            print("Invalid input type, please enter an integer value.")
    while True:
        try:
            output[DIL_FACTOR] = int(
                input("Enter dilution factor (or press enter for default): ") or DEFAULT_DIL_FACTOR)
            break
        except ValueError:
            print("Invalid input type, please enter an integer value.")

    return output


def open_and_parse_dataset(path):
    raw_data = {"615": {}, "665": {}}
    try:
        # check if input is a directory
        if os.path.isdir(path):
            directory_files = os.listdir(path)
            for file in directory_files:
                if file.endswith(".csv"):
                    with open(os.path.join(path, file), "r") as f:
                        reader = csv.reader(f)
                        line = next(reader)
                        raw_data["615"][len(raw_data["615"]) + 1] = parse_data(reader, line, True)
                        line = next(reader)
                        raw_data["665"][len(raw_data["665"]) + 1] = parse_data(reader, line, False)
        # if not a directory, assume it is a file
        else:
            with open(path, "r") as file:
                reader = csv.reader(file)
                line = next(reader)
                raw_data["615"][1] = parse_data(reader, line, True)
                line = next(reader)
                raw_data["665"][1] = parse_data(reader, line, False)
    except IOError:
        print("Input directory/file does not exist or does not contain a valid csv file.")
    return raw_data


def parse_data(reader, line, is_first_half):
    data_arr = []
    while (line != []) if is_first_half else (line is not None):
        data_arr.append(int(line[0]))
        line = next(reader, None)
    return data_arr


def process_signal(data):
    output = {}
    for i in range(1, len(data["665"]) + 1):
        output[i] = correct_signal(data["615"][i], data["665"][i])
    return output


def correct_signal(data_615, data_665):
    output = []
    last_index = len(data_615) - 1
    alpha = data_665[last_index] / data_615[last_index]
    first_index_of_donor_plus = len(data_615) // 2
    for p in range(first_index_of_donor_plus, last_index):
        m = p - first_index_of_donor_plus
        corrected = ((data_665[p] - (alpha * data_615[p])) - (data_665[m] - (alpha * data_615[m])))
        output.append(corrected)
    return output


def normalize_signal(data):
    output = {}
    for repeat, values in data[SIGNAL_VALUES].items():
        output[repeat] = []
        max_value, min_value = max(values), min(values)
        for i in range(len(values)):
            output[repeat].append((values[i] - min_value) / (max_value - min_value))
    return output


def calculate_concentrations(data_info):
    max_concentration = data_info[MAX_CONC]
    dilution_factor = data_info[DIL_FACTOR]
    num_datapoints = data_info[NUM_DATAPOINTS]

    concentrations = []
    current_concentration = float(max_concentration) * 1000
    for i in range(1, num_datapoints + 1):
        concentrations.append(current_concentration)
        current_concentration /= dilution_factor

    return concentrations


def convert_conc_log(array_of_concentrations):
    output = []
    for value in array_of_concentrations:
        output.append(np.log10(value))
    return output


def calculate_statistics(data):
    repeat_num = len(data[SIGNAL_VALUES])
    datapoint_num = len(next(iter(data[SIGNAL_VALUES].values())))
    values = np.zeros((repeat_num, datapoint_num))

    for i in range(repeat_num):
        values[i, :] = np.array(data[SIGNAL_VALUES][i + 1])

    averages = (np.mean(values, axis=0)).tolist()
    std_devs_pop = (np.std(values, axis=0, ddof=0)).tolist()
    std_errors_mean = (std_devs_pop / np.sqrt(repeat_num)).tolist()

    return {AVERAGE_SIGNAL: averages, STD_DEV: std_devs_pop, STD_ERR: std_errors_mean}


main()
