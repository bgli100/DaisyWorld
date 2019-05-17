import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
X_AXIS_FIELD = "tick"
Y_AXIS_FIELD = "global temperature"

CSV_FILE_NAME = "output.csv"

output = pd.read_csv(CSV_FILE_NAME)

import pylab

pylab.plot([1,1], [1,2])
pylab.show()