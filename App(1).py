import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Economic Diversity Index", layout="wide")

st.title("Economic Diversity Index of Maharashtra Districts")

# Load files
ranking = pd.read_excel("economic_diversity_ranking.xlsx")
gdf = gpd.read_file("maharashtra.geojson")

# District name updates
gdf["district"] = gdf["district"].replace({
    "Ahmednagar": "Ahilyanagar",
    "Aurangabad": "Chhatrapati Sambhajinagar",
    "Osmanabad": "Dharashiv"
})

# Quartiles
q1 = ranking["Normalized Diversity"].quantile(0.25)
q2 = ranking["Normalized Diversity"].quantile(0.50)
q3 = ranking["Normalized Diversity"].quantile(0.75)

def category(x):
    if x <= q1:
        return "Low"
    elif x <= q2:
        return "Medium"
    elif x <= q3:
        return "High"
    else:
        return "Very High"

ranking["Category"] = ranking["Normalized Diversity"].apply(category)

# Ranking Table
st.subheader("District Ranking Table")
st.dataframe(ranking, use_container_width=True)

# Merge Data
map_data = gdf.merge(
    ranking,
    left_on="district",
    right_on="District",
    how="left"
)

# Map
m = folium.Map(location=[19.5, 75.3], zoom_start=6)

folium.Choropleth(
    geo_data=map_data,
    data=map_data,
    columns=["District", "Normalized Diversity"],
    key_on="feature.properties.district",
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name="Economic Diversity Index"
).add_to(m)

folium.GeoJson(
    map_data,
    tooltip=folium.GeoJsonTooltip(
        fields=["district", "Rank", "Category"],
        aliases=["District", "Rank", "Category"]
    )
).add_to(m)

st.subheader("Economic Diversity Map")
st_folium(m, width=1000, height=600)
