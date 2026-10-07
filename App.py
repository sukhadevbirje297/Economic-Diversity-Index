import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

st.set_page_config(
    page_title="Economic Diversity Index",
    layout="wide"
)

st.title("Economic Diversity Index of Maharashtra Districts")

# Load data
ranking = pd.read_excel("economic_diversity_ranking.xlsx")
mh = gpd.read_file("maharashtra.geojson")

# District name cleaning
ranking["District"] = ranking["District"].str.title()

ranking["District"] = ranking["District"].replace({
    "Ahmadnagar": "Ahilyanagar",
    "Gondiya": "Gondia",
    "Buldana": "Buldhana",
    "Aurangabad": "Chhatrapati Sambhajinagar",
    "Osmanabad": "Dharashiv"
})

mh["district"] = mh["district"].replace({
    "Ahmednagar": "Ahilyanagar",
    "Aurangabad": "Chhatrapati Sambhajinagar",
    "Osmanabad": "Dharashiv"
})

# Quartiles
Q1 = ranking["Normalized_Diversity"].quantile(0.25)
Q3 = ranking["Normalized_Diversity"].quantile(0.75)

def category(x):
    if pd.isna(x):
        return "No Data"
    elif x <= Q1:
        return "Low"
    elif x <= Q3:
        return "Medium"
    else:
        return "High"

ranking["Category"] = ranking["Normalized_Diversity"].apply(category)

# Merge
map_data = mh.merge(
    ranking,
    left_on="district",
    right_on="District",
    how="left"
)

# Category for missing districts (Palghar)
map_data["Category"] = map_data["Category"].fillna("No Data")

# Colors
color_dict = {
    "Low": "red",
    "Medium": "orange",
    "High": "green",
    "No Data": "lightgrey"
}

map_data["Color"] = map_data["Category"].map(color_dict)

# -------------------------
# Ranking Table
# -------------------------
st.subheader("District Ranking")

ranking_display = ranking.sort_values("Rank")

st.dataframe(
    ranking_display[["District",
                     "Normalized_Diversity",
                     "Rank"]],
    use_container_width=True
)

# Download button
with open("economic_diversity_ranking.xlsx", "rb") as file:
    st.download_button(
        label="Download Ranking Excel",
        data=file,
        file_name="economic_diversity_ranking.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# -------------------------
# Map
# -------------------------
st.subheader("District-wise Economic Diversity Map")

fig, ax = plt.subplots(figsize=(14, 12))

map_data.plot(
    color=map_data["Color"],
    edgecolor="black",
    linewidth=0.8,
    ax=ax
)

for idx, row in map_data.iterrows():

    x = row.geometry.centroid.x
    y = row.geometry.centroid.y

    if pd.notna(row.get("Rank")):
        label = f"{row['district']}\n{int(row['Rank'])}"
    else:
        label = f"{row['district']}\nNo Data"

    ax.text(
        x,
        y,
        label,
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

# Top districts
st.subheader("Top 10 Districts")

top10 = ranking.sort_values("Rank").head(10)

st.dataframe(
    top10[["District",
           "Normalized_Diversity",
           "Rank"]],
    use_container_width=True
)

# Bottom districts
st.subheader("Bottom 10 Districts")

bottom10 = ranking.sort_values("Rank").tail(10)

st.dataframe(
    bottom10[["District",
              "Normalized_Diversity",
              "Rank"]],
    use_container_width=True
)
