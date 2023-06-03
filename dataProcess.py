import csv
import re

from modules.curve_fitting import *
from modules.save_xlsx import *
import pandas as pd


def main():
    print("Program requires csv file(s) with single replicates arranged in a specific format. See README")
    while True:
        dataProcess(get_dataset_info())
        print(f"\n{'*' * 50}\n")


def get_dataset_info():
    output = {PATH: input("Enter path or 'q' to exit: ") or DEFAULT_PATH,
              PLATE_FORMAT: COLUMN_PLATE_FORMAT,
              MAX_CONC: 0,
              CONC_REVERSE: False,
              DIL_FACTOR: 0}

    if output[PATH] == "q":
        quit()

    while True:
        try:
            output[MAX_CONC] = float(
                input("Enter [max] in mM (or press enter for '10'): ") or DEFAULT_MAX_CONC)
            break
        except ValueError:
            print("Invalid input type, please enter an integer value.")

    if re.search(r"[yY]", input("Concentrations NOT in decreasing order? [y/Y for increasing] ")):
        output[CONC_REVERSE] = True

    if re.search(r"[yY]", input("Samples NOT in column format? [y/Y for row format] ")):
        output[PLATE_FORMAT] = ROW_PLATE_FORMAT

    while True:
        try:
            output[DIL_FACTOR] = int(
                input("Enter dilution factor (or press enter for '2'): ") or DEFAULT_DIL_FACTOR)
            break
        except ValueError:
            print("Invalid input type, please enter an integer value.")

    return output


def dataProcess(dataset_info):
    input_data_as_df = parse_dataset(dataset_info)

    raw_signal = format_raw_signal(input_data_as_df)

    corrected_signal = {SIGNAL_VALUES: correct_signal(raw_signal)}

    normalized_signal = {SIGNAL_VALUES: normalize_signal(corrected_signal)}

    dataset_info[NUM_REPEATS] = len(corrected_signal[SIGNAL_VALUES])
    dataset_info[NUM_DATAPOINTS] = len(next(iter(corrected_signal[SIGNAL_VALUES].values())))

    corrected_signal[CONC] = normalized_signal[CONC] = calculate_concentrations(dataset_info)
    corrected_signal[LOG_CONC] = normalized_signal[LOG_CONC] = convert_conc_to_log(corrected_signal[CONC])

    corrected_signal[STATS] = calculate_signal_statistics(corrected_signal)
    normalized_signal[STATS] = calculate_signal_statistics(normalized_signal)

    fit_results = {SIMPLE_MODEL: fit_curve(dataset_info, normalized_signal, simple_model_equation),
                   QUADRATIC_MODEL: fit_curve(dataset_info, normalized_signal, quadratic_model_equation),
                   COOPERATIVE_MODEL: fit_curve(dataset_info, normalized_signal, hill_equation)}

    output_results(dataset_info, corrected_signal, normalized_signal, fit_results)

    return


def parse_dataset(dataset_info):
    path = dataset_info[PATH]
    plate_format = dataset_info[PLATE_FORMAT]
    dfs = []
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                if file_path.endswith(".csv"):
                    dfs.append(pd.read_csv(file_path, header=None, skip_blank_lines=False))
    else:
        dfs.append(pd.read_csv(path, header=None, skip_blank_lines=False))

    if plate_format == ROW_PLATE_FORMAT:
        for i in range(0, len(dfs)):
            dfs[i] = dfs[i].transpose()

    return dfs


def format_raw_signal(dfs):
    output = {"615": {}, "665": {}}
    repeat = 0
    for df in dfs:
        # blank = pd.Series([""])
        # i0 = (df.iloc[0])
        # i1 = (df.iloc[1])
        # i4 = (df.iloc[4])
        # i5 = (df.iloc[5])
        # # print(pd.concat([i0, blank, i4], axis=0))
        # # print(pd.concat([i1, blank, i5], axis=0))
        # print((pd.concat([pd.concat([i0, blank, i4], axis=0), pd.concat([i1, blank, i5], axis=0)], axis=1)))
        repeat += 1
        output["615"][repeat] = []
        output["665"][repeat] = []
        for col in df:
            if df[col].any():
                filter = "615"
                for value in df[col]:
                    if value > 0:
                        output[filter][repeat].append(value)
                    else:
                        filter = "665"
    return output


def correct_signal(data):
    output = {}
    for i in range(1, len(data["615"]) + 1):
        data_615 = data["615"][i]
        data_665 = data["665"][i]
        repeat_signal = []
        last_index = len(data_615) - 1
        alpha = data_665[last_index] / data_615[last_index]
        first_index_of_donor_plus = len(data_615) // 2
        for p in range(first_index_of_donor_plus, last_index):
            m = p - first_index_of_donor_plus
            corrected = ((data_665[p] - (alpha * data_615[p])) - (data_665[m] - (alpha * data_615[m])))
            repeat_signal.append(corrected)
        output[i] = repeat_signal
    return output


def _format_raw_signal(data):
    output = {}
    for i in range(1, len(data["665"]) + 1):
        output[i] = _correct_signal(data["615"][i], data["665"][i])

    return output


def _parse_dataset(path):
    raw_data = {"615": {}, "665": {}}
    try:
        # check if input is a directory
        if os.path.isdir(path):
            directory_files = os.listdir(path)
            for file in directory_files:
                if file.endswith(".csv"):
                    with open(os.path.join(path, file), "r", encoding='utf-8-sig') as f:
                        reader = csv.reader(f)
                        line = next(reader)
                        raw_data["615"][len(raw_data["615"]) + 1] = parse_values_from_file(reader, line)
                        line = next(reader)
                        raw_data["665"][len(raw_data["665"]) + 1] = parse_values_from_file(reader, line)
        # if not a directory, assume it is a file
        else:
            with open(path, "r", encoding='utf-8-sig') as file:
                reader = csv.reader(file)
                line = next(reader)
                raw_data["615"][1] = parse_values_from_file(reader, line)
                line = next(reader)
                raw_data["665"][1] = parse_values_from_file(reader, line)
    except IOError:
        print("Input directory/file does not exist or does not contain a valid csv file.")

    return raw_data


def parse_values_from_file(reader, line):
    data_arr = []
    while line:
        data_arr.append(int(line[0]))
        line = next(reader, None)

    return data_arr


def _correct_signal(data_615, data_665):
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
        if data_info[CONC_REVERSE]:
            concentrations.insert(0, current_concentration)
        else:
            concentrations.append(current_concentration)
        current_concentration /= dilution_factor

    return concentrations


def convert_conc_to_log(array_of_concentrations):
    output = []
    for value in array_of_concentrations:
        output.append(np.log10(value))

    return output


def calculate_signal_statistics(data):
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
