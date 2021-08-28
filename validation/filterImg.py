import os
import shutil

import pandas as pd

fname = pd.read_csv('../validation/figurename.csv')
filePath = '../validation'
for file in os.listdir(filePath):
    for name in fname['name']:
        if file == name:
            shutil.move(os.path.join(filePath, file), os.path.join('synthetic_json', file))
