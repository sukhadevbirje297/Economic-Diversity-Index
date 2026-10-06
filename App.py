import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="Economic Diversity - Maharashtra",
    page_icon="📊",
    layout="wide"
)

# =========================================================
# TITLE
# =========================================================

st.title("📊 District-wise Economic Diversity in Maharashtra")

st.markdown(
    "### Economic Diversity Index – District-wise Ranking and Map"
)

# =========================================================
# LOAD EXCEL
# =========================================================

@st.cache_data
def load_ranking():

    ranking = pd.read_excel(
        "economic_diversity_ranking.xlsx"
    )

    return ranking


# =========================================================
# LOAD GEOJSON
# =========================================================

@st.cache_data
def load_map():

    mh = gpd.read_file(
        "maharashtra.geojson"
    )

    return mh


ranking = load_ranking()
mh = load_map()

# =========================================================
# CLEAN DISTRICT NAMES
# =========================================================

ranking["District"] = (
    ranking["District"]
    .astype(str)
    .str.strip()
    .str.title()
)

# District name corrections in Excel
ranking["District"] = ranking["District"].replace({

    "Ahmadnagar": "Ahmednagar",

    "Gondiya": "Gondia",

    "Buldana": "Buldhana"
})


# GeoJSON district names
mh["district"] = (
    mh["district"]
    .astype(str)
    .str.strip()
)

# Remove Palghar
mh = mh[mh["district"] != "Palghar"].copy()

# =========================================================
# STANDARDIZE GEOJSON NAMES
# =========================================================

mh["district"] = mh["district"].replace({

    "Ahmadnagar": "Ahilyanagar",

    "Ahmednagar": "Ahilyanagar",

    "Gondiya": "Gondia",

    "Buldana": "Buldhana",

    "Aurangabad": "Chhatrapati Sambhajinagar",

    "Osmanabad": "Dharashiv"
})

# =========================================================
# QUARTILES
# =========================================================

Q1 = ranking["Normalized_Diversity"].quantile(0.25)

Q2 = ranking["Normalized_Diversity"].quantile(0.50)

Q3 = ranking["Normalized_Diversity"].quantile(0.75)


# =========================================================
# CATEGORY
# =========================================================

def category(x):

    if x <= Q1:

        return "Low"

    elif x <= Q3:

        return "Medium"

    else:

        return "High"


ranking["Category"] = (
    ranking["Normalized_Diversity"]
    .apply(category)
)

# =========================================================
# MERGE EXCEL + GEOJSON
# =========================================================

map_data = mh.merge(
    ranking,
    left_on="district",
    right_on="District",
    how="left"
)

# =========================================================
# COLOURS
# =========================================================

color_dict = {

    "Low": "#e74c3c",

    "Medium": "#f39c12",

    "High": "#27ae60"
}


map_data["Color"] = (
    map_data["Category"]
    .map(color_dict)
    .fillna("#bdbdbd")
)

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("📌 Economic Diversity")

st.sidebar.markdown(
    """
    ### Economic Diversity Level

    🔴 **Low**

    🟠 **Medium**

    🟢 **High**
    """
)

st.sidebar.markdown("---")

st.sidebar.write(
    f"**Q1:** {Q1:.4f}"
)

st.sidebar.write(
    f"**Median:** {Q2:.4f}"
)

st.sidebar.write(
    f"**Q3:** {Q3:.4f}"
)

# =========================================================
# SUMMARY
# =========================================================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Total Districts",
        len(ranking)
    )

with col2:

    st.metric(
        "High",
        len(
            ranking[
                ranking["Category"] == "High"
            ]
        )
    )

with col3:

    st.metric(
        "Medium",
        len(
            ranking[
                ranking["Category"] == "Medium"
            ]
        )
    )

with col4:

    st.metric(
        "Low",
        len(
            ranking[
                ranking["Category"] == "Low"
            ]
        )
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

table = table.sort_values(
    "Rank"
)

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
# MAP
# =========================================================

st.subheader(
    "🗺️ District-wise Economic Diversity Map"
)

m = folium.Map(
    location=[19.5, 75.3],
    zoom_start=6,
    tiles="CartoDB positron"
)

# =========================================================
# DISTRICT POLYGONS
# =========================================================

folium.GeoJson(

    map_data,

    name="Economic Diversity",

    style_function=lambda feature: {

        "fillColor":
            feature["properties"].get(
                "Color",
                "#bdbdbd"
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
            "Economic Diversity:"
        ],

        localize=True,

        sticky=True,

        labels=True
    )

).add_to(m)

# =========================================================
# DISTRICT NAME + RANK LABELS
# =========================================================

for idx, row in map_data.iterrows():

    if row.geometry is None:
        continue

    if row.geometry.is_empty:
        continue

    try:

        centroid = row.geometry.representative_point()

        district_name = row.get(
            "district",
            ""
        )

        rank = row.get(
            "Rank",
            ""
        )

        if pd.notna(rank):

            label = (
                f"<b>{district_name}</b>"
                f"<br>Rank: {int(rank)}"
            )

        else:

            label = f"<b>{district_name}</b>"

        folium.Marker(

            location=[
                centroid.y,
                centroid.x
            ],

            icon=folium.DivIcon(

                html=f"""
                <div style="
                    font-size: 9px;
                    font-weight: bold;
                    color: black;
                    text-align: center;
                    width: 100px;
                    margin-left: -50px;
                    text-shadow:
                        1px 1px 2px white,
                        -1px -1px 2px white;
                ">
                    {label}
                </div>
                """
            )

        ).add_to(m)

    except Exception:

        pass

# =========================================================
# LEGEND
# =========================================================

legend_html = """

<div style="
position: fixed;
bottom: 40px;
right: 30px;
z-index: 9999;
background-color: white;
border: 2px solid grey;
border-radius: 6px;
padding: 12px;
font-size: 14px;
">

<b>Economic Diversity Level</b>

<br><br>

<div>
<span style="
display:inline-block;
width:18px;
height:18px;
background:#e74c3c;
margin-right:7px;
"></span>
Low
</div>

<br>

<div>
<span style="
display:inline-block;
width:18px;
height:18px;
background:#f39c12;
margin-right:7px;
"></span>
Medium
</div>

<br>

<div>
<span style="
display:inline-block;
width:18px;
height:18px;
background:#27ae60;
margin-right:7px;
"></span>
High
</div>

</div>

"""

m.get_root().html.add_child(
    folium.Element(legend_html)
)

# =========================================================
# MAP LAYER CONTROL
# =========================================================

folium.LayerControl().add_to(m)

# =========================================================
# DISPLAY MAP
# =========================================================

st_folium(
    m,
    use_container_width=True,
    height=700
)

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "Economic Diversity Index | Maharashtra Districts"
)
