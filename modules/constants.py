import numpy as np

# input file constant names and default values
DEFAULT_PATH = "/Users/jespinol/Downloads/data"
PATH = "Path to file(s)"
PLATE_FORMAT = "Plate format"
COLUMN_PLATE_FORMAT = "Columns"
ROW_PLATE_FORMAT = "Rows"
DEFAULT_MAX_CONC = 10
MAX_CONC = "Maximum concentration (µM)"
DEFAULT_DIL_FACTOR = 2
DIL_FACTOR = "Dilution factor"
DEFAULT_COL_NUM = 6
CHART_COL_WIDTH = 6
CHART_ROW_HEIGHT = 27

# constant names for replicate number and dataset length
NUM_REPEATS = "Number of replicates"
NUM_DATAPOINTS = "Number of datapoints per replicate"

# constant names for values to be calculated
CONC = "Concentration (nM)"
CONC_REVERSE = "Conc in increasing order"
LOG_CONC = "Log(concentration)"
SIGNAL_VALUES = "Signal"
STATS = "Statistics"
AVERAGE_SIGNAL = "Average signal"
STD_DEV = "Standard deviation"
STD_ERR = "Standard error"

# constant names for curve fitting
COOPERATIVE_MODEL = "Cooperative model"
SIMPLE_MODEL = "Simple model"
QUADRATIC_MODEL = "Quadratic model"
MODELS = [COOPERATIVE_MODEL, SIMPLE_MODEL, QUADRATIC_MODEL]


def simple_model_equation(lt, kd):
    return lt / (kd + lt)


def quadratic_model_equation(lt, kd, rt=1):
    rl = ((rt + lt + kd) - np.sqrt(((rt + lt + kd) ** 2) - (4 * rt * lt))) / 2
    return (lt - rl) / (kd + (lt - rl))


def hill_equation(lt, ec50, hill_slope):
    return np.power(lt, hill_slope) / (
            np.power(ec50, hill_slope) + np.power(lt, hill_slope))


MODEL_EQUATIONS = {COOPERATIVE_MODEL: hill_equation, SIMPLE_MODEL: simple_model_equation,
                   QUADRATIC_MODEL: quadratic_model_equation}
KD = "KD (nM)"
NH = "nH"
CONF_INT_LOWER = "CI lower bound"
CONF_INT_UPPER = "CI upper bound"
STD_DEV_FIT = "Std deviation"
STD_ERR_FIT = "Std error"

# constant names related to output file
WS_NAME = "Data"
SIGNAL_DATAFRAME_FORMAT = [LOG_CONC, SIGNAL_VALUES, STATS]
PARAMETER = "Parameter"
VALUE = "Value"
HELPER_X = "Helper x"
HELPER_Y = "Helper y"
