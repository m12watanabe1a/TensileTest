import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 降伏点が明確に存在する材料
WITH_UPPER_YIELD_POINT = ["Al", "Fe_ro"]
POLYMERS = ["PET"]
MATERIAL_MAPPER = {"Al": "Alminium", "Fe_ro": "Annealed Iron", "Fe_water": "Quenched Iron", "Mg": "Magnesium", "PET": "PET", "Ti": "Titanium"}

COLOR = "orange"

# csvファイル読み込み
def readCsv(material):
    path = "./data/"
    df = pd.read_csv(path + material + ".csv", index_col=0)
    return df


# 歪みゲージの値を取得
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


# 断面積情報の取得
def getArea(material):
    path = "./data/"
    df = pd.read_csv(path + material + "_plate.csv")
    width = df["width[mm]"][0]
    thickness = df["thickness[mm]"][0]
    return width * thickness


# 引張試験の開始点を取得
def getStartPoint(df):
    times = df.index.values.tolist()
    analog1 = df["Analog1[V]"]
    analog2 = df["Analog2[V]"]
    analog9 = df["Analog9[V]"]
    start_flag = False
    cnt = 0
    cnt_threshold = 10

    val1_pre = analog1[0]
    val2_pre = analog2[0]
    val3_pre = analog9[0]

    for (time, val1, val2, val3) in zip(times, analog1, analog2, analog9):
        if((val1 - val1_pre > 0.0) and (val2 - val2_pre > 0.0) and (val3 - val3_pre > 0.0)):
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

        val1_pre = val1
        val2_pre = val2
        val3_pre = val3

    df["Analog1[V]"] -= init_val1
    df["Analog2[V]"] -= init_val2
    df["Analog9[V]"] -= init_val3

    return df[start:]


# 電圧を物性に変換
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


# 公称応力歪み線図の描画
def plotNorminalSSCurve(df, tensile_list, E_list, Y_list, brokenPoint, material):
    path = "./results/" + material + "/"
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

    # 歪みゲージ
    plt.figure()
    plt.plot(x1,y, label = "Strain Gauge", color=COLOR)
    plt.plot(tensile_strain, tensile_strength, marker="x", color="red")
    plt.plot(yield_strain, yield_stress, marker="x", color="red")
    # plt.plot(x1, x1 * E_strain + E_starin_b, linestyle="dashed", color="gray")

    if material in WITH_UPPER_YIELD_POINT:
        plt.plot(x1, x1 * E_strain + E_starin_b, linestyle="dashdot", color="gray")
    elif material in POLYMERS:
        plt.plot([0, 0.8*tensile_strain], [0,0.8*E_strain * tensile_strain], linestyle="dashdot", color="gray")
    else:
        plt.plot(x1, (x1 - 0.2) * E_strain + E_starin_b, linestyle="dashdot", color="gray")

    # plt.title("Norminal Stress - Strain Curve of " + MATERIAL_MAPPER[material] + " (Strain Gauge)")
    plt.xlabel("Strain [%]")
    plt.ylabel("Stress [MPa]")
    plt.ylim([tensile_strength * (-0.1), tensile_strength * 1.2])
    # plt.legend(bbox_to_anchor=(1, 1), loc='upper right')
    plt.grid()
    plt.savefig(path + 'NSSG.pdf')
    # plt.show()

    # ストローク
    plt.figure()
    plt.plot(x2,y, label = "Stroke", color=COLOR)
    plt.plot(tensile_strain_from_stroke, tensile_strength, marker="x", color="red")
    plt.plot(yield_strain_from_stroke, yield_stress_from_stroke, marker="x", color="red")
    # plt.plot(x2, x2 * E_strain_from_stroke + E_strain_from_stroke_b, linestyle="dashed",color="gray")

    if material in WITH_UPPER_YIELD_POINT:
        plt.plot(x2, x2 * E_strain_from_stroke + E_strain_from_stroke_b, linestyle="dashdot", color="gray")
    elif material in POLYMERS:
        plt.plot([0, 0.8*tensile_strain_from_stroke], [0,0.8*E_strain_from_stroke * tensile_strain_from_stroke], linestyle="dashdot", color="gray")
    else:
        plt.plot(x2, (x2 - 0.2) * E_strain_from_stroke + E_strain_from_stroke_b, linestyle="dashdot", color="gray")

    if brokenPoint[0] is not None:
        plt.plot(brokenPoint[0], brokenPoint[1], marker="x", color="blue")

    # plt.title("Norminal Stress - Strain Curve of " + MATERIAL_MAPPER[material] + " (Stroke)")
    plt.xlabel("Strain [%]")
    plt.ylabel("Stress [MPa]")
    plt.ylim([tensile_strength * (-0.1), tensile_strength * 1.2])
    # plt.legend(bbox_to_anchor=(1, 1), loc='upper right')
    plt.grid()
    plt.savefig(path + 'NSSS.pdf')
    # plt.show()


# 真応力歪み線図の描画
def plotTrueSSCurve(df, material):
    path = "./results/" + material + "/"

    x1 = np.log(1 + df["strain [%]"] / 100) * 100
    y1 = df["stress [MPa]"] * (1 + df["strain [%]"] / 100)

    x2 = np.log(1 + df["strain from stroke [%]"] /100) * 100
    y2 = df["stress [MPa]"] * (1 + df["strain from stroke [%]"] / 100)

    # 歪みゲージ
    plt.figure()
    plt.plot(x1,y1, label = "Strain Gauge", color=COLOR)
    # plt.title("True Stress - True Strain Curve of " + MATERIAL_MAPPER[material] + " (Strain Gauge)")
    plt.xlabel("Strain [%]")
    plt.ylabel("Stress [MPa]")
    plt.ylim([max(y1) * (-0.1), max(y1) * 1.2])
    # plt.legend(bbox_to_anchor=(1, 1), loc='upper right')
    plt.grid()
    plt.savefig(path + 'TSSG.pdf')
    # plt.show()

    # ストローク
    plt.figure()
    plt.plot(x2,y2, label = "Stroke", color=COLOR)
    # plt.title("True Stress - True Strain Curve of " + MATERIAL_MAPPER[material] + " (Stroke)")
    plt.xlabel("Strain [%]")
    plt.ylabel("Stress [MPa]")
    plt.ylim([max(y2) * (-0.1), max(y2) * 1.2])
    # plt.legend(bbox_to_anchor=(1, 1), loc='upper right')
    plt.grid()
    plt.savefig(path + 'TSSS.pdf')
    # plt.show()


# 両対数真応力歪み線図の描画
def plotLogTrueSSCurve(df, linePoint, material):
    path = "./results/" + material + "/"

    x1 = np.log(1 + df["strain [%]"] / 100) * 100
    y1 = df["stress [MPa]"] * (1 + df["strain [%]"] / 100)

    x2 = np.log(1 + df["strain from stroke [%]"] /100) * 100
    y2 = df["stress [MPa]"] * (1 + df["strain from stroke [%]"] / 100)

    # 歪みゲージ
    plt.figure()
    plt.plot(x1,y1, label = "Strain Gauge", color=COLOR)
    # plt.title("True Stress - True Strain Curve of " + MATERIAL_MAPPER[material] + " (Strain Gauge)")
    plt.xlabel("Strain [%]")
    plt.xscale('log')
    plt.ylabel("Stress [MPa]")
    plt.yscale('log')
    # plt.legend(bbox_to_anchor=(1, 1), loc='upper right')
    plt.grid()
    plt.savefig(path + 'LTSSG.pdf')
    # plt.show()

    # ストローク
    plt.figure()
    plt.plot(x2,y2, label = "Stroke", color=COLOR)
    plt.plot(linePoint[0],linePoint[1], linestyle = "dashed", color="gray" )
    # plt.title("True Stress - True Strain Curve of " + MATERIAL_MAPPER[material] + " (Stroke)")
    plt.xlabel("Strain [%]")
    plt.xscale('log')
    plt.ylabel("Stress [MPa]")
    plt.yscale('log')
    # plt.legend(bbox_to_anchor=(1, 1), loc='upper right')
    plt.grid()
    plt.savefig(path + 'LTSSS.pdf')
    # plt.show()


# 耐力の取得
# TODO : 降伏の有無で計算条件を変更
def getTensileStrength(df):
    stress = max(df["stress [MPa]"])
    strain = np.average(df[df["stress [MPa]"] == stress]["strain [%]"])
    strain_from_stroke = np.average(df[df["stress [MPa]"] == stress]["strain from stroke [%]"])
    return [stress, strain, strain_from_stroke]


# ヤング率の計算
# TODO : 降伏の有無で計算条件を変更
def getYoungModulesLineByStress(df, tensile_strength, material):

    normianl_stress = df["stress [MPa]"]
    normianl_strain = df["strain [%]"]

    stress_list = []
    strain_list = []
    if material in WITH_UPPER_YIELD_POINT:
        df_tmp = df[:int(len(df) * 0.2)]
        yield_stress = max(df_tmp["stress [MPa]"])
        yield_strain = np.average(df_tmp[df_tmp["stress [MPa]"] ==  yield_stress]["strain [%]"])
        strain_list = [normianl_strain[0], yield_strain]
        stress_list = [normianl_stress[0], yield_stress]

    else:
        for (stress, strain) in zip(normianl_stress, normianl_strain):
            if(stress > 0.04 * tensile_strength):
                stress_list.append(stress)
                strain_list.append(strain)
            if(stress > 0.33 * tensile_strength):
                break
    return calcLine(np.array(strain_list), np.array(stress_list))


# ストロークからのヤング率の算出
# 耐力の算出に使用
def getYoungModulesLineByStressFromStroke(df, tensile_strength, material):

    normianl_stress = df["stress [MPa]"]
    normianl_strain = df["strain from stroke [%]"]

    stress_list = []
    strain_list = []

    if material in WITH_UPPER_YIELD_POINT:
        df_tmp = df[:int(len(df) * 0.2)]
        yield_stress = max(df_tmp["stress [MPa]"])
        yield_strain = np.average(df_tmp[df_tmp["stress [MPa]"] ==  yield_stress]["strain from stroke [%]"])
        strain_list = [normianl_strain[0], yield_strain]
        stress_list = [normianl_stress[0], yield_stress]
    else:
        for (stress, strain) in zip(normianl_stress, normianl_strain):
            if(stress > 0.04 * tensile_strength):
                stress_list.append(stress)
                strain_list.append(strain)
            if(stress > 0.33 * tensile_strength):
                break

    return calcLine(np.array(strain_list), np.array(stress_list))


# 耐力の算出
def getYieldStressByStrain(df, E_list, material):
    x = df["strain [%]"]
    y = df["stress [MPa]"]

    E_strain = E_list[0]
    E_strain_b = E_list[1]

    stress = 0
    strain = 0

    if material in WITH_UPPER_YIELD_POINT:
        df_tmp = df[:int(len(df) * 0.2)]
        stress = max(df_tmp["stress [MPa]"])
        strain = np.average(df_tmp[df_tmp["stress [MPa]"] ==  stress]["strain [%]"])

    elif material in POLYMERS:
        stress = max(df["stress [MPa]"])
        strain = np.average(df[df["stress [MPa]"] ==  stress]["strain [%]"])

    else:
        df["tmp"] = abs(y - yieldStressLine(x, E_strain, E_strain_b))
        tmp = df[df["tmp"] == min(df["tmp"])]
        strain = np.average(tmp["strain [%]"])
        stress = np.average(tmp["stress [MPa]"])

    return [stress, strain]


def getYieldStressByStrainFromStroke(df, E_list, material):
    x = df["strain from stroke [%]"]
    y = df["stress [MPa]"]

    E_strain = E_list[0]
    E_strain_b = E_list[1]

    if material in WITH_UPPER_YIELD_POINT:
        df_tmp = df[:int(len(df) * 0.12)]
        stress = max(df_tmp["stress [MPa]"])
        strain = np.average(df_tmp[df_tmp["stress [MPa]"] ==  stress]["strain from stroke [%]"])

    elif material in POLYMERS:
        stress = max(df["stress [MPa]"])
        strain = np.average(df[df["stress [MPa]"] ==  stress]["strain from stroke [%]"])

    else:
        df["tmp"] = abs(y - yieldStressLine(x, E_strain, E_strain_b))
        tmp = df[df["tmp"] == min(df["tmp"])]
        strain = np.average(tmp["strain from stroke [%]"])
        stress = np.average(tmp["stress [MPa]"])

    return [stress, strain]


def yieldStressLine(x, a,b):
    return a * (x - 0.2) + b


def calcLine(x,y):
    a, b= np.polyfit(x, y, 1)
    return a, b


def getBrokenPoint(df, tensile_strength, material):
    df_tmp = df[int(len(df)*0.5):]
    stress_list = df_tmp["stress [MPa]"]
    strain_list = df_tmp["strain from stroke [%]"]

    stress_pre = stress_list[0]
    strain_pre = strain_list[0]
    if(material in ["Ti", "Mg", "Fe_water", "Fe_ro"]):
        stress_ratio = tensile_strength * 0.005
        strain_ratio = 0.1
        for (stress, strain) in zip(stress_list, strain_list):
            stress_diff = stress - stress_pre
            strain_diff = strain - strain_pre
            if( (stress_diff < - stress_ratio) and (abs(strain_diff) < strain_ratio)):
                return [strain, stress]
            stress_pre = stress
            strain_pre = strain
    elif material in ["Al"]:
        stress_ratio = tensile_strength * 0.004
        strain_ratio = 0.3
        cnt = 0
        for (stress, strain) in zip(stress_list, strain_list):
            stress_diff = stress - stress_pre
            strain_diff = strain - strain_pre
            if( (stress_diff < - stress_ratio) and (abs(strain_diff) < strain_ratio)):
                cnt += 1
            else:
                cnt = 0
            if(cnt > 3):
                return [strain, stress]
            stress_pre = stress
            strain_pre = strain
    elif material in ["PET"]:
        stress_ratio = tensile_strength * 0.00412
        strain_ratio = 2.0
        cnt = 0
        for (stress, strain) in zip(stress_list, strain_list):
            stress_diff = stress - stress_pre
            strain_diff = strain - strain_pre
            if( (stress_diff < - stress_ratio) and (abs(strain_diff) < strain_ratio)):
                cnt += 1
            else:
                cnt = 0
            if(cnt > 2):
                return [strain, stress]
            stress_pre = stress
            strain_pre = strain

    else:
        return [None, None]

    return [None, None]


def printValues(material, tensile_strength, E_list, Y_list, broken_strain, wh_index):
    E_strain = E_list[0][0] / 10
    Y_stress = Y_list[0][0]

    _E_strain_from_stroke = E_list[1][0] / 10
    Y_stress_from_stroke = Y_list[1][0]
    print("")
    print("--------------------")
    print(MATERIAL_MAPPER[material])

    print("降伏応力（ゲージ）[MPa] :\t%.2f" % Y_stress)
    print("降伏応力（ストローク）[MPa] :\t%.2f" % Y_stress_from_stroke)

    print("引張応力[MPa] :\t\t\t%.2f" % tensile_strength)
    print("ヤング率[GPa] :\t\t\t%.2f" % (E_strain / 10))
    print("破断伸び[%%] :\t\t\t%.2f" % broken_strain)
    print("加工硬化指数[-] :\t\t%.3f" % wh_index)
    print("--------------------")
    print("")

def wirteValues(material, tensile_strength, E_list, Y_list, broken_strain, wh_index):
    E_strain = E_list[0][0] / 10
    Y_stress = Y_list[0][0]

    _E_strain_from_stroke = E_list[1][0] / 10
    Y_stress_from_stroke = Y_list[1][0]

    filename = "./results/" + material + "/info.csv"
    file = open(filename, 'w')
    file.write("," + MATERIAL_MAPPER[material] + "\n")
    file.write("降伏応力（ゲージ）[MPa],%.2f" % Y_stress + "\n")
    file.write("降伏応力（ストローク）[MPa],%.2f" % Y_stress_from_stroke+"\n")

    file.write("引張応力[MPa],%.2f" % tensile_strength + "\n")
    file.write("ヤング率[GPa],%.2f" % E_strain + "\n")
    file.write("破断伸び[%%],%.2f" % broken_strain + "\n")
    file.write("加工硬化指数[-],%.3f" % wh_index + "\n")
    file.close()


def convertPointToStrain(brokenPoint, E_strain):
    if(brokenPoint[0] is None):
        return 0
    strain = brokenPoint[0]
    stress = brokenPoint[1]
    strain_diff = stress / E_strain
    return strain - strain_diff


def getWHindex(df, material, yield_strain, tensile_strain):
    strain_offset = (tensile_strain - yield_strain) * 0.1
    if material == "Al":
        measurement_range = [yield_strain + strain_offset, tensile_strain - strain_offset]
    elif material == "Fe_ro":
        measurement_range = [yield_strain + 2 * strain_offset, tensile_strain - strain_offset]
    elif material == "Fe_water":
        measurement_range = [yield_strain + strain_offset, tensile_strain - strain_offset]
    elif material == "Mg":
        measurement_range = [yield_strain + strain_offset, tensile_strain - strain_offset]
    elif material == "PET":
        measurement_range = [9, 10.22]
    elif material == "Ti":
        measurement_range = [yield_strain + strain_offset, tensile_strain - strain_offset]
    else:
        return None

    stress_list = df["stress [MPa]"] * (1 + df["strain from stroke [%]"] / 100)
    strain_list = np.log(1 + df["strain from stroke [%]"] /100) * 100
    stress_line = []
    strain_line = []

    for (stress, strain) in zip(stress_list, strain_list):
        if(strain > min(measurement_range)):
            stress_line.append(stress)
            strain_line.append(strain)
            if(strain > max(measurement_range)):
                break
        else:
            pass

    stress_line = np.log10(stress_line)
    strain_line = np.log10(strain_line)

    n, b = calcLine(strain_line, stress_line)

    linePoint = [np.power(10, [strain_line[0], strain_line[len(strain_line)-1]]), np.power(10, [n*strain_line[0] + b, n*strain_line[len(strain_line) -1] + b])]


    return [n, linePoint]



def executeMeasurement(material):
    df = readCsv(material)
    area = getArea(material)
    strain_ratio = getCalibrationValue(df)

    df = getStartPoint(df)
    df = convertValues(df, area, strain_ratio)

    tensile_list = getTensileStrength(df)
    tensile_strength = tensile_list[0]
    tensile_strain_from_stroke = tensile_list[2]

    E_strain, E_strain_b = getYoungModulesLineByStress(df, tensile_strength, material)
    E_strain_from_stroke, E_strain_from_stroke_b = getYoungModulesLineByStressFromStroke(df, tensile_strength, material)
    E_list = [[E_strain, E_strain_b], [E_strain_from_stroke, E_strain_from_stroke_b]]

    yield_stress, yield_strain = getYieldStressByStrain(df, E_list[0], material)
    yield_stress_from_stroke, yield_strain_from_stroke = getYieldStressByStrainFromStroke(df, E_list[1], material)
    Y_list =[[yield_stress, yield_strain], [yield_stress_from_stroke, yield_strain_from_stroke]]

    brokenPoint = getBrokenPoint(df, tensile_strength, material)
    broken_strain = convertPointToStrain(brokenPoint, E_strain)

    wh_index, linePoint = getWHindex(df, material, yield_strain_from_stroke, tensile_strain_from_stroke)

    plotNorminalSSCurve(df, tensile_list, E_list, Y_list, brokenPoint, material)
    plt.close()
    plotTrueSSCurve(df, material)
    plt.close()
    plotLogTrueSSCurve(df, linePoint, material)
    plt.close()


    # plt.show()

    # printValues(material, tensile_strength, E_list, Y_list, broken_strain, wh_index)
    wirteValues(material, tensile_strength, E_list, Y_list, broken_strain, wh_index)

if __name__ == "__main__":
    materials = ["Al", "Fe_ro", "Fe_water", "Mg", "PET", "Ti"]
    for material in materials:
        executeMeasurement(material)
    # executeMeasurement("Fe_ro")
    # plt.show()