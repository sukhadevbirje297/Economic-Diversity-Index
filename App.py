import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# --------------------------------------------------
# PAGE SETTINGS
# --------------------------------------------------
st.set_page_config(
    page_title="Economic Diversity Index - Maharashtra",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Economic Diversity Index - Maharashtra")
st.markdown(
    "District-wise Economic Diversity Ranking, Quartiles and Map"
)

# --------------------------------------------------
# LOAD EXCEL
# --------------------------------------------------
ranking = pd.read_excel("economic_diversity_ranking.xlsx")

# --------------------------------------------------
# CHECK REQUIRED COLUMNS
# --------------------------------------------------
required_columns = [
    "District",
    "Normalized_Diversity",
    "Rank"
]

missing = [
    col for col in required_columns
    if col not in ranking.columns
]

if missing:
    st.error(f"Missing columns in Excel: {missing}")
    st.stop()

# --------------------------------------------------
# QUARTILES
# --------------------------------------------------
q1 = ranking["Normalized_Diversity"].quantile(0.25)
q2 = ranking["Normalized_Diversity"].quantile(0.50)
q3 = ranking["Normalized_Diversity"].quantile(0.75)

def get_category(value):
    if value <= q1:
        return "Low"
    elif value <= q2:
        return "Medium"
    elif value <= q3:
        return "High"
    else:
        return "Very High"

ranking["Category"] = ranking["Normalized_Diversity"].apply(
    get_category
)

# --------------------------------------------------
# QUARTILE SUMMARY
# --------------------------------------------------
st.subheader("📌 Quartile Classification")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Q1 - Low",
    f"≤ {q1:.3f}"
)

c2.metric(
    "Q2 - Medium",
    f"{q1:.3f} – {q2:.3f}"
)

c3.metric(
    "Q3 - High",
    f"{q2:.3f} – {q3:.3f}"
)

c4.metric(
    "Very High",
    f"> {q3:.3f}"
)

# --------------------------------------------------
# RANKING TABLE
# --------------------------------------------------
st.subheader("🏆 District Ranking")

display_columns = [
    "Rank",
    "District",
    "Diversity_Index",
    "Normalized_Diversity",
    "Category"
]

st.dataframe(
    ranking[display_columns].sort_values("Rank"),
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# LOAD GEOJSON
# --------------------------------------------------
try:
    gdf = gpd.read_file("maharashtra.geojson")
except Exception as e:
    st.error(f"Unable to load Maharashtra GeoJSON: {e}")
    st.stop()

# --------------------------------------------------
# FIND DISTRICT COLUMN IN GEOJSON
# --------------------------------------------------
possible_district_columns = [
    "district",
    "District",
    "DISTRICT",
    "NAME_2",
    "NAME",
    "name",
    "dtname",
    "DT_NAME"
]

geo_district_column = None

for col in possible_district_columns:
    if col in gdf.columns:
        geo_district_column = col
        break

if geo_district_column is None:
    st.error(
        "District name column was not found in maharashtra.geojson. "
        f"Available columns: {list(gdf.columns)}"
    )
    st.stop()

# --------------------------------------------------
# STANDARDIZE DISTRICT NAMES
# --------------------------------------------------
def clean_district_name(name):
    name = str(name).strip()

    replacements = {
        "Ahmednagar": "Ahilyanagar",
        "Ahmed Nagar": "Ahilyanagar",
        "Aurangabad": "Chhatrapati Sambhajinagar",
        "Osmanabad": "Dharashiv"
    }

    return replacements.get(name, name)

gdf["District_Map"] = gdf[geo_district_column].apply(
    clean_district_name
)

ranking["District_Map"] = ranking["District"].apply(
    clean_district_name
)

# --------------------------------------------------
# MERGE EXCEL + GEOJSON
# --------------------------------------------------
map_data = gdf.merge(
    ranking,
    on="District_Map",
    how="left"
)

# --------------------------------------------------
# MAP
# --------------------------------------------------
st.subheader("🗺️ Maharashtra Economic Diversity Map")

m = folium.Map(
    location=[19.5, 75.3],
    zoom_start=6,
    tiles="CartoDB positron"
)

# --------------------------------------------------
# CATEGORY COLORS
# --------------------------------------------------
category_colors = {
    "Low": "#d73027",
    "Medium": "#fee08b",
    "High": "#91cf60",
    "Very High": "#1a9850"
}

def style_function(feature):
    category = feature["properties"].get(
        "Category",
        None
    )

    return {
        "fillColor": category_colors.get(
            category,
            "#cccccc"
        ),
        "color": "black",
        "weight": 1,
        "fillOpacity": 0.7
    }

# --------------------------------------------------
# GEOJSON LAYER
# --------------------------------------------------
folium.GeoJson(
    map_data.to_json(),
    name="Economic Diversity",
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(
        fields=[
            geo_district_column,
            "Rank",
            "Normalized_Diversity",
            "Category"
        ],
        aliases=[
            "District:",
            "Rank:",
            "Normalized Diversity:",
            "Category:"
        ],
        localize=True,
        sticky=False
    )
).add_to(m)

folium.LayerControl().add_to(m)

st_folium(
    m,
    width=1200,
    height=650
)

# --------------------------------------------------
# DATA DOWNLOAD
# --------------------------------------------------
st.subheader("⬇️ Download Ranking Data")

csv_data = ranking[
    display_columns
].sort_values("Rank").to_csv(index=False)

st.download_button(
    label="Download Ranking CSV",
    data=csv_data,
    file_name="maharashtra_economic_diversity_ranking.csv",
    mime="text/csv"
)
