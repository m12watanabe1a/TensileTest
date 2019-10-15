import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def readCsv(material):
    path = "./data/"
    df = pd.read_csv(path + material + ".csv", index_col=0)
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

def getArea(material):
    path = "./data/"
    df = pd.read_csv(path + material + "_plate.csv")
    width = df["width[mm]"][0]
    thickness = df["thickness[mm]"][0]
    return width * thickness

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

def convertValues(df, area, strain_ratio):

    load_ratio = 2000
    stroke_ratio = 6
    initial_length = 35

    df = df.rename(columns={"Analog1[V]": "load [N]", "Analog2[V]": "strain [%]", "Analog9[V]": "stroke [mm]"})

    df["load [N]"] *= load_ratio
    df["strain [%]"] /= strain_ratio
    df["stroke [mm]"] *= stroke_ratio
    df["strain from stroke [%]"] = df["stroke [mm]"] * 100 / initial_length
    df["stress [MPa]"] = df["load [N]"] / area

    return df

def plotNorminalSSCurve(df, tensile_list):
    x1 = df["strain [%]"]
    x2 = df["strain from stroke [%]"]
    y = df["stress [MPa]"]

    tensile_strength = tensile_list[0]
    tensile_strain = tensile_list[1]
    tensile_strain_from_stroke = tensile_list[2]

    plt.figure()

    plt.plot(x1,y, label = "Strain Gauge")
    plt.plot(tensile_strain, tensile_strength, marker="x", color="red")

    plt.plot(x2,y, label = "Stroke")
    plt.plot(tensile_strain_from_stroke, tensile_strength, marker="x", color="red")

    plt.title("Norminal Stress - Strain Curve")
    plt.xlabel("Strain [%]")
    plt.ylabel("Stress [MPa]")
    plt.legend(bbox_to_anchor=(1, 1), loc='upper right')
    plt.grid()
    plt.show()

def plotTrueSSCurve(df):

    x1 = np.log(1 + df["strain [%]"] / 100) * 100
    y1 = df["stress [MPa]"] * (1 + df["strain [%]"] / 100)

    x2 = np.log(1 + df["strain from stroke [%]"] /100) * 100
    y2 = df["stress [MPa]"] * (1 + df["strain from stroke [%]"] / 100)

    plt.figure()

    plt.plot(x1,y1, label = "Strain Gauge")

    plt.plot(x2,y2, label = "Stroke")

    plt.title("True Stress - True Strain Curve")
    plt.xlabel("Strain [%]")
    plt.ylabel("Stress [MPa]")
    plt.legend(bbox_to_anchor=(1, 1), loc='upper right')
    plt.grid()
    plt.show()

def getTensileStrength(df):
    stress = max(df["stress [MPa]"])
    strain = np.average(df[df["stress [MPa]"] == stress]["strain [%]"])
    strain_from_stroke = np.average(df[df["stress [MPa]"] == stress]["strain from stroke [%]"])
    return [stress, strain, strain_from_stroke]

if __name__ == "__main__":
    material = "Ti"

    df = readCsv(material)
    area = getArea(material)
    strain_ratio = getCalibrationValue(df)
    df = getStartPoint(df)
    df = convertValues(df, area, strain_ratio)

    tensile_list = getTensileStrength(df)
    # plotNorminalSSCurve(df, tensile_list)
    plotTrueSSCurve(df)