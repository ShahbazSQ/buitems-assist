import pandas as pd

# Load raw CSV without headers
df = pd.read_csv("timetable.csv", header=None)

# Find the header row
header_index = df[df.iloc[:, 0] == "Sr.NO"].index[0]

# Extract the clean data
df_clean = df.iloc[header_index:].reset_index(drop=True)
df_clean.columns = df_clean.iloc[0]  # Set first row as header
df_clean = df_clean[1:]  # Drop header row

# Remove fully empty columns
df_clean = df_clean.dropna(axis=1, how='all')

# Clean whitespace and case
df_clean.columns = df_clean.columns.str.strip().str.capitalize()
df_clean = df_clean.applymap(lambda x: x.strip().capitalize() if isinstance(x, str) else x)

# Save cleaned version
df_clean.to_csv("timetable_cleaned.csv", index=False)
print("✅ Saved as 'timetable_cleaned.csv'")
