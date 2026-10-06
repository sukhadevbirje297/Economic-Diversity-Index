import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.features import DivIcon
from streamlit_folium import st_folium
import re

# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="Economic Diversity Index - Maharashtra",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Economic Diversity Index - Maharashtra")
st.markdown("### District-wise Economic Diversity Ranking")

# =========================================================
# LOAD FILES
# =========================================================

ranking = pd.read_excel("economic_diversity_ranking.xlsx")
gdf = gpd.read_file("maharashtra.geojson")

# =========================================================
# CLEAN DISTRICT NAMES
# =========================================================

def clean_name(x):
    x = str(x).strip().lower()

    # Remove common words/symbols
    x = x.replace("district", "")
    x = x.replace("dist.", "")
    x = re.sub(r"[^a-z0-9]", "", x)

    return x


ranking["District"] = ranking["District"].astype(str).str.strip()
gdf["district"] = gdf["district"].astype(str).str.strip()

# =========================================================
# COMMON DISTRICT NAME CHANGES
# =========================================================

name_changes = {
    "Ahmednagar": "Ahilyanagar",
    "Ahmadnagar": "Ahilyanagar",
    "Aurangabad": "Chhatrapati Sambhajinagar",
    "Osmanabad": "Dharashiv"
}

ranking["District"] = ranking["District"].replace(name_changes)
gdf["district"] = gdf["district"].replace(name_changes)

# Create matching key
ranking["match_key"] = ranking["District"].apply(clean_name)
gdf["match_key"] = gdf["district"].apply(clean_name)

# =========================================================
# NUMERIC DATA
# =========================================================

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

# =========================================================
# SORT BY RANK
# =========================================================

ranking = ranking.sort_values("Rank").reset_index(drop=True)

# =========================================================
# HIGH / MEDIUM / LOW
# NO QUARTILES
# =========================================================

n = len(ranking)

def get_category(i):
    if i < n / 3:
        return "High"
    elif i < (2 * n) / 3:
        return "Medium"
    else:
        return "Low"

ranking["Category"] = [
    get_category(i)
    for i in range(n)
]

# =========================================================
# SUMMARY
# =========================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Districts", len(ranking))

with col2:
    st.metric(
        "High",
        int((ranking["Category"] == "High").sum())
    )

with col3:
    st.metric(
        "Medium",
        int((ranking["Category"] == "Medium").sum())
    )

with col4:
    st.metric(
        "Low",
        int((ranking["Category"] == "Low").sum())
    )

# =========================================================
# RANKING TABLE
# =========================================================

st.subheader("🏆 District-wise Ranking")

table = ranking[
    [
        "Rank",
        "District",
        "Diversity_Index",
        "Normalized_Diversity",
        "Category"
    ]
].copy()

table.columns = [
    "Rank",
    "District",
    "Diversity Index",
    "Normalized Diversity",
    "Category"
]

st.dataframe(
    table,
    use_container_width=True,
    hide_index=True
)

# =========================================================
# MERGE MAP DATA
# =========================================================

map_data = gdf.merge(
    ranking[
        [
            "match_key",
            "District",
            "Diversity_Index",
            "Normalized_Diversity",
            "Rank",
            "Category"
        ]
    ],
    on="match_key",
    how="left"
)

# =========================================================
# MAP COLOURS
# =========================================================

def get_color(category):

    if category == "High":
        return "#2ca25f"

    if category == "Medium":
        return "#ffd92f"

    if category == "Low":
        return "#de2d26"

    # unmatched districts
    return "#d9d9d9"

# =========================================================
# CREATE MAP
# =========================================================

m = folium.Map(
    location=[19.5, 75.3],
    zoom_start=6,
    tiles="CartoDB positron"
)

# =========================================================
# DISTRICT POLYGONS
# =========================================================

folium.GeoJson(
    map_data.to_json(),
    name="Districts",

    style_function=lambda feature: {
        "fillColor": get_color(
            feature["properties"].get("Category")
        ),
        "color": "#333333",
        "weight": 1,
        "fillOpacity": 0.75
    },

    highlight_function=lambda feature: {
        "weight": 3,
        "color": "#0000ff",
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

# =========================================================
# DISTRICT NAME + RANK LABELS INSIDE MAP
# =========================================================

for _, row in map_data.iterrows():

    if row.geometry is None:
        continue

    # Point guaranteed to be inside polygon
    point = row.geometry.representative_point()

    district = row.get("district", "")
    rank = row.get("Rank", "")

    if pd.isna(rank):
        continue

    # Short district name for map
    label = f"""
    <div style="
        font-size: 10px;
        font-weight: bold;
        color: black;
        text-align: center;
        white-space: nowrap;
        text-shadow:
            1px 1px 2px white,
            -1px -1px 2px white,
            1px -1px 2px white,
            -1px 1px 2px white;
    ">
        {district}<br>
        Rank: {int(rank)}
    </div>
    """

    folium.Marker(
        location=[point.y, point.x],
        icon=DivIcon(
            icon_size=(150, 40),
            icon_anchor=(75, 20),
            html=label
        )
    ).add_to(m)

# =========================================================
# LEGEND
# =========================================================

legend_html = """
<div style="
position: fixed;
bottom: 30px;
left: 30px;
width: 170px;
background-color: white;
border: 2px solid #555;
z-index: 9999;
font-size: 14px;
padding: 10px;
border-radius: 5px;
">

<b>Economic Diversity</b><br><br>

<div>
<span style="
display:inline-block;
width:18px;
height:18px;
background:#2ca25f;
margin-right:7px;
"></span>
High
</div>

<div>
<span style="
display:inline-block;
width:18px;
height:18px;
background:#ffd92f;
margin-right:7px;
"></span>
Medium
</div>

<div>
<span style="
display:inline-block;
width:18px;
height:18px;
background:#de2d26;
margin-right:7px;
"></span>
Low
</div>

</div>
"""

m.get_root().html.add_child(
    folium.Element(legend_html)
)

# =========================================================
# MAP TITLE
# =========================================================

st.subheader("🗺️ Maharashtra District-wise Economic Diversity Map")

st.markdown(
    """
    **🟢 High** &nbsp;&nbsp;
    **🟡 Medium** &nbsp;&nbsp;
    **🔴 Low**
    """
)

# =========================================================
# SHOW MAP
# =========================================================

st_folium(
    m,
    width=None,
    height=700
)

# =========================================================
# END
# =========================================================

st.markdown("---")

st.caption(
    "Economic Diversity Index | District-wise analysis of Maharashtra"
)
