import numpy as np
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.chart.data_source import NumDataSource, NumRef
from openpyxl.chart.error_bar import ErrorBars
from openpyxl.chart.marker import Marker
from openpyxl.chart.series_factory import SeriesFactory

from modules.constants import *
from modules.curve_fitting import simple_model_equation, quadratic_model_equation


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

    # y-axis settings
    chart.x_axis.title = "[Ligand] nM"
    chart.x_axis.majorTickMark = "in"
    chart.x_axis.crosses = "min"
    chart.x_axis.scaling.min = 0
    chart.x_axis.majorGridlines = None

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

    return ErrorBars(plus=nds, minus=nds, errDir="y", errValType="cust")


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
