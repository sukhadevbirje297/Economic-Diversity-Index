import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Economic Diversity Index",
    layout="wide"
)

st.title("Economic Diversity Index of Maharashtra Districts")
st.markdown("District-wise Economic Diversity Ranking and Mapping")

# -----------------------------
# Load Data
# -----------------------------
ranking = pd.read_excel("economic_diversity_ranking.xlsx")
mh = gpd.read_file("maharashtra.geojson")

# -----------------------------
# Data Cleaning
# -----------------------------
ranking["District"] = ranking["District"].str.title()

ranking["District"] = ranking["District"].replace({
    "Ahmadnagar": "Ahmednagar",
    "Gondiya": "Gondia",
    "Buldana": "Buldhana"
})

# -----------------------------
# Quartiles
# -----------------------------
Q1 = ranking["Normalized_Diversity"].quantile(0.25)
Q2 = ranking["Normalized_Diversity"].quantile(0.50)
Q3 = ranking["Normalized_Diversity"].quantile(0.75)

def category(x):
    if x <= Q1:
        return "Low"
    elif x <= Q3:
        return "Medium"
    else:
        return "High"

ranking["Category"] = ranking["Normalized_Diversity"].apply(category)

# -----------------------------
# Merge Data
# -----------------------------
map_data = mh.merge(
    ranking,
    left_on="district",
    right_on="District",
    how="left"
)

# Updated district names
map_data["district"] = map_data["district"].replace({
    "Ahmednagar": "Ahilyanagar",
    "Aurangabad": "Chhatrapati Sambhajinagar",
    "Osmanabad": "Dharashiv"
})

# -----------------------------
# No Data Category
# -----------------------------
map_data["Category"] = map_data["Category"].fillna("No Data")

# -----------------------------
# Colors
# -----------------------------
color_dict = {
    "Low": "red",
    "Medium": "orange",
    "High": "green",
    "No Data": "lightgrey"
}

map_data["Color"] = map_data["Category"].map(color_dict)

# -----------------------------
# Summary Metrics
# -----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Total Districts", len(map_data))
col2.metric("Highest Rank", int(ranking["Rank"].min()))
col3.metric("Lowest Rank", int(ranking["Rank"].max()))

# -----------------------------
# Ranking Table
# -----------------------------
st.subheader("District Ranking Table")

ranking_display = ranking[
    ["District", "Normalized_Diversity", "Rank", "Category"]
].sort_values("Rank")

st.dataframe(
    ranking_display,
    use_container_width=True
)

# -----------------------------
# Download Button
# -----------------------------
excel_file = "economic_diversity_ranking.xlsx"

with open(excel_file, "rb") as file:
    st.download_button(
        label="Download Ranking Excel File",
        data=file,
        file_name="economic_diversity_ranking.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# -----------------------------
# Search District
# -----------------------------
st.subheader("District Information")

district_name = st.selectbox(
    "Select District",
    sorted(map_data["district"].unique())
)

district_info = map_data[map_data["district"] == district_name]

st.dataframe(
    district_info[
        ["district", "Normalized_Diversity", "Rank", "Category"]
    ],
    use_container_width=True
)

# -----------------------------
# Map
# -----------------------------
st.subheader("District-wise Economic Diversity Map")

fig, ax = plt.subplots(figsize=(14, 12))

map_data.plot(
    color=map_data["Color"],
    edgecolor="black",
    linewidth=0.8,
    ax=ax
)

for idx, row in map_data.iterrows():

    if row.geometry is not None:

        x = row.geometry.centroid.x
        y = row.geometry.centroid.y

        rank_text = ""

        if pd.notnull(row["Rank"]):
            rank_text = int(row["Rank"])
        else:
            rank_text = "No Data"

        ax.text(
            x,
            y,
            f"{row['district']}\n{rank_text}",
            fontsize=6,
            ha="center"
        )

legend_elements = [
    Patch(facecolor='red', edgecolor='black', label='Low'),
    Patch(facecolor='orange', edgecolor='black', label='Medium'),
    Patch(facecolor='green', edgecolor='black', label='High'),
    Patch(facecolor='lightgrey', edgecolor='black', label='No Data')
]

ax.legend(
    handles=legend_elements,
    title="Economic Diversity Level",
    loc="lower right"
)

plt.title(
    "District-wise Economic Diversity in Maharashtra",
    fontsize=16,
    fontweight="bold"
)

plt.axis("off")

st.pyplot(fig)

# -----------------------------
# Top 10 Districts
# -----------------------------
st.subheader("Top 10 Districts")

st.dataframe(
    ranking.sort_values("Rank").head(10),
    use_container_width=True
)

# -----------------------------
# Bottom 10 Districts
# -----------------------------
st.subheader("Bottom 10 Districts")

st.dataframe(
    ranking.sort_values("Rank").tail(10),
    use_container_width=True
)
