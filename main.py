import pandas as pd
import json,os


def read_excel(name):
    data = pd.read_excel(name)
    jsonData = []
    for i, row in data.iterrows():
        jsonData.append({"ID": row["Numbering"], "arabicName": row["Sign"], "type": row["TYPE"], "englishName": row["SIGN IN ENGLISH"], "folderName": row["PROPOSED DIRECTORY NAMING 1"]})
        if not os.path.exists("RGB/" + row["PROPOSED DIRECTORY NAMING 1"]):
            os.makedirs("RGB/" + row["PROPOSED DIRECTORY NAMING 1"])

    with open("signsNames.json", 'w') as file:
        json.dump(jsonData, file)
if __name__ == '__main__':
    read_excel('classes.xlsx')
