import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def readCsv(filename):
    path = "./data/"
    df = pd.read_csv(path + filename, index_col=0)
    return df

def getCalibrationValue(df):

    target_values = df["Analog2[V]"]
    initial_value = target_values[0]
    threshold = 0.12 + initial_value

    stack_values = []
    calib_frag = False
    for target_value in target_values:
        if( target_value > threshold):
            stack_values.append(target_value)
            if(not calib_frag):
                calib_frag = True
        if( (target_value < threshold) and calib_frag):
            break
    return sum(stack_values) / len(stack_values)

def getStartPoint(df):
    times = df.index.values.tolist()
    analog1 = df["Analog1[V]"]
    analog2 = df["Analog2[V]"]
    analog9 = df["Analog9[V]"]
    for (time, val1, val2, val3) in zip(times, analog1, analog2, analog9):
        if((val1 > 0.0) and (val2 > 0.0) and (val3 > 0.0)):
            start = time
            init_val1 = val1
            init_val2 = val2
            init_val3 = val3
            break
    df["Analog1[V]"] -= init_val1
    df["Analog2[V]"] -= init_val2
    df["Analog9[V]"] -= init_val3
    return df[start:]

if __name__ == "__main__":
    filename = "PET.csv"
    df = readCsv(filename)
    epsilon_ratio = getCalibrationValue(df)
    tensile_value = getStartPoint(df)

    tensile_value.plot()
    plt.show()