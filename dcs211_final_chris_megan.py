import pandas as pd
import matplotlib.pyplot as plt
from prettytable import PrettyTable
import requests
import json
import plotly.express as px
import folium
from branca.colormap import linear


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
data = data[data["HPROBCOUNT"] != -1]
data = data[data["RODENTS_UNIT"] != -3]
data = data[data["UNIT_RATING"] != -1]

# boro to names: 1 = Bronx, 2 = Brooklyn, 3 = Manhattan, 4 = Queens, 5 = Staten Island
# Note: fix the spelling of "Brookyln" to "Brooklyn" here.
data["BORO"] = data["BORO"].replace({1: "Bronx", 2: "Brooklyn", 3: "Manhattan", 4: "Queens", 5: "Staten Island"})

# race to words: 1 = white, 2 = black, 3 = native american, 4 = asian, 5 = pacific islander, 6 = two or more races
data["RACE_P"] = data["RACE_P"].replace({1: "White", 2: "Black", 3: "Native American", 4: "Asian", 5: "Pacific Islander", 6: "Two+ races"})

# gender to words: 1 = male, 2 = female, 3 = other 
data["GENDER_P"] = data["GENDER_P"].replace({1: "Male", 2: "Female", 3: "Other"})

# pet presence to 0-1: 1(Yes) = 1, 2(No) = 0 
data["ANIMS"] = data["ANIMS"].replace({2: 0})

# rodent prescence to 0-1: 1(Yes) = 1, 2(No) = 0
data["RODENTS_UNIT"] = data["RODENTS_UNIT"].replace({2: 0})

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

# apartment problems, rodents, and rating by borough 
borough_other = ( 
    data.groupby('BORO')
    .agg(
        mean_probs=('HPROBCOUNT', 'mean'),
        mean_rodents=('RODENTS_UNIT', 'mean'),
        mean_rating=('UNIT_RATING', 'mean')
    )
    .sort_values(by='mean_rating', ascending=False)
)

table_five = PrettyTable()
table_five.field_names = ["Borough", "# Problems (mean)", "Rodent Presence (mean)", "Apartment Rating (mean)"]
for BORO, row in borough_other.iterrows(): 
    table_five.add_row([
        BORO,
        f"{row['mean_probs']:.2f}",
        f"{row['mean_rodents']:.2f}",
        f"{row['mean_rating']:.2f}"
    ])

print(table_five)

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
plt.savefig("income_vs_rent.png", bbox_inches="tight")  # save scatterplot
plt.show()

# correlation between rent and utility cost (summer)?  
plt.scatter(data["RENT_AMOUNT"], data["UTILCOSTS_SUMMER"])
plt.xlabel("Monthly Rent (USD)")
plt.ylabel("Summer Utility Cost (USD)")
plt.title("Monthly Rent vs Utility Costs")
plt.savefig("rent_vs_util_summer.png", bbox_inches="tight")  # save scatterplot
plt.show()

# correlation between age and rent? 
plt.scatter(data["AGE_REC_P"], data["RENT_AMOUNT"])
plt.xlabel("Age")
plt.ylabel("Monthly Rent (USD)")
plt.title("Age vs Monthly Rent")
plt.savefig("age_vs_rent.png", bbox_inches="tight")  # save scatterplot
plt.show()

# histograms to show borough characteristics 
# pet ownership by borough  
group = data.groupby("BORO")["ANIMS"].mean()
group.plot(kind="bar")

plt.xlabel("Borough")
plt.ylabel("Pet Presence")
plt.title("Pet Presence by Borough")
plt.savefig("pet_by_borough.png", bbox_inches="tight")  # save figure for dashboard
plt.show()
 
# rent by borough 
group = data.groupby("BORO")["RENT_AMOUNT"].mean()
group.plot(kind="bar")

plt.xlabel("Borough")
plt.ylabel("Monthly Rent (USD)")
plt.title("Average Rent by Borough")
plt.savefig("rent_by_borough.png", bbox_inches="tight")  # save figure for dashboard
plt.show()

# summer util by borough 
group = data.groupby("BORO")["UTILCOSTS_SUMMER"].mean()
group.plot(kind="bar")

plt.xlabel("Borough")
plt.ylabel("Summer Utility Costs (USD)")
plt.title("Summer Utility Costs by Borough")
plt.savefig("summer_util_by_borough.png", bbox_inches="tight")  # optional save
plt.show()

# winter util by borough 
group = data.groupby("BORO")["UTILCOSTS_WINTER"].mean()
group.plot(kind="bar")

plt.xlabel("Borough")
plt.ylabel("Winter Utility Costs (USD)")
plt.title("Winter Utility Costs by Borough")
plt.savefig("winter_util_by_borough.png", bbox_inches="tight")  # optional save
plt.show()

# lease length by borough 
group = data.groupby("BORO")["LEASE_LENGTH"].mean()
group.plot(kind="bar")

plt.xlabel("Borough")
plt.ylabel("Lease Length")
plt.title("Lease Length by Borough")
plt.savefig("lease_length_by_borough.png", bbox_inches="tight")  # optional save
plt.show()

# age by borough 
group = data.groupby("BORO")["AGE_REC_P"].mean()
group.plot(kind="bar")

plt.xlabel("Borough")
plt.ylabel("Main Resident Age")
plt.title("Main Resident Age by Borough")
plt.savefig("age_by_borough.png", bbox_inches="tight")  # optional save
plt.show()

# household income by borough 
group = data.groupby("BORO")["HHINC_REC1"].mean()
group.plot(kind="bar")

plt.xlabel("Borough")
plt.ylabel("Household Income (USD)")
plt.title("Household Income by Borough")
plt.savefig("income_by_borough.png", bbox_inches="tight")  # save figure for dashboard
plt.show()

# histograms to show gender characteristics 
# pet ownership by gender  
group = data.groupby("GENDER_P")["ANIMS"].mean()
group.plot(kind="bar")

plt.xlabel("Gender")
plt.ylabel("Pet Presence")
plt.title("Pet Presence by Gender")
plt.savefig("pet_by_gender.png", bbox_inches="tight")  # optional save
plt.show()
 
# rent by gender 
group = data.groupby("GENDER_P")["RENT_AMOUNT"].mean()
group.plot(kind="bar")

plt.xlabel("Gender")
plt.ylabel("Monthly Rent (USD)")
plt.title("Average Rent by Gender")
plt.savefig("rent_by_gender.png", bbox_inches="tight")  # optional save
plt.show()

# summer util by gender 
group = data.groupby("GENDER_P")["UTILCOSTS_SUMMER"].mean()
group.plot(kind="bar")

plt.xlabel("Gender")
plt.ylabel("Summer Utility Costs (USD)")
plt.title("Summer Utility Costs by Gender")
plt.savefig("summer_util_by_gender.png", bbox_inches="tight")  # optional save
plt.show()

# winter util by gender 
group = data.groupby("GENDER_P")["UTILCOSTS_WINTER"].mean()
group.plot(kind="bar")

plt.xlabel("Gender")
plt.ylabel("Winter Utility Costs (USD)")
plt.title("Winter Utility Costs by Gender")
plt.savefig("winter_util_by_gender.png", bbox_inches="tight")  # optional save
plt.show()

# lease length by gender
group = data.groupby("GENDER_P")["LEASE_LENGTH"].mean()
group.plot(kind="bar")

plt.xlabel("Gender")
plt.ylabel("Lease Length")
plt.title("Lease Length by Gender")
plt.savefig("lease_length_by_gender.png", bbox_inches="tight")  # optional save
plt.show()

# age by gender 
group = data.groupby("GENDER_P")["AGE_REC_P"].mean()
group.plot(kind="bar")

plt.xlabel("Gender")
plt.ylabel("Main Resident Age")
plt.title("Main Resident Age by Gender")
plt.savefig("age_by_gender.png", bbox_inches="tight")  # optional save
plt.show()

# household income by gender 
group = data.groupby("GENDER_P")["HHINC_REC1"].mean()
group.plot(kind="bar")

plt.xlabel("Gender")
plt.ylabel("Household Income (USD)")
plt.title("Household Income by Gender")
plt.savefig("income_by_gender.png", bbox_inches="tight")  # optional save
plt.show()

# histrograms to show race characteristics 
# pet ownership by race  
group = data.groupby("RACE_P")["ANIMS"].mean()
group.plot(kind="bar")

plt.xlabel("Race")
plt.ylabel("Pet Presence")
plt.title("Pet Presence by Race")
plt.savefig("pet_by_race.png", bbox_inches="tight")  # optional save
plt.show()
 
# rent by race 
group = data.groupby("RACE_P")["RENT_AMOUNT"].mean()
group.plot(kind="bar")

plt.xlabel("Race")
plt.ylabel("Monthly Rent (USD)")
plt.title("Average Rent by Race")
plt.savefig("rent_by_race.png", bbox_inches="tight")  # optional save
plt.show()

# summer util by race 
group = data.groupby("RACE_P")["UTILCOSTS_SUMMER"].mean()
group.plot(kind="bar")

plt.xlabel("Race")
plt.ylabel("Summer Utility Costs (USD)")
plt.title("Summer Utility Costs by Race")
plt.savefig("summer_util_by_race.png", bbox_inches="tight")  # optional save
plt.show()

# winter util by race 
group = data.groupby("RACE_P")["UTILCOSTS_WINTER"].mean()
group.plot(kind="bar")

plt.xlabel("Race")
plt.ylabel("Winter Utility Costs (USD)")
plt.title("Winter Utility Costs by Race")
plt.savefig("winter_util_by_race.png", bbox_inches="tight")  # optional save
plt.show()

# lease length by race
group = data.groupby("RACE_P")["LEASE_LENGTH"].mean()
group.plot(kind="bar")

plt.xlabel("Race")
plt.ylabel("Lease Length")
plt.title("Lease Length by Race")
plt.savefig("lease_length_by_race.png", bbox_inches="tight")  # optional save
plt.show()

# age by race
group = data.groupby("RACE_P")["AGE_REC_P"].mean()
group.plot(kind="bar")

plt.xlabel("Race")
plt.ylabel("Main Resident Age")
plt.title("Main Resident Age by Race")
plt.savefig("age_by_race.png", bbox_inches="tight")  # optional save
plt.show()

# household income by race 
group = data.groupby("RACE_P")["HHINC_REC1"].mean()
group.plot(kind="bar")

plt.xlabel("Race")
plt.ylabel("Household Income (USD)")
plt.title("Household Income by Race")
plt.savefig("income_by_race.png", bbox_inches="tight")  # optional save
plt.show()

# Combined utilities chart across boroughs for dashboard
winter_avg = data.groupby('BORO')["UTILCOSTS_WINTER"].mean()
summer_avg = data.groupby('BORO')["UTILCOSTS_SUMMER"].mean()
util_df = pd.DataFrame({'Winter': winter_avg, 'Summer': summer_avg})
util_df.plot(kind='bar')
plt.xlabel('Borough')
plt.ylabel('Utility Costs (USD)')
plt.title('Utility Costs by Borough')
plt.savefig('utilities_by_borough.png', bbox_inches='tight')
plt.show()

#Dashboard 

# Prepare data for dashboard JSON
borough_stats_reset = borough_stats.reset_index().copy()
borough_stats_reset["BORO"] = borough_stats_reset["BORO"].replace({"Brookyln": "Brooklyn"})

dashboard_stats = {}
for _, row in borough_stats_reset.iterrows():
    boro = row["BORO"]
    dashboard_stats[boro] = {
        "mean_rent": float(row["mean_rent"]),
        "mean_pets": float(row["mean_pets"]),
        "mean_utilwinter": float(row["mean_utilwinter"]),
        "mean_utilsummer": float(row["mean_utilsummer"]),
    }

with open("dashboard_stats.json", "w") as f:
    json.dump(dashboard_stats, f, indent=4)

print("\nDashboard statistics saved to dashboard_stats.json. Use this file in your HTML dashboard.")

# Create and save Plotly choropleth map
geojson_url = "https://data.cityofnewyork.us/api/geospatial/gthc-hcne?method=export&format=GeoJSON"
nyc_geo = requests.get(geojson_url).json()

fig = px.choropleth(
    borough_stats_reset,
    geojson=nyc_geo,
    locations="BORO",
    color="mean_rent",
    featureidkey="properties.boroname",
    hover_data={
        "mean_rent": ":.2f",
        "mean_pets": ":.2f",
        "mean_utilwinter": ":.2f",
        "mean_utilsummer": ":.2f",
    },
    color_continuous_scale="YlOrRd",
)
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(
    title="Average Rent by NYC Borough",
    margin={"r": 0, "t": 50, "l": 0, "b": 0},
)
fig.write_html("nyc_borough_choropleth.html")
print("Plotly choropleth saved to nyc_borough_choropleth.html")

# Create and save Folium interactive map
borough_stats_reset.set_index("BORO", inplace=True)
colormap = linear.YlOrRd_09.scale(
    borough_stats_reset["mean_rent"].min(),
    borough_stats_reset["mean_rent"].max(),
)
colormap.caption = "Average Monthly Rent ($)"

for feature in nyc_geo["features"]:
    name = feature["properties"]["boroname"]
    if name in borough_stats_reset.index:
        stats = borough_stats_reset.loc[name]
        feature["properties"].update({
            "Mean Rent": f"{stats['mean_rent']:.2f}",
            "Avg Pets": f"{stats['mean_pets']:.2f}",
            "Winter Util": f"{stats['mean_utilwinter']:.2f}",
            "Summer Util": f"{stats['mean_utilsummer']:.2f}",
        })

def style_function(feature):
    boro_name = feature["properties"]["boroname"]
    rent_value = borough_stats_reset.loc[boro_name, "mean_rent"] if boro_name in borough_stats_reset.index else None
    return {
        "fillColor": colormap(rent_value) if rent_value is not None else "transparent",
        "color": "black",
        "weight": 1,
        "fillOpacity": 0.7,
    }

tooltip = folium.GeoJsonTooltip(
    fields=["boroname", "Mean Rent", "Avg Pets", "Winter Util", "Summer Util"],
    aliases=["Borough:", "Mean Rent ($):", "Avg. Pets:", "Winter Util ($):", "Summer Util ($):"],
    localize=True,
    sticky=False,
    labels=True,
)

m = folium.Map(location=[40.7128, -74.0060], zoom_start=11, tiles="cartodbpositron")
folium.GeoJson(
    nyc_geo,
    name="Rent by Borough",
    style_function=style_function,
    tooltip=tooltip,
).add_to(m)
m.add_child(colormap)
m.save("nyc_borough_folium.html")
print("Folium map saved to nyc_borough_folium.html")
