import pandas as pd
import matplotlib.pyplot as plt
from prettytable import PrettyTable
import requests

# save occupied nychvs data as pandas data frame 
occupied_data = pd.read_csv("dcs_occupied_puf_23.csv", engine='python', thousands=',')

# save all units nychvs data as pandas data frame 
allunits_data = pd.read_csv("allunits_puf_23.csv", engine='python', thousands=',')

# save person nychvs data as pandas data frame 
person_data = pd.read_csv("dcs_person_puf_23.csv", engine='python', thousands=',')

# merge first two data frames  
occupied_allunits = pd.merge(occupied_data, allunits_data, on='CONTROL', how='inner')

# merge third for complete data frame for analysis
data = pd.merge(occupied_allunits, person_data, on='CONTROL', how='inner')

# inspect data frame 
print(data.head())
print(data.head(10))
print(data.tail())
print(data.tail(10))
print(data.columns)
print(data.info())
print(data.shape)

# dropping observations with missing values (in variables of interest) from data
data = data[data["RENT_AMOUNT"] != -2]
data = data[data["UTILCOSTS_SUMMER"] != -2]
data = data[data["UTILCOSTS_SUMMER"] != -3]
data = data[data["UTILCOSTS_WINTER"] != -2]
data = data[data["UTILCOSTS_WINTER"] != -3]
data = data[data["ANIMS"] != -1]
data = data[data["LEASE_LENGTH"] != -2]
data = data[data["LEASE_LENGTH"] != -1]
data = data[data["GRENT"] != -2]
data = data[data["GRENT"] != -3]
data = data[data["GRENT"] != -1]

# boro to names: 1 = Bronx, 2 = Brooklyn, 3 = Manhattan, 4 = Queens, 5 = Staten Island
data["BORO"] = data["BORO"].replace({1: "Bronx", 2: "Brookyln", 3: "Manhattan", 4: "Queens", 5: "Staten Island"})

# race to words: 1 = white, 2 = black, 3 = native american, 4 = asian, 5 = pacific islander, 6 = two or more races
data["RACE_P"] = data["RACE_P"].replace({1: "White", 2: "Black", 3: "Native American", 4: "Asian", 5: "Pacific Islander", 6: "Two+ races"})

# gender to words: 1 = male, 2 = female, 3 = other 
data["GENDER_P"] = data["GENDER_P"].replace({1: "Male", 2: "Female", 3: "Other"})

# rank boroughs on price of rent, number of pets, cost of utilities
borough_stats = ( 
    data.groupby('BORO')
    .agg(
        mean_rent=('RENT_AMOUNT', 'mean'),
        mean_pets=('ANIMS', 'mean'), 
        mean_utilwinter=('UTILCOSTS_WINTER', 'mean'),
        mean_utilsummer=('UTILCOSTS_SUMMER', 'mean')
    )
    .sort_values(by='mean_rent', ascending=False)
)

table_one = PrettyTable()
table_one.field_names = ["Borough", "Rent ($ mean)", "Pets (mean)", "Winter Util. ($ mean)", "Summer Util. ($ mean)"]
for BORO, row in borough_stats.iterrows(): 
    table_one.add_row([
        BORO,
        f"{row['mean_rent']:.2f}",
        f"{row['mean_pets']:.2f}",
        f"{row['mean_utilwinter']:.2f}",
        f"{row['mean_utilsummer']:.2f}"
    ])

print(table_one) 

# demographics of boroughs: age, income 
borough_demos = ( 
    data.groupby('BORO')
    .agg(
        mean_age=('AGE_REC_P', 'mean'),
        mean_income=('HHINC_REC1', 'mean')
    )
    .sort_values(by='mean_income', ascending=False)
)

table_two = PrettyTable()
table_two.field_names = ["Borough", "Income ($ mean)", "Age (mean)"]
for BORO, row in borough_demos.iterrows(): 
    table_two.add_row([
        BORO,
        f"{row['mean_income']:.2f}",
        f"{row['mean_age']:.2f}"
    ])

print(table_two) 

# gender by borough  
gender_count = (data.groupby(["BORO", "GENDER_P"]).size().reset_index(name="count")) # gender count per borough
gender_count["total"] = gender_count.groupby("BORO")["count"].transform("sum") # sum of gender count per borough 
gender_count["fraction"] = gender_count["count"] / gender_count["total"] # fraction of specific counts over total 

table_gender = gender_count.pivot(index="BORO", columns="GENDER_P", values="fraction") # raw table 
table_three = PrettyTable() # making pretty table 
table_three.field_names = ["Borough"] + list(table_gender.columns)
for BORO, row in table_gender.iterrows():
    table_three.add_row([BORO] + [f"{v:.2f}" for v in row]) # list fraction for each value to second decimal 

print(table_three)

# race by borough 
race_count = (data.groupby(["BORO", "RACE_P"]).size().reset_index(name="count")) # race count per borough
race_count["total"] = race_count.groupby("BORO")["count"].transform("sum") # sum of race count per borough 
race_count["fraction"] = race_count["count"] / race_count["total"] # fraction of specific counts over total 

table_race = race_count.pivot(index="BORO", columns="RACE_P", values="fraction") # raw table 
table_four = PrettyTable() # making pretty table 
table_four.field_names = ["Borough"] + list(table_race.columns)
for BORO, row in table_race.iterrows():
    table_four.add_row([BORO] + [f"{v:.2f}" for v in row]) # list fraction for each value to second decimal 

print(table_four)

# scatterplots of empirical 
# correlation between income and rent? 
plt.scatter(data["HHINC_REC1"], data["RENT_AMOUNT"])
plt.xlabel("Household Income (USD)")
plt.ylabel("Monthly Rent (USD)")
plt.title("Household Income vs Monthly Rent")
plt.show()

# correlation between rent and utility cost (summer)?  
plt.scatter(data["RENT_AMOUNT"], data["UTILCOSTS_SUMMER"])
plt.xlabel("Monthly Rent (USD)")
plt.ylabel("Summer Utility Cost (USD)")
plt.title("Monthly Rent vs Utility Costs")
plt.show()

# correlation between age and rent? 
plt.scatter(data["AGE_REC_P"], data["RENT_AMOUNT"])
plt.xlabel("Age")
plt.ylabel("Monthly Rent (USD)")
plt.title("Age vs Monthly Rent")
plt.show()


# histograms to show borough characteristics 
# pet ownership by borough  
group = data.groupby("BORO")["ANIMS"].mean()
group.plot(kind="bar")

plt.xlabel("Borough")
plt.ylabel("Pet Presence")
plt.title("Pet Presence by Borough")
plt.show()
 
# rent by borough 
group = data.groupby("BORO")["RENT_AMOUNT"].mean()
group.plot(kind="bar")

plt.xlabel("Borough")
plt.ylabel("Monthly Rent (USD)")
plt.title("Average Rent by Borough")
plt.show()

# summer util by borough 
group = data.groupby("BORO")["UTILCOSTS_SUMMER"].mean()
group.plot(kind="bar")

plt.xlabel("Borough")
plt.ylabel("Summer Utility Costs (USD)")
plt.title("Summer Utility Costs by Borough")
plt.show()

# winter util by borough 
group = data.groupby("BORO")["UTILCOSTS_WINTER"].mean()
group.plot(kind="bar")

plt.xlabel("Borough")
plt.ylabel("Winter Utility Costs (USD)")
plt.title("Winter Utility Costs by Borough")
plt.show()

# lease length by borough 
# correlations between borough and pet ownership? 
group = data.groupby("BORO")["LEASE_LENGTH"].mean()
group.plot(kind="bar")

plt.xlabel("Borough")
plt.ylabel("Lease Length")
plt.title("Lease Length by Borough")
plt.show()

# age by borough 
# correlations between borough and pet ownership? 
group = data.groupby("BORO")["AGE_REC_P"].mean()
group.plot(kind="bar")

plt.xlabel("Borough")
plt.ylabel("Main Resident Age")
plt.title("Main Resident Age by Borough")
plt.show()

# household income by borough 
# correlations between borough and pet ownership? 
group = data.groupby("BORO")["HHINC_REC1"].mean()
group.plot(kind="bar")

plt.xlabel("Borough")
plt.ylabel("Household Income (USD)")
plt.title("Household Income by Borough")
plt.show()


