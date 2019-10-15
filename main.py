import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def readCsv(material):
    path = "./data/"
    df = pd.read_csv(path + material + ".csv", index_col=0)
    return df


def getCalibrationValue(df):

    target_values = df["Analog2[V]"]
    threshold = 0.18

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
    start_flag = False
    cnt = 0
    cnt_threshold = 10
    for (time, val1, val2, val3) in zip(times, analog1, analog2, analog9):
        if((val1 > 0.0) and (val2 > 0.0) and (val3 > 0.0)):
            if(not start_flag):
                start = time
                init_val1 = val1
                init_val2 = val2
                init_val3 = val3
            start_flag = True
            if(cnt > cnt_threshold):
                break
        else:
            start_flag = False

        if(start_flag):
            cnt += 1
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


def plotNorminalSSCurve(df, tensile_list, E_list, Y_list):
    x1 = df["strain [%]"]
    x2 = df["strain from stroke [%]"]
    y = df["stress [MPa]"]

    tensile_strength = tensile_list[0]
    tensile_strain = tensile_list[1]
    tensile_strain_from_stroke = tensile_list[2]

    E_strain = E_list[0][0]
    E_starin_b = E_list[0][1]

    E_strain_from_stroke = E_list[1][0]
    E_strain_from_stroke_b = E_list[1][1]

    yield_stress = Y_list[0][0]
    yield_strain = Y_list[0][1]

    yield_stress_from_stroke = Y_list[1][0]
    yield_strain_from_stroke = Y_list[1][1]

    plt.figure()

    plt.plot(x1,y, label = "Strain Gauge")
    plt.plot(tensile_strain, tensile_strength, marker="x", color="red")
    plt.plot(yield_strain, yield_stress, marker="x", color="red")
    # plt.plot(x1, x1 * E_strain + E_starin_b, linestyle="dashed", color="gray")
    plt.plot(x1, (x1 - 0.2) * E_strain + E_starin_b, linestyle="dashdot", color="gray")

    plt.plot(x2,y, label = "Stroke")
    plt.plot(tensile_strain_from_stroke, tensile_strength, marker="x", color="red")
    plt.plot(yield_strain_from_stroke, yield_stress_from_stroke, marker="x", color="red")
    # plt.plot(x2, x2 * E_strain_from_stroke + E_strain_from_stroke_b, linestyle="dashed",color="gray")
    plt.plot(x2, (x2 - 0.2) * E_strain_from_stroke + E_strain_from_stroke_b, linestyle="dashdot",color="gray")

    plt.title("Norminal Stress - Strain Curve")
    plt.xlabel("Strain [%]")
    plt.ylabel("Stress [MPa]")
    plt.ylim([tensile_strength * (-0.1), tensile_strength * 1.2])
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


def getYoungModulesLineByStress(df, tensile_strength):

    normianl_stress = df["stress [MPa]"]
    normianl_strain = df["strain [%]"]

    stress_list = []
    strain_list = []
    for (stress, strain) in zip(normianl_stress, normianl_strain):
        stress_list.append(stress)
        strain_list.append(strain)
        if(stress > 0.33 * tensile_strength):
            break

    return calcYoungModules(np.array(strain_list), np.array(stress_list))


def getYoungModulesLineByStressFromStroke(df, tensile_strength):

    normianl_stress = df["stress [MPa]"]
    normianl_strain = df["strain from stroke [%]"]

    stress_list = []
    strain_list = []
    for (stress, strain) in zip(normianl_stress, normianl_strain):
        if(stress > 0.1 * tensile_strength):
            stress_list.append(stress)
            strain_list.append(strain)
        if(stress > 0.33 * tensile_strength):
            break

    return calcYoungModules(np.array(strain_list), np.array(stress_list))


def getYieldStressByStrain(df, E_list):
    x = df["strain [%]"]
    y = df["stress [MPa]"]

    E_strain = E_list[0]
    E_strain_b = E_list[1]

    df["tmp"] = abs(y - yieldStressLine(x, E_strain, E_strain_b))
    tmp = df[df["tmp"] == min(df["tmp"])]
    strain = np.average(tmp["strain [%]"])
    stress = np.average(tmp["stress [MPa]"])
    return [stress, strain]


def getYieldStressByStrainFromStroke(df, E_list):
    x = df["strain from stroke [%]"]
    y = df["stress [MPa]"]

    E_strain = E_list[0]
    E_strain_b = E_list[1]

    df["tmp"] = abs(y - yieldStressLine(x, E_strain, E_strain_b))
    tmp = df[df["tmp"] == min(df["tmp"])]
    strain = np.average(tmp["strain from stroke [%]"])
    stress = np.average(tmp["stress [MPa]"])
    return [stress, strain]


def yieldStressLine(x, a,b):
    return a * (x - 0.2) + b


def calcYoungModules(x,y):
    a, b= np.polyfit(x, y, 1)
    return a, b


if __name__ == "__main__":
    material = "PET"
    # materials = ["Al", "Fe_ro", "Fe_water", "Mg", "PET", "Ti"]

    df = readCsv(material)
    area = getArea(material)
    strain_ratio = getCalibrationValue(df)
    print(strain_ratio)

    df = getStartPoint(df)
    df = convertValues(df, area, strain_ratio)

    tensile_list = getTensileStrength(df)
    tensile_strength = tensile_list[0]

    E_strain, E_strain_b = getYoungModulesLineByStress(df, tensile_strength)
    E_strain_from_stroke, E_strain_from_stroke_b = getYoungModulesLineByStressFromStroke(df, tensile_strength)
    E_list = [[E_strain, E_strain_b], [E_strain_from_stroke, E_strain_from_stroke_b]]

    yield_stress, yield_strain = getYieldStressByStrain(df, E_list[0])
    yield_stress_from_stroke, yield_strain_from_stroke = getYieldStressByStrainFromStroke(df, E_list[1])
    Y_list =[[yield_stress, yield_strain], [yield_stress_from_stroke, yield_strain_from_stroke]]

    # plotNorminalSSCurve(df, tensile_list, E_list, Y_list)
    # plotTrueSSCurve(df)