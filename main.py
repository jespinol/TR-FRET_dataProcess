import csv
import os

import numpy as np

from modules.constants import *
from modules.curve_fitting import fit_curve, simple_model_equation, quadratic_model_equation
from modules.save_xlsx import output_results


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

    corrected_signal[STATS] = calculate_statistics(corrected_signal)
    normalized_signal[STATS] = calculate_statistics(normalized_signal)

    fit_results = {SIMPLE_MODEL: fit_curve(normalized_signal, dataset_info, simple_model_equation),
                   QUADRATIC_MODEL: fit_curve(normalized_signal, dataset_info, quadratic_model_equation)}

    output_results(dataset_info, corrected_signal, normalized_signal, fit_results)

    return


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
