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


def create_chart(worksheet, model):
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
    chart.y_axis.title = "Normalized fluorescence"
    chart.y_axis.title.tx.rich.p[0].pPr.defRPr = axis_font
    chart.y_axis.scaling.min = 0.0
    chart.y_axis.scaling.max = 1.1
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
    chart.x_axis.scaling.max = 5.5
    chart.x_axis.txPr = RichText(
        p=[Paragraph(pPr=ParagraphProperties(defRPr=axis_label_font), endParaRPr=axis_label_font)])
    chart.x_axis.number_format = '"10"'
    chart.x_axis.majorUnit = 1.0

    # plot experimental curve as a scatter plot showing only markers
    x_values, y_values = find_xy_values_in_worksheet(worksheet, LOG_CONC, AVERAGE_SIGNAL)
    series = SeriesFactory(y_values, x_values)
    series.errBars = get_error_bars(worksheet)
    series.errBars.spPr = GraphicalProperties(ln=LineProperties(w=25400))
    series.marker = Marker(size=10, symbol="circle")
    series.graphicalProperties.line.noFill = True
    chart.series.append(series)

    # plot fitted curve as a smooth line
    x_label = f"x_{model}"
    y_label = f"y_{model}"
    x_values, y_values = find_xy_values_in_worksheet(worksheet, x_label, y_label)
    series = Series(values=y_values, xvalues=x_values)
    series.graphicalProperties.line.width = 25400
    chart.series.append(series)

    # plot a helper column to display exponent in x-axis label
    x_values, y_values = find_xy_values_in_worksheet(worksheet, HELPER_X, HELPER_Y)
    series = SeriesFactory(y_values, x_values)
    series.graphicalProperties.line.noFill = True
    series.dLbls = DataLabelList()
    for x in range(int(chart.x_axis.scaling.max) + 2):
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


def find_xy_values_in_worksheet(worksheet, x_label, y_label):
    col, row_start, row_end = find_coordinate_by_col_name(worksheet, x_label)
    x_values = Reference(worksheet, min_col=col, min_row=row_start, max_row=row_end)
    col, min_row, max_row = find_coordinate_by_col_name(worksheet, y_label)
    y_values = Reference(worksheet, min_col=col, min_row=row_start, max_row=row_end)
    return x_values, y_values


def find_coordinate_by_col_name(worksheet, column_name):
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


def get_error_bars(worksheet):
    col, row_start, row_end = find_coordinate_by_col_name(worksheet, STD_DEV)
    nds = NumDataSource(NumRef(Reference(worksheet, min_col=col, min_row=row_start, max_row=row_end)))

    return ErrorBars(plus=nds, minus=nds, errDir="y", errValType="cust")
