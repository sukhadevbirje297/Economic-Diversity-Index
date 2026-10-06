import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# --------------------------------------------------
# Page settings
# --------------------------------------------------
st.set_page_config(
    page_title="Economic Diversity Index - Maharashtra",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Economic Diversity Index - Maharashtra")
st.write("District-wise Economic Diversity Ranking and Quartile Map")

# --------------------------------------------------
# Load Excel and GeoJSON
# --------------------------------------------------
ranking = pd.read_excel("economic_diversity_ranking.xlsx")
gdf = gpd.read_file("maharashtra.geojson")

# --------------------------------------------------
# Clean column names
# --------------------------------------------------
ranking.columns = ranking.columns.str.strip()
gdf.columns = gdf.columns.str.strip()

# Convert required columns to numeric
ranking["Normalized_Diversity"] = pd.to_numeric(
    ranking["Normalized_Diversity"],
    errors="coerce"
)

ranking["Diversity_Index"] = pd.to_numeric(
    ranking["Diversity_Index"],
    errors="coerce"
)

ranking["Rank"] = pd.to_numeric(
    ranking["Rank"],
    errors="coerce"
)

# --------------------------------------------------
# District name cleaning
# --------------------------------------------------
ranking["District"] = ranking["District"].astype(str).str.strip()
gdf["district"] = gdf["district"].astype(str).str.strip()

# Common Maharashtra district name differences
district_mapping = {
    "Ahmednagar": "Ahilyanagar",
    "Aurangabad": "Chhatrapati Sambhajinagar",
    "Osmanabad": "Dharashiv"
}

ranking["District"] = ranking["District"].replace(district_mapping)
gdf["district"] = gdf["district"].replace(district_mapping)

# --------------------------------------------------
# Calculate Quartiles
# --------------------------------------------------
q1 = ranking["Normalized_Diversity"].quantile(0.25)
q2 = ranking["Normalized_Diversity"].quantile(0.50)
q3 = ranking["Normalized_Diversity"].quantile(0.75)

def get_quartile(value):
    if pd.isna(value):
        return "No Data"
    elif value <= q1:
        return "Q1 - Low"
    elif value <= q2:
        return "Q2 - Moderate"
    elif value <= q3:
        return "Q3 - High"
    else:
        return "Q4 - Very High"

ranking["Quartile"] = ranking["Normalized_Diversity"].apply(get_quartile)

# --------------------------------------------------
# Dashboard summary
# --------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Districts", len(ranking))

with col2:
    st.metric("Q1 - Low", (ranking["Quartile"] == "Q1 - Low").sum())

with col3:
    st.metric("Q2 - Moderate", (ranking["Quartile"] == "Q2 - Moderate").sum())

with col4:
    st.metric("Q4 - Very High", (ranking["Quartile"] == "Q4 - Very High").sum())

# --------------------------------------------------
# Ranking Table
# --------------------------------------------------
st.subheader("🏆 District Ranking")

display_columns = [
    "Rank",
    "District",
    "Diversity_Index",
    "Normalized_Diversity",
    "Quartile"
]

st.dataframe(
    ranking[display_columns].sort_values("Rank"),
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# Quartile information
# --------------------------------------------------
st.subheader("📈 Quartile Thresholds")

threshold_df = pd.DataFrame({
    "Quartile": [
        "Q1 - Low",
        "Q2 - Moderate",
        "Q3 - High",
        "Q4 - Very High"
    ],
    "Range": [
        f"≤ {q1:.4f}",
        f"{q1:.4f} – {q2:.4f}",
        f"{q2:.4f} – {q3:.4f}",
        f"> {q3:.4f}"
    ]
})

st.table(threshold_df)

# --------------------------------------------------
# Merge Excel data with Maharashtra GeoJSON
# --------------------------------------------------
map_data = gdf.merge(
    ranking,
    left_on="district",
    right_on="District",
    how="left"
)

# --------------------------------------------------
# Maharashtra Map
# --------------------------------------------------
st.subheader("🗺️ Economic Diversity Map")

m = folium.Map(
    location=[19.5, 75.3],
    zoom_start=6,
    tiles="CartoDB positron"
)

# Choropleth based on Normalized Diversity
folium.Choropleth(
    geo_data=map_data,
    data=map_data,
    columns=["District", "Normalized_Diversity"],
    key_on="feature.properties.district",
    fill_color="YlOrRd",
    fill_opacity=0.75,
    line_opacity=0.4,
    nan_fill_color="lightgray",
    legend_name="Normalized Economic Diversity"
).add_to(m)

# --------------------------------------------------
# Map Tooltip
# --------------------------------------------------
tooltip_fields = [
    "district",
    "Rank",
    "Diversity_Index",
    "Normalized_Diversity",
    "Quartile"
]

tooltip_aliases = [
    "District:",
    "Rank:",
    "Diversity Index:",
    "Normalized Diversity:",
    "Quartile:"
]

folium.GeoJson(
    map_data,
    name="District Information",
    style_function=lambda feature: {
        "fillColor": "transparent",
        "color": "black",
        "weight": 0.5,
        "fillOpacity": 0
    },
    tooltip=folium.GeoJsonTooltip(
        fields=tooltip_fields,
        aliases=tooltip_aliases,
        localize=True,
        sticky=False,
        labels=True
    )
).add_to(m)

st_folium(
    m,
    width=None,
    height=650
)

# --------------------------------------------------
# Data download
# --------------------------------------------------
st.subheader("⬇️ Download Ranking Data")

csv_data = ranking[display_columns].sort_values("Rank").to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download Ranking CSV",
    data=csv_data,
    file_name="economic_diversity_ranking_quartiles.csv",
    mime="text/csv"
)
