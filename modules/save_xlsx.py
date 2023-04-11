import os
import time

import openpyxl.chart.label
import openpyxl.utils.cell
import pandas as pd

from modules.plotting import *


def output_results(dataset_info, data_corrected, data_normalized, fit):
    path = dataset_info[PATH]
    workbook = create_workbook(path)

    writer = pd.ExcelWriter(workbook, engine="openpyxl", mode="a", if_sheet_exists="overlay")

    # add normalized data to the output file
    df_normalized = create_signal_DataFrame(data_normalized)
    df_normalized.to_excel(writer, sheet_name=NORMALIZED_WS, index=False)

    # add curve fitting data
    df_fit = create_fit_DataFrame(fit)
    df_fit.to_excel(writer, sheet_name=NORMALIZED_WS, index=False, startrow=dataset_info[NUM_DATAPOINTS] + 5)

    # add theoretical data based on fit
    fitted_curve_datapoints = calculate_fitted_curve_datapoints(data_normalized, fit)
    df_fitted_data = pd.DataFrame(data=fitted_curve_datapoints)
    df_fitted_data.to_excel(writer, sheet_name=NORMALIZED_WS, index=False, startcol=26)

    # add helper series for chart x-axis labels
    df_helper_data = pd.DataFrame(data={HELPER_X: [0, 1, 2, 3, 4], HELPER_Y: [0, 0, 0, 0, 0]})
    df_helper_data.to_excel(writer, sheet_name=NORMALIZED_WS, index=False, startcol=29)

    # add a plot of log(concentration) vs. normalized signal including the fitted curve
    plot_worksheet = writer.sheets[NORMALIZED_WS]
    chart = create_chart(plot_worksheet)
    plot_worksheet.add_chart(chart, "J2")

    # add unnormalized data to the same file but in a different worksheet
    df_corrected = create_signal_DataFrame(data_corrected)
    df_corrected.to_excel(writer, sheet_name=UNNORMALIZED_WS, index=False)

    writer.close()
    return


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
    workbook["Sheet"].title = NORMALIZED_WS

    # increase the width of a number of columns
    resize_columns(workbook)

    workbook.save(filename)

    # returns the path to the output file so that ExcelWriter and other writing functions can find it
    return filename


def resize_columns(workbook):
    for worksheet in workbook.sheetnames:
        sheet = workbook[worksheet]
        for col_idx in range(1, 20):
            col_letter = openpyxl.utils.get_column_letter(col_idx)
            sheet.column_dimensions[col_letter].width = 17

    return


def create_signal_DataFrame(data):
    df_dict = {}
    for column in DATAFRAME_FORMAT:
        if column == SIGNAL_VALUES:
            for repeat in data[column]:
                label = f"Repeat {repeat}"
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
