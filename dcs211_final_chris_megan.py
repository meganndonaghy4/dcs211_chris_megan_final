import pandas as pd
import matplotlib.pyplot as plt
from prettytable import PrettyTable
import requests
import json
import plotly.express as px
import folium
from branca.colormap import linear


occupied_data = pd.read_csv("dcs_occupied_puf_23.csv", engine='python', thousands=',')
allunits_data = pd.read_csv("allunits_puf_23.csv", engine='python', thousands=',')
person_data = pd.read_csv("dcs_person_puf_23.csv", engine='python', thousands=',')

occupied_allunits = pd.merge(occupied_data, allunits_data, on='CONTROL', how='inner')
data = pd.merge(occupied_allunits, person_data, on='CONTROL', how='inner')

# Inspect data
print(data.head())
print(data.head(10))
print(data.tail())
print(data.tail(10))
print(data.columns)
print(data.info())
print(data.shape)

# Drop invalid values
data = data[data["RENT_AMOUNT"] != -2]
data = data[data["UTILCOSTS_SUMMER"].isin([-2, -3]) == False]
data = data[data["UTILCOSTS_WINTER"].isin([-2, -3]) == False]
data = data[data["ANIMS"] != -1]
data = data[data["LEASE_LENGTH"].isin([-2, -1]) == False]
data = data[data["GRENT"].isin([-2, -3, -1]) == False]

# Map codes to names (typo corrected here)
data["BORO"] = data["BORO"].replace({
    1: "Bronx",
    2: "Brooklyn",  # corrected spelling
    3: "Manhattan",
    4: "Queens",
    5: "Staten Island"
})
data["RACE_P"] = data["RACE_P"].replace({1:"White", 2:"Black", 3:"Native American", 4:"Asian", 5:"Pacific Islander", 6:"Two+ races"})
data["GENDER_P"] = data["GENDER_P"].replace({1:"Male", 2:"Female", 3:"Other"})
data["ANIMS"] = data["ANIMS"].replace({2: 0})
data["RODENTS_UNIT"] = data["RODENTS_UNIT"].replace({2: 0})

# Borough stats (mean rent, pets, utilities)
borough_stats = (data.groupby("BORO")
                 .agg(mean_rent=("RENT_AMOUNT","mean"),
                      mean_pets=("ANIMS","mean"),
                      mean_utilwinter=("UTILCOSTS_WINTER","mean"),
                      mean_utilsummer=("UTILCOSTS_SUMMER","mean"))
                 .sort_values(by="mean_rent", ascending=False))

table_one = PrettyTable()
table_one.field_names = ["Borough","Rent ($ mean)","Pets (mean)","Winter Util. ($ mean)","Summer Util. ($ mean)"]
for BORO, row in borough_stats.iterrows():
    table_one.add_row([BORO, f"{row['mean_rent']:.2f}", f"{row['mean_pets']:.2f}", f"{row['mean_utilwinter']:.2f}", f"{row['mean_utilsummer']:.2f}"])
print(table_one)

# Demographics: mean age, mean income
borough_demos = (data.groupby("BORO")
                 .agg(mean_age=("AGE_REC_P","mean"),
                      mean_income=("HHINC_REC1","mean"))
                 .sort_values(by="mean_income", ascending=False))
table_two = PrettyTable()
table_two.field_names = ["Borough","Income ($ mean)","Age (mean)"]
for BORO, row in borough_demos.iterrows():
    table_two.add_row([BORO, f"{row['mean_income']:.2f}", f"{row['mean_age']:.2f}"])
print(table_two)

# Gender distribution
gender_count = (data.groupby(["BORO","GENDER_P"]).size().reset_index(name="count"))
gender_count["total"] = gender_count.groupby("BORO")["count"].transform("sum")
gender_count["fraction"] = gender_count["count"]/gender_count["total"]
table_gender = gender_count.pivot(index="BORO", columns="GENDER_P", values="fraction")
table_three = PrettyTable()
table_three.field_names = ["Borough"] + list(table_gender.columns)
for BORO, row in table_gender.iterrows():
    table_three.add_row([BORO] + [f"{v:.2f}" for v in row])
print(table_three)

# Race distribution
race_count = (data.groupby(["BORO","RACE_P"]).size().reset_index(name="count"))
race_count["total"] = race_count.groupby("BORO")["count"].transform("sum")
race_count["fraction"] = race_count["count"]/race_count["total"]
table_race = race_count.pivot(index="BORO", columns="RACE_P", values="fraction")
table_four = PrettyTable()
table_four.field_names = ["Borough"] + list(table_race.columns)
for BORO, row in table_race.iterrows():
    table_four.add_row([BORO] + [f"{v:.2f}" for v in row])
print(table_four)

# Scatterplots and bar/hist charts (display only)
# House­hold income vs rent
plt.scatter(data["HHINC_REC1"], data["RENT_AMOUNT"])
plt.xlabel("Household Income (USD)")
plt.ylabel("Monthly Rent (USD)")
plt.title("Household Income vs Monthly Rent")
plt.show()

# Rent vs summer utilities
plt.scatter(data["RENT_AMOUNT"], data["UTILCOSTS_SUMMER"])
plt.xlabel("Monthly Rent (USD)")
plt.ylabel("Summer Utility Cost (USD)")
plt.title("Monthly Rent vs Utility Costs")
plt.show()

# Age vs rent
plt.scatter(data["AGE_REC_P"], data["RENT_AMOUNT"])
plt.xlabel("Age")
plt.ylabel("Monthly Rent (USD)")
plt.title("Age vs Monthly Rent")
plt.show()

# Borough histograms (display)
for label, series, ylabel, title in [
    ("BORO", data.groupby("BORO")["ANIMS"].mean(), "Pet Presence", "Pet Presence by Borough"),
    ("BORO", data.groupby("BORO")["RENT_AMOUNT"].mean(), "Monthly Rent (USD)", "Average Rent by Borough"),
    ("BORO", data.groupby("BORO")["UTILCOSTS_SUMMER"].mean(), "Summer Utility Costs (USD)", "Summer Utility Costs by Borough"),
    ("BORO", data.groupby("BORO")["UTILCOSTS_WINTER"].mean(), "Winter Utility Costs (USD)", "Winter Utility Costs by Borough"),
    ("BORO", data.groupby("BORO")["LEASE_LENGTH"].mean(), "Lease Length", "Lease Length by Borough"),
    ("BORO", data.groupby("BORO")["AGE_REC_P"].mean(), "Main Resident Age", "Main Resident Age by Borough"),
    ("BORO", data.groupby("BORO")["HHINC_REC1"].mean(), "Household Income (USD)", "Household Income by Borough"),
]:
    series.plot(kind="bar")
    plt.xlabel(label)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.show()

# Gender histograms
for label, series, ylabel, title in [
    ("Gender", data.groupby("GENDER_P")["ANIMS"].mean(), "Pet Presence", "Pet Presence by Gender"),
    ("Gender", data.groupby("GENDER_P")["RENT_AMOUNT"].mean(), "Monthly Rent (USD)", "Average Rent by Gender"),
    ("Gender", data.groupby("GENDER_P")["UTILCOSTS_SUMMER"].mean(), "Summer Utility Costs (USD)", "Summer Utility Costs by Gender"),
    ("Gender", data.groupby("GENDER_P")["UTILCOSTS_WINTER"].mean(), "Winter Utility Costs (USD)", "Winter Utility Costs by Gender"),
    ("Gender", data.groupby("GENDER_P")["LEASE_LENGTH"].mean(), "Lease Length", "Lease Length by Gender"),
    ("Gender", data.groupby("GENDER_P")["AGE_REC_P"].mean(), "Main Resident Age", "Main Resident Age by Gender"),
    ("Gender", data.groupby("GENDER_P")["HHINC_REC1"].mean(), "Household Income (USD)", "Household Income by Gender"),
]:
    series.plot(kind="bar")
    plt.xlabel(label)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.show()

# Race histograms
for label, series, ylabel, title in [
    ("Race", data.groupby("RACE_P")["ANIMS"].mean(), "Pet Presence", "Pet Presence by Race"),
    ("Race", data.groupby("RACE_P")["RENT_AMOUNT"].mean(), "Monthly Rent (USD)", "Average Rent by Race"),
    ("Race", data.groupby("RACE_P")["UTILCOSTS_SUMMER"].mean(), "Summer Utility Costs (USD)", "Summer Utility Costs by Race"),
    ("Race", data.groupby("RACE_P")["UTILCOSTS_WINTER"].mean(), "Winter Utility Costs (USD)", "Winter Utility Costs by Race"),
    ("Race", data.groupby("RACE_P")["LEASE_LENGTH"].mean(), "Lease Length", "Lease Length by Race"),
    ("Race", data.groupby("RACE_P")["AGE_REC_P"].mean(), "Main Resident Age", "Main Resident Age by Race"),
    ("Race", data.groupby("RACE_P")["HHINC_REC1"].mean(), "Household Income (USD)", "Household Income by Race"),
]:
    series.plot(kind="bar")
    plt.xlabel(label)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.show()

#  Dashboard generation (save charts, compute stats, create maps)

# Function to save bar charts (PNG) for dashboard
def save_bar(series, xlabel, ylabel, title, fname):
    series.plot(kind="bar")
    plt.xlabel(xlabel); plt.ylabel(ylabel); plt.title(title)
    plt.savefig(fname, bbox_inches="tight"); plt.close()

# Save the charts
save_bar(data.groupby("BORO")["ANIMS"].mean(), "Borough","Pet Presence",
         "Pet Presence by Borough","pet_by_borough.png")
save_bar(data.groupby("BORO")["RENT_AMOUNT"].mean(), "Borough","Monthly Rent (USD)",
         "Average Rent by Borough","rent_by_borough.png")
save_bar(data.groupby("BORO")["HHINC_REC1"].mean(),"Borough","Household Income (USD)",
         "Household Income by Borough","income_by_borough.png")
save_bar(data.groupby("BORO")["UTILCOSTS_SUMMER"].mean(),"Borough","Summer Utility Costs (USD)",
         "Summer Utility Costs by Borough","summer_util_by_borough.png")
save_bar(data.groupby("BORO")["UTILCOSTS_WINTER"].mean(),"Borough","Winter Utility Costs (USD)",
         "Winter Utility Costs by Borough","winter_util_by_borough.png")
save_bar(data.groupby("BORO")["LEASE_LENGTH"].mean(),"Borough","Lease Length",
         "Lease Length by Borough","lease_length_by_borough.png")
save_bar(data.groupby("BORO")["AGE_REC_P"].mean(),"Borough","Main Resident Age",
         "Main Resident Age by Borough","age_by_borough.png")

# Extended stats using names
extended_stats = (data.groupby("BORO")
                  .agg(mean_rent=("RENT_AMOUNT","mean"),
                       mean_pets=("ANIMS","mean"),
                       mean_utilwinter=("UTILCOSTS_WINTER","mean"),
                       mean_utilsummer=("UTILCOSTS_SUMMER","mean"),
                       mean_income=("HHINC_REC1","mean"),
                       mean_rating=("UNIT_RATING","mean"),
                       mean_rodents=("RODENTS_UNIT","mean"),
                       mean_probs=("HPROBCOUNT","mean"),
                       mean_lease=("LEASE_LENGTH","mean"),
                       mean_age=("AGE_REC_P","mean"))
                  .reset_index())

# Demographic distributions
gender_count2 = (data.groupby(["BORO","GENDER_P"]).size().reset_index(name="count"))
gender_count2["total"] = gender_count2.groupby("BORO")["count"].transform("sum")
gender_count2["fraction"] = gender_count2["count"]/gender_count2["total"]
gender_dist2 = gender_count2.pivot(index="BORO", columns="GENDER_P", values="fraction")
race_count2 = (data.groupby(["BORO","RACE_P"]).size().reset_index(name="count"))
race_count2["total"] = race_count2.groupby("BORO")["count"].transform("sum")
race_count2["fraction"] = race_count2["count"]/race_count2["total"]
race_dist2 = race_count2.pivot(index="BORO", columns="RACE_P", values="fraction")

# Build stats dictionary
extended_dashboard_stats = {}
for _, row in extended_stats.iterrows():
    b = row["BORO"]
    extended_dashboard_stats[b] = {
        "mean_rent": float(row["mean_rent"]),
        "mean_pets": float(row["mean_pets"]),
        "mean_utilwinter": float(row["mean_utilwinter"]),
        "mean_utilsummer": float(row["mean_utilsummer"]),
        "mean_income": float(row["mean_income"]),
        "mean_rating": float(row["mean_rating"]),
        "mean_rodents": float(row["mean_rodents"]),
        "mean_probs": float(row["mean_probs"]),
        "mean_lease": float(row["mean_lease"]),
        "mean_age": float(row["mean_age"]),
        "gender_distribution": {g: float(gender_dist2.loc[b, g]) for g in gender_dist2.columns},
        "race_distribution": {r: float(race_dist2.loc[b, r]) for r in race_dist2.columns}
    }

# Save stats to JSON and JS
with open("extended_dashboard_stats.json","w") as f:
    json.dump(extended_dashboard_stats, f, indent=4)

with open("stats.js","w") as jsf:
    jsf.write("window.boroughStats = ")
    jsf.write(json.dumps(extended_dashboard_stats, indent=4))
    jsf.write(";\n")

# Load borough polygons
geojson_url = "https://data.cityofnewyork.us/api/geospatial/gthc-hcne?method=export&format=GeoJSON"
nyc_geo = requests.get(geojson_url).json()

# Helper for Folium choropleths
def create_folium_choropleth(var, legend_title, prop_key, filename, color_scale="YlOrRd_09"):
    df = extended_stats.set_index("BORO")
    try:
        cmap = getattr(linear, color_scale)
    except AttributeError:
        cmap = linear.YlOrRd_09
    colormap = cmap.scale(df[var].min(), df[var].max())
    colormap.caption = legend_title
    for feat in nyc_geo["features"]:
        name = feat["properties"]["boroname"]
        if name in df.index:
            feat["properties"][prop_key] = f"{df.loc[name, var]:.2f}"
    def style_fn(feat):
        name = feat["properties"]["boroname"]
        val = df.loc[name, var] if name in df.index else None
        return {"fillColor": colormap(val) if val is not None else "transparent",
                "color":"black", "weight":1, "fillOpacity":0.7}
    tooltip = folium.GeoJsonTooltip(fields=["boroname", prop_key],
                                    aliases=["Borough:", f"{legend_title}:"],
                                    localize=True, sticky=False, labels=True)
    m = folium.Map(location=[40.7128,-74.0060], zoom_start=11, tiles="cartodbpositron")
    folium.GeoJson(nyc_geo, name=legend_title, style_function=style_fn, tooltip=tooltip).add_to(m)
    m.add_child(colormap)
    m.save(filename)

# Create choropleths 
create_folium_choropleth("mean_rent","Average Monthly Rent ($)","Average Rent","nyc_borough_folium.html","YlOrRd_09")
create_folium_choropleth("mean_income","Average Household Income ($)","Average Income","income_choropleth.html","YlGnBu_09")
create_folium_choropleth("mean_rating","Average Unit Rating","Unit Rating","rating_choropleth.html","PuBu_09")
create_folium_choropleth("mean_utilwinter","Average Winter Utilities ($)","Average Winter Utilities","winter_util_choropleth.html","OrRd_09")
create_folium_choropleth("mean_utilsummer","Average Summer Utilities ($)","Average Summer Utilities","summer_util_choropleth.html","YlOrRd_09")
create_folium_choropleth("mean_pets","Average Pet Ownership","Average Pet Ownership","pets_choropleth.html","Blues_09")
create_folium_choropleth("mean_lease","Average Lease Length (months)","Average Lease Length","lease_choropleth.html","Greens_09")
