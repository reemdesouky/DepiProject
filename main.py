import pandas as pd

from model import model
from data_transformation import DataTransformer
transformer = DataTransformer()

data = pd.read_csv("D:\\old dataset\\train.csv")
data=transformer.transform(data)
# mae, mse = model(data)
# print(f"MAE: {mae}, MSE: {mse}")


print(data.columns)

