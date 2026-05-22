import pandas as pd
from model import model
from data_prepare import prepare_data
# data = pd.read_csv("D:\\old dataset\\train.csv")
data = prepare_data('path')  
mae, mse = model(data)

print(f"MAE: {mae}, MSE: {mse}")
