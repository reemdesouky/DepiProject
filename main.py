import pandas as pd
from model import model
data = pd.read_csv("D:\\old dataset\\train.csv")

mae, mse = model(data)

print(f"MAE: {mae}, MSE: {mse}")
