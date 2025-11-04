import pandas as pd

file_name = "data/nucor.csv"

# Read the CSV, specifying the semicolon separator
df = pd.read_csv(file_name, sep=';')


print(df.head())