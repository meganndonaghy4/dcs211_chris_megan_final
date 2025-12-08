import pandas as pd
import matplotlib.pyplot as plt
from prettytable import PrettyTable
import requests

# save nychvs data as pandas data frame 
rawdata = pd.read_csv("allunits_puf_23.csv", engine='python', thousands=',')

# inspect data frame 
print(rawdata.head())
print(rawdata.head(10))
print(rawdata.tail())
print(rawdata.tail(10))
print(rawdata.columns)
print(rawdata.info())
print(rawdata.shape)


