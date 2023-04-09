import csv
import os
import time
import numpy as np  # need to install
import openpyxl  # need to install
import openpyxl.chart.label
import pandas as pd  # need to install

from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.chart.data_source import NumDataSource, NumRef
from openpyxl.chart.error_bar import ErrorBars
from openpyxl.chart.marker import Marker
from openpyxl.chart.series_factory import SeriesFactory
from scipy.optimize import curve_fit  # need to install
from scipy.stats import t

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

SIMPLE_MODEL = "simple model"
QUADRATIC_MODEL = "quadratic model"
KD = "binding constant"
CONF_INT = "confidence interval"
CONF_INT_LOWER = "ci lower bound"
CONF_INT_UPPER = "ci upper bound"
STD_DEV_FIT = "standard deviation"
STD_ERR_FIT = "standard error"

DATAFRAME_FORMAT = [LOG_CONC, SIGNAL_VALUES, STATS]

SELECTED_MODEL = SIMPLE_MODEL
CALC_X = "Calculated x"
CALC_Y = "Calculated y"


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

    perr = np.sqrt(np.diag(pcov))
    se_a = perr[0]
    alpha = 0.05
    tcrit = t.ppf((1 - alpha / 2), df)
    conf_int = kd + np.array([-1, 1]) * tcrit * se_a
    std_dev = np.sqrt(df) * ((conf_int[1] - conf_int[0]) / (2 * tcrit))
    std_err = std_dev / np.sqrt(df)

    return {KD: kd, CONF_INT_LOWER: conf_int[0], CONF_INT_UPPER: conf_int[1], STD_DEV: std_dev, STD_ERR: std_err}


def output_results(dataset_info, data_corrected, data_normalized, fit):
    path = dataset_info[PATH]
    filename = create_workbook(path)

    writer = pd.ExcelWriter(filename, engine="openpyxl", mode="a", if_sheet_exists="overlay")

    # add normalized data to the output file
    df_normalized = create_signal_DataFrame(data_normalized)
    df_normalized.to_excel(writer, sheet_name="normalized", index=False)

    # add curve fitting data
    df_fit = create_fit_DataFrame(fit)
    df_fit.to_excel(writer, sheet_name="normalized", index=False, startrow=dataset_info[NUM_DATAPOINTS] + 5)

    # add a plot of log(concentration) vs. normalized signal
    plot_worksheet = writer.sheets["normalized"]
    fitted_curve_datapoints = calculate_fitted_curve_datapoints(data_normalized, fit)
    df_fitted_data = pd.DataFrame(data=fitted_curve_datapoints)
    df_fitted_data.to_excel(writer, sheet_name="normalized", index=False, startcol=26)
    chart = create_chart(plot_worksheet)
    plot_worksheet.add_chart(chart, "I2")

    # add unnormalized data to the same file but in a different worksheet
    df_corrected = create_signal_DataFrame(data_corrected)
    df_corrected.to_excel(writer, sheet_name="unnormalized", index=False)

    writer.close()


def create_workbook(path):
    # add a suffix with the current time so the file will always be unique
    filename_suffix = time.strftime("%Y%m%d-%H%M%S")

    # if a single input file was provided, output will have the same filename with xlsx extension
    # if a directory was provided as input, the output name will have the name of the directory
    if path.endswith(".csv"):
        root, extension = os.path.splitext(path)
        filename = f"{root}_{filename_suffix}.xlsx"
    else:
        parent_dir = os.path.basename(path)
        filename = f"{path}/{parent_dir}_{filename_suffix}.xlsx"

    # open a new workbook and rename the default worksheet name
    workbook = openpyxl.Workbook()
    workbook["Sheet"].title = "normalized"
    workbook.save(filename)

    # returns the path to the output file so that ExcelWriter and other writing functions can find it
    return filename


def create_signal_DataFrame(data):
    df_dict = {}
    for column in DATAFRAME_FORMAT:
        if column == SIGNAL_VALUES:
            for repeat in data[column]:
                label = f"repeat {repeat}"
                df_dict[label] = data[column][repeat]
        elif column == STATS:
            for stat in data[column]:
                df_dict[stat] = data[column][stat]
        else:
            df_dict[column] = data[column]

    df_dict = {**{CONC: data[CONC]}, **df_dict}

    return pd.DataFrame(df_dict)


def create_fit_DataFrame(fit_data):
    df = pd.DataFrame(fit_data)
    df = df.transpose()
    df.index.name = "model"
    df.reset_index(inplace=True)
    df.rename(columns={"index": "Parameter"}, inplace=True)
    return df


def create_chart(worksheet):
    # initialize a chart object, set size, remove legend
    chart = ScatterChart()
    chart.height = 15.24
    chart.width = 22.86
    chart.legend = None

    # x-axis settings
    chart.y_axis.majorGridlines = None
    chart.y_axis.title = "Normalized Signal"
    chart.y_axis.majorTickMark = "in"
    chart.y_axis.scaling.max = 1.1
    chart.y_axis.scaling.min = -0.1
    chart.x_axis.majorGridlines = None

    # y-axis settings
    chart.x_axis.title = "[Ligand] nM"
    chart.x_axis.majorTickMark = "in"
    chart.x_axis.crosses = "min"

    # plot experimental curve as a scatter plot showing only markers
    col, row_start, row_end = find_column_row(worksheet, LOG_CONC)
    x_values = Reference(worksheet, min_col=col, min_row=row_start, max_row=row_end)
    col, row_start, row_end = find_column_row(worksheet, AVERAGE_SIGNAL)
    y_values = Reference(worksheet, min_col=col, min_row=row_start, max_row=row_end)
    series = SeriesFactory(y_values, x_values)
    series.errBars = get_error_bars(worksheet)
    series.marker = Marker(size=15, symbol="circle")
    series.graphicalProperties.line.noFill = True
    chart.series.append(series)

    # plot fitted curve as a smooth line
    col, row_start, row_end = find_column_row(worksheet, CALC_X)
    x_values = Reference(worksheet, min_col=col, min_row=row_start, max_row=row_end)
    col, min_row, max_row = find_column_row(worksheet, CALC_Y)
    y_values = Reference(worksheet, min_col=col, min_row=row_start, max_row=row_end)

    # curve = ScatterChart()
    series = Series(values=y_values, xvalues=x_values)
    chart.series.append(series)

    return chart


def get_error_bars(worksheet):
    col, row_start, row_end = find_column_row(worksheet, STD_DEV)
    nds = NumDataSource(NumRef(Reference(worksheet, min_col=col, min_row=row_start, max_row=row_end)))
    return ErrorBars(plus=nds, minus=nds, errDir="y", errValType="stdDev")


def find_column_row(worksheet, column_name):
    col, row_start, row_end = 0, 2, 0
    for column_cell in worksheet.columns:
        col += 1
        if column_cell[0].value == column_name:
            for column_row in worksheet.iter_cols(min_row=1, min_col=col, max_col=col):
                for cell in column_row:
                    if cell.value is not None:
                        row_end += 1
                    else:
                        break
            break

    return col, row_start, row_end


def calculate_fitted_curve_datapoints(data, fit):
    max_concentration = data[CONC][0] * 1.1
    min_concentration = data[CONC][-1] * 0.9
    kd = fit[SELECTED_MODEL][KD]

    if SELECTED_MODEL == SIMPLE_MODEL:
        model_equation = simple_model_equation
    else:
        model_equation = quadratic_model_equation

    fit_x_values = []
    fit_y_values = []
    current_x = max_concentration
    while current_x > min_concentration:
        fit_x_values.append(np.log10(current_x))
        fit_y_values.append(model_equation(current_x, kd))
        current_x *= 0.9

    return {CALC_X: fit_x_values, CALC_Y: fit_y_values}


main()
