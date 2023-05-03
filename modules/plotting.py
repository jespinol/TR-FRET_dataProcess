import numpy as np
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.chart.data_source import NumDataSource, NumRef
from openpyxl.chart.error_bar import ErrorBars
from openpyxl.chart.label import DataLabelList, DataLabel
from openpyxl.chart.marker import Marker
from openpyxl.chart.series_factory import SeriesFactory
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.chart.text import RichText
from openpyxl.drawing.line import LineProperties
from openpyxl.drawing.text import Font, CharacterProperties, Paragraph, ParagraphProperties

from modules.constants import *
from modules.curve_fitting import simple_model_equation, quadratic_model_equation


def create_chart(worksheet):
    # initialize a chart object, set size, remove legend
    chart = ScatterChart()
    chart.height = 15.24
    chart.width = 22.86
    chart.legend = None
    chart.graphical_properties = GraphicalProperties(ln=LineProperties(noFill=True))
    font = Font(typeface="Calibri")
    axis_font = CharacterProperties(latin=font, sz=2000)
    axis_label_font = CharacterProperties(latin=font, sz=1800)
    axis_superscript_font = CharacterProperties(latin=font, sz=1300)

    # y-axis settings
    chart.y_axis.majorGridlines = None
    chart.y_axis.majorTickMark = "in"
    chart.y_axis.title = "Fraction Bound"
    chart.y_axis.title.tx.rich.p[0].pPr.defRPr = axis_font
    chart.y_axis.scaling.min = 0.0
    chart.y_axis.scaling.max = 1.0
    chart.y_axis.txPr = RichText(
        p=[Paragraph(pPr=ParagraphProperties(defRPr=axis_label_font), endParaRPr=axis_label_font)])
    chart.y_axis.number_format = "#,##0.0"
    chart.y_axis.majorUnit = 0.2

    # x-axis settings
    chart.x_axis.majorGridlines = None
    chart.x_axis.majorTickMark = "in"
    chart.x_axis.title = "[Ligand] nM"
    chart.x_axis.title.tx.rich.p[0].pPr.defRPr = axis_font
    chart.x_axis.crosses = "min"
    chart.x_axis.scaling.min = 0.0
    chart.x_axis.scaling.max = 4.0
    chart.x_axis.txPr = RichText(
        p=[Paragraph(pPr=ParagraphProperties(defRPr=axis_label_font), endParaRPr=axis_label_font)])
    chart.x_axis.number_format = '"10"'
    chart.x_axis.majorUnit = 1.0

    # plot experimental curve as a scatter plot showing only markers
    col, row_start, row_end = find_column_and_rows(worksheet, LOG_CONC)
    x_values = Reference(worksheet, min_col=col, min_row=row_start, max_row=row_end)
    col, row_start, row_end = find_column_and_rows(worksheet, AVERAGE_SIGNAL)
    y_values = Reference(worksheet, min_col=col, min_row=row_start, max_row=row_end)
    series = SeriesFactory(y_values, x_values)
    series.errBars = get_error_bars(worksheet)
    series.errBars.spPr = GraphicalProperties(ln=LineProperties(w=25400))
    series.marker = Marker(size=15, symbol="circle")
    series.graphicalProperties.line.noFill = True
    chart.series.append(series)

    # plot fitted curve as a smooth line
    col, row_start, row_end = find_column_and_rows(worksheet, CALC_X)
    x_values = Reference(worksheet, min_col=col, min_row=row_start, max_row=row_end)
    col, min_row, max_row = find_column_and_rows(worksheet, CALC_Y)
    y_values = Reference(worksheet, min_col=col, min_row=row_start, max_row=row_end)
    series = Series(values=y_values, xvalues=x_values)
    chart.series.append(series)

    # plot a helper column to display exponent in x-axis label
    col, row_start, row_end = find_column_and_rows(worksheet, HELPER_X)
    x_values = Reference(worksheet, min_col=col, min_row=row_start, max_row=row_end)
    col, row_start, row_end = find_column_and_rows(worksheet, HELPER_Y)
    y_values = Reference(worksheet, min_col=col, min_row=row_start, max_row=row_end)
    series = SeriesFactory(y_values, x_values)
    series.graphicalProperties.line.noFill = True
    series.dLbls = DataLabelList()
    for x in range(4 + 1):
        data_label = DataLabel(x)
        data_label.text = f"{x}"
        data_label.showCatName = True
        data_label.showVal = False
        data_label.position = "b"
        series.dLbls.dLbl.append(data_label)
    series.dLbls.numFmt = '"          "0;#'
    series.dLbls.txPr = RichText(
        p=[Paragraph(pPr=ParagraphProperties(defRPr=axis_superscript_font), endParaRPr=axis_superscript_font)])
    chart.series.append(series)

    return chart


def get_error_bars(worksheet):
    col, row_start, row_end = find_column_and_rows(worksheet, STD_DEV)
    nds = NumDataSource(NumRef(Reference(worksheet, min_col=col, min_row=row_start, max_row=row_end)))

    return ErrorBars(plus=nds, minus=nds, errDir="y", errValType="cust")


def find_column_and_rows(worksheet, column_name):
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
    max_concentration = data[CONC][0] * 1.2
    min_concentration = data[CONC][-1] * 0.8
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
