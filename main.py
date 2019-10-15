import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def readCsv(filename):
    path = "./data/"
    df = pd.read_csv(path + filename, index_col=0)
    return df

def plotCsv(df):
    df.plot();

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

if __name__ == "__main__":
    filename = "PET.csv"
    df = readCsv(filename)
    plotCsv(df)
    epsilon_ratio = getCalibrationValue(df)
    print(epsilon_ratio)