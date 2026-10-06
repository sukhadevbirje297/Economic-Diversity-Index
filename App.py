import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# ---------------------------------------------------
# Page Configuration
# ---------------------------------------------------

st.set_page_config(
    page_title="Economic Diversity Index - Maharashtra",
    page_icon="📊",
    layout="wide"
)

# ---------------------------------------------------
# Title
# ---------------------------------------------------

st.title("📊 Economic Diversity Index - Maharashtra")
st.markdown("### District-wise Economic Diversity Ranking")

# ---------------------------------------------------
# Load Excel Data
# ---------------------------------------------------

ranking = pd.read_excel("economic_diversity_ranking.xlsx")

# ---------------------------------------------------
# Load Maharashtra GeoJSON
# ---------------------------------------------------

gdf = gpd.read_file("maharashtra.geojson")

# ---------------------------------------------------
# Clean District Names
# ---------------------------------------------------

ranking["District"] = (
    ranking["District"]
    .astype(str)
    .str.strip()
)

gdf["district"] = (
    gdf["district"]
    .astype(str)
    .str.strip()
)

# ---------------------------------------------------
# Handle Maharashtra District Name Differences
# ---------------------------------------------------

name_changes = {
    "Ahmednagar": "Ahilyanagar",
    "Ahmadnagar": "Ahilyanagar",
    "Aurangabad": "Chhatrapati Sambhajinagar",
    "Osmanabad": "Dharashiv"
}

ranking["District"] = ranking["District"].replace(name_changes)

gdf["district"] = gdf["district"].replace(name_changes)

# ---------------------------------------------------
# Make sure numeric columns are numeric
# ---------------------------------------------------

ranking["Diversity_Index"] = pd.to_numeric(
    ranking["Diversity_Index"],
    errors="coerce"
)

ranking["Normalized_Diversity"] = pd.to_numeric(
    ranking["Normalized_Diversity"],
    errors="coerce"
)

ranking["Rank"] = pd.to_numeric(
    ranking["Rank"],
    errors="coerce"
)

# ---------------------------------------------------
# HIGH / MEDIUM / LOW
# No Quartiles
#
# Classification is based on Normalized Diversity:
# Top third    = High
# Middle third = Medium
# Bottom third = Low
# ---------------------------------------------------

ranking = ranking.sort_values(
    "Normalized_Diversity",
    ascending=False
).reset_index(drop=True)

n = len(ranking)

def classify(index):
    if index < n / 3:
        return "High"
    elif index < (2 * n) / 3:
        return "Medium"
    else:
        return "Low"

ranking["Category"] = [
    classify(i) for i in range(n)
]

# ---------------------------------------------------
# Sidebar
# ---------------------------------------------------

st.sidebar.header("📌 Economic Diversity")

st.sidebar.markdown(
    """
    **Categories**

    🟢 High  
    🟡 Medium  
    🔴 Low
    """
)

# ---------------------------------------------------
# Summary
# ---------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Districts",
        len(ranking)
    )

with col2:
    high_count = (ranking["Category"] == "High").sum()
    st.metric(
        "High Diversity",
        high_count
    )

with col3:
    low_count = (ranking["Category"] == "Low").sum()
    st.metric(
        "Low Diversity",
        low_count
    )

# ---------------------------------------------------
# Ranking Table
# ---------------------------------------------------

st.subheader("🏆 District-wise Ranking")

display_columns = [
    "Rank",
    "District",
    "Diversity_Index",
    "Normalized_Diversity",
    "Category"
]

display_data = ranking[display_columns].copy()

display_data.columns = [
    "Rank",
    "District",
    "Diversity Index",
    "Normalized Diversity",
    "Category"
]

st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True
)

# ---------------------------------------------------
# Merge Excel + GeoJSON
# ---------------------------------------------------

map_data = gdf.merge(
    ranking,
    left_on="district",
    right_on="District",
    how="left"
)

# ---------------------------------------------------
# Map
# ---------------------------------------------------

st.subheader("🗺️ Maharashtra Economic Diversity Map")

m = folium.Map(
    location=[19.5, 75.3],
    zoom_start=6,
    tiles="CartoDB positron"
)

# ---------------------------------------------------
# Category Colours
# ---------------------------------------------------

category_colors = {
    "High": "#2ca25f",
    "Medium": "#ffd92f",
    "Low": "#de2d26"
}

# ---------------------------------------------------
# Function for Map Colours
# ---------------------------------------------------

def get_color(category):

    if category == "High":
        return "#2ca25f"

    elif category == "Medium":
        return "#ffd92f"

    elif category == "Low":
        return "#de2d26"

    return "#bdbdbd"

# ---------------------------------------------------
# GeoJSON District Layer
# ---------------------------------------------------

folium.GeoJson(
    map_data,
    name="Economic Diversity",
    style_function=lambda feature: {
        "fillColor": get_color(
            feature["properties"].get("Category")
        ),
        "color": "black",
        "weight": 1,
        "fillOpacity": 0.75
    },
    highlight_function=lambda feature: {
        "weight": 3,
        "color": "blue",
        "fillOpacity": 0.9
    },
    tooltip=folium.GeoJsonTooltip(
        fields=[
            "district",
            "Rank",
            "Diversity_Index",
            "Normalized_Diversity",
            "Category"
        ],
        aliases=[
            "District:",
            "Rank:",
            "Diversity Index:",
            "Normalized Diversity:",
            "Category:"
        ],
        localize=True,
        sticky=False,
        labels=True
    )
).add_to(m)

# ---------------------------------------------------
# Map Legend
# ---------------------------------------------------

legend_html = """
<div style="
position: fixed;
bottom: 40px;
left: 40px;
width: 180px;
height: 125px;
background-color: white;
border: 2px solid grey;
z-index: 9999;
font-size: 14px;
padding: 10px;
">

<b>Economic Diversity</b><br><br>

<span style="
background:#2ca25f;
width:18px;
height:18px;
display:inline-block;
"></span>
&nbsp; High<br>

<span style="
background:#ffd92f;
width:18px;
height:18px;
display:inline-block;
"></span>
&nbsp; Medium<br>

<span style="
background:#de2d26;
width:18px;
height:18px;
display:inline-block;
"></span>
&nbsp; Low

</div>
"""

m.get_root().html.add_child(
    folium.Element(legend_html)
)

# ---------------------------------------------------
# Layer Control
# ---------------------------------------------------

folium.LayerControl().add_to(m)

# ---------------------------------------------------
# Display Map
# ---------------------------------------------------

st_folium(
    m,
    width=None,
    height=650
)

# ---------------------------------------------------
# Data Information
# ---------------------------------------------------

st.markdown("---")

st.caption(
    "Economic Diversity Index | District-wise analysis of Maharashtra"
)
